import plotly.graph_objects as go
from datetime import datetime, timedelta
import copy
from collections import OrderedDict
from sqlalchemy import create_engine
import pandas as pd
import json
import os
from collections import Counter
from functools import reduce


buy_commission = 0 
sell_commission = 0 
# buy_commission = 0.0025 
# sell_commission = 0.0025 
# buy_commission = 0.0000 
# sell_commission = 0.0001 

class StockPortfolio:
    def __init__(self, date, cash):
        self.date = datetime.strptime(date, '%Y-%m-%d')
        self.cash = cash
        self.cash_plus_stock = cash
        self.initial_cash = cash
        self.stocks = {}
        self.daily_history = {}
        self.memory_date = datetime.strptime(date, '%Y-%m-%d')
        engine = create_engine('mysql+pymysql://root:1234@127.0.0.1:3306/stock_db')
        self.stock_price = pd.read_sql('select * from lab_assignment;', con=engine)
        engine.dispose()


    def initialization_stock(self):

        if(self.memory_date != self.date):
            for ticker in self.stocks:
                self.stocks[ticker]['quantity_buy'] = 0
                self.stocks[ticker]['quantity_sold'] = 0
                self.stocks[ticker]['return_stock_selling'] = 0
            self.memory_date = self.date

    def add_stock(self, ticker, price, quantity):

        if ticker not in self.stocks:
            self.stocks[ticker] = {
                'price': price,
                'quantity': quantity,
                'total_bought': quantity * price * (1 + buy_commission),
                'total_sold': 0,
                'quantity_buy':quantity,
                'quantity_sold': 0,
                'recovery_bought': quantity * price * (1 + buy_commission),
                'return_stock_selling': 0,
            }
        else:
            print(f"Stock {ticker} already exists in the portfolio.")

    def buy_stock(self, date, ticker, price, quantity):
        date = datetime.strptime(date, '%Y-%m-%d')
        self.date = date

        self.initialization_stock()

        if ticker in self.stocks:
            self.stocks[ticker]['price'] = price
            self.stocks[ticker]['quantity'] += quantity
            self.stocks[ticker]['total_bought'] += quantity * price * (1 + buy_commission)
            self.stocks[ticker]['recovery_bought'] += quantity * price * (1 + buy_commission)
            self.stocks[ticker]['quantity_buy'] = quantity
            # self.stocks[ticker]['quantity_sold'] = 0
            self.cash -= price * quantity * (1 + buy_commission)
            # self.stocks[ticker]['return_stock_selling'] = 0

        else:
            self.add_stock(ticker, price, quantity)
            self.cash -= price * quantity * (1 + buy_commission)

        self.cash_plus_stock = self.get_cash_plus_stocks()
        self.update_daily_history(date)

    def sell_stock(self, date, ticker, price, quantity):
        date = datetime.strptime(date, '%Y-%m-%d')
        self.date = date

        self.initialization_stock()

        if ticker in self.stocks:
            if self.stocks[ticker]['quantity'] >= quantity:
                self.stocks[ticker]['price'] = price

                # 누적수익률 구하려고 함
                buy = (self.stocks[ticker]['recovery_bought'] / self.stocks[ticker]['quantity'] * quantity)
                sell = price * quantity
                self.stocks[ticker]['return_stock_selling'] = (sell - buy) / buy

                self.stocks[ticker]['recovery_bought'] -= self.stocks[ticker]['recovery_bought'] / self.stocks[ticker]['quantity'] * quantity

                self.stocks[ticker]['quantity'] -= quantity
                self.stocks[ticker]['total_sold'] += price * quantity * (1 - sell_commission)
                # self.stocks[ticker]['quantity_buy'] = 0
                self.stocks[ticker]['quantity_sold'] = quantity

                self.cash += price * quantity * (1 - sell_commission)
            else:
                print(f"Not enough quantity of {ticker} to sell.")
        else:
            print(f"Stock {ticker} not found in the portfolio.")

        self.cash_plus_stock = self.get_cash_plus_stocks()
        self.update_daily_history(date)

    def get_cash_plus_stocks(self):
        cash_plus_stock = 0
        cash_plus_stock += self.cash
        for ticker, data in self.stocks.items():
            cash_plus_stock += data['price'] * data['quantity'] * (1 - sell_commission)
        return cash_plus_stock

    def sell_all_stocks(self):
        # 가장 최근 날짜를 가져옴
        if self.daily_history:
            last_date = max(self.daily_history.keys())
        else:
            last_date = self.date.strftime('%Y-%m-%d')

        total_value = 0
        for ticker, data in self.stocks.items():
            total_value += data['price'] * data['quantity']
            self.cash += data['price'] * data['quantity'] * (1 - sell_commission)
            data['total_sold'] += data['price'] * data['quantity']
            data['quantity_sold'] += data['quantity']
            data['quantity'] = 0

        # 가장 최근 날짜로 기록 업데이트
        self.update_daily_history(datetime.strptime(last_date, '%Y-%m-%d'))
        return total_value

    def calculate_return_rate(self):
        # 포트폴리오의 복사본을 생성
        portfolio_copy = copy.deepcopy(self)
        current_value = self.cash + portfolio_copy.sell_all_stocks()
        return_rate = ((current_value - self.initial_cash) / self.initial_cash) * 100
        return return_rate

    def calculate_stock_return_rate(self, ticker):
        if ticker in self.stocks:
            data = self.stocks[ticker]
            if data['total_bought'] > 0:
                stock_return_rate = ((data['total_sold'] - data['total_bought']) / data['total_bought'])
                return stock_return_rate
            else:
                return 0
        else:
            print(f"Stock {ticker} not found in the portfolio.")
            return None

    def calculate_all_stock_return_rates(self):
        stock_return_rates = {}
        portfolio_copy = copy.deepcopy(self)

        total_value = 0
        for ticker, data in portfolio_copy.stocks.items():
            total_value += data['price'] * data['quantity']
            portfolio_copy.cash += data['price'] * data['quantity'] * (1 - sell_commission)
            data['total_sold'] += data['price'] * data['quantity']
            data['quantity_sold'] += data['quantity']
            data['quantity'] = 0

        for ticker, data in portfolio_copy.stocks.items():
            stock_return_rate = portfolio_copy.calculate_stock_return_rate(ticker)
            stock_return_rates[ticker] = {
                'return_rate': stock_return_rate
            }

        directory = './Record'
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, 'stock_rate.json')

        with open(file_path, 'w') as file:
            json.dump(stock_return_rates, file, indent=4)

        return stock_return_rates

    def update_daily_history(self, date):
        
        tmp =  copy.deepcopy(self.stocks)

        # 기록을 저장
        self.daily_history[date.strftime('%Y-%m-%d')] = {
            'cash': self.cash,
            'cash_plus_stock': self.cash_plus_stock,
            'stocks': tmp
        }
        # self.cash_plus_stock = self.get_cash_plus_stocks()

    def get_portfolio_summary(self):
        summary = {
            'date': self.date,
            'cash': self.cash,
            'cash_plus_stock': self.cash_plus_stock,
            'stocks': self.stocks,
            # 'daily_history': self.daily_history
        }
        return summary

    def get_daily_history(self):
        return self.daily_history
    
    def get_daily_history_file(self):
        directory = './Record'
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, 'stock_history.json')

        with open(file_path, 'w') as file:
            json.dump(self.daily_history, file, indent=4)

    def fill_missing_dates(self):
        if not self.daily_history:
            return
        
        start_date = min(self.daily_history.keys())
        end_date = max(self.daily_history.keys())
        
        # stock_price = pd.read_sql('select * from lab_assignment2_open;', con=engine)
        self.stock_price['Date'] = pd.to_datetime(self.stock_price['Date']).dt.date.astype(str)
        self.stock_price = self.stock_price.set_index(['Date']) # 이걸로 인덱스 설정하겠다.
        
        # print(stock_price.index)
        # print(type(stock_price.index))
        
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 시작 날짜부터 끝 날짜까지 하루씩 증가시키면서 반복합니다.
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in self.stock_price.index:
                if date_str not in self.daily_history:
                    previous_date = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
                    # 이전 날짜가 daily_history에 있으면, 그 값을 깊은 복사하여 현재 날짜에 추가합니다.
                    if previous_date in self.daily_history:
                        temp = copy.deepcopy(self.daily_history[previous_date])
                        
                    for ticker in temp['stocks']:
                        temp['stocks'][ticker]['price'] = self.stock_price.loc[date_str, ticker]
                        temp['stocks'][ticker]['quantity_buy'] = 0
                        temp['stocks'][ticker]['quantity_sold'] = 0
                        temp['stocks'][ticker]['return_stock_selling'] = 0
                        temp['cash_plus_stock'] = self.get_cash_plus_stocks()
                    self.daily_history[date_str] = temp
            current_date += timedelta(days=1)

        # 날짜 순으로 정렬
        self.daily_history = OrderedDict(sorted(self.daily_history.items()))

    def plot_rate_of_return_history(self):
        self.fill_missing_dates()  # Fill in missing dates before plotting

        spy_price = []
        dates = []
        cash_plus_stock_values = []
        buy_annotations = {}
        sell_annotations = {}
        returns = []

        for date_str, data in self.daily_history.items():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            dates.append(date)
            spy_price.append(self.stock_price['SPY'][date_str])

            cash_plus_stock_values.append(data['cash_plus_stock'])

            current_value = data['cash_plus_stock']
            returns.append(round((current_value - self.initial_cash) / self.initial_cash * 100, 2))

            for ticker, stock_data in data['stocks'].items():
                if stock_data['quantity_buy'] > 0:
                    if date not in buy_annotations:
                        buy_annotations[date] = []
                    buy_annotations[date].append(f'{ticker}: {stock_data["quantity_buy"]} (Buy)')
                if stock_data['quantity_sold'] > 0:
                    if date not in sell_annotations:
                        sell_annotations[date] = []
                    sell_annotations[date].append(f'{ticker}: {stock_data["quantity_sold"]} (Sell), Return: {stock_data["return_stock_selling"]:.2%}')

        # 수익률 계산
        spy_price = (spy_price - spy_price[0]) / spy_price[0] * 100
        spy_price = [round(price, 2) for price in spy_price]

        #SPY 수익률과 포트폴리오 수익률을 그래프와 라벨로 표시
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=spy_price, mode='lines+markers', name='SPY',
            hovertemplate='%{x|(%b %d, %Y}, %{y:.2f}%)',  # 날짜, 시간 및 % 기호 추가
            line=dict(color='purple'),  # 선 색깔을 보라색으로 설정
            hovertext=[f"{price}%" for price in spy_price],  # Hover 텍스트에 % 기호 추가
            hoverlabel=dict(font=dict(size=16)),  # Set hover text font size
            showlegend=True
        ))

        # 포트폴리오 수익률 그래프 추가
        fig.add_trace(go.Scatter(
            x=dates, y=returns, mode='lines+markers', name='My',
            hovertemplate='%{x|(%b %d, %Y}, %{y:.2f}%)',  # 날짜, 시간 및 % 기호 추가
            hovertext=[f"{price}%" for price in returns],  # Hover 텍스트에 % 기호 추가
            hoverlabel=dict(font=dict(size=16)),  # Set hover text font size
            showlegend=True
        ))

        for date, annotations in buy_annotations.items():
            fig.add_trace(go.Scatter(
                x=[date], y=[returns[dates.index(date)]],
                mode='markers', name='Buy',
                marker=dict(color='red', symbol='triangle-up', size=10),
                text='<br>'.join(annotations),
                hoverlabel=dict(font=dict(size=25)),
                hovertemplate='%{x|(%b %d, %Y}, %{y:.2f}%)' + '<br>' + '<br>'.join(annotations),
                showlegend=False
            ))

        for date, annotations in sell_annotations.items():
            fig.add_trace(go.Scatter(
                x=[date + timedelta(minutes=400)], y=[returns[dates.index(date)]],
                mode='markers', name='Sell',
                marker=dict(color='blue', symbol='triangle-down', size=10),
                text='<br>'.join(annotations),
                hoverlabel=dict(font=dict(size=25)),
                hovertemplate='%{x|(%b %d, %Y}, %{y:.2f})%' + '<br>' + '<br>'.join(annotations),
                showlegend=False
            ))

        fig.update_layout(title='Rate of return',
                        xaxis_title='Date',
                        yaxis_title='Rate of return (%)',
                        showlegend=True,
                        font=dict(size=25),  # Increase the font size for title, axis titles, and legend
                        title_font=dict(size=40),  # Increase the title font size
                        xaxis=dict(title=dict(font=dict(size=30))),  # Increase the x-axis title font size
                        yaxis=dict(title=dict(font=dict(size=30))),  # Increase the y-axis title font size and add % symbol to tick format
                        legend=dict(font=dict(size=40))  # 범례 글꼴 크기 변경               
        )
        fig.write_html("static/day_report.html")

    # def return_stock_selling_minus(self, percen):
    def static_stock(self):
                # 파일 경로 설정
        file_path = 'Record/stock_history.json'

        # JSON 파일 읽기
        with open(file_path, 'r') as file:
            data = json.load(file)

        # 'quantity_buy'가 0이 아닌 경우의 종목별 빈도 계산
        quantity_buy_nonzero = []
        quantity_sold_nonzero = []
        Retun_less_0per = []
        Retun_less_4per = []
        Retun_less_8per = []
        Retun_less_12per = []

        for date, details in data.items():
            for stock, stock_data in details['stocks'].items():
                if stock_data['quantity_buy'] > 0:
                    quantity_buy_nonzero.append(stock)
                if stock_data['quantity_sold'] > 0:
                    quantity_sold_nonzero.append(stock)
                if stock_data['return_stock_selling'] < 0:
                    Retun_less_0per.append(stock)
                if stock_data['return_stock_selling'] < -0.04:
                    Retun_less_4per.append(stock)
                if stock_data['return_stock_selling'] < -0.08:
                    Retun_less_8per.append(stock)
                if stock_data['return_stock_selling'] < -0.12:
                    Retun_less_12per.append(stock)
                

        # 빈도 계산
        quantity_buy_nonzero_counter = Counter(quantity_buy_nonzero)
        quantity_sold_nonzero_counter = Counter(quantity_sold_nonzero)
        Retun_less_0per_counter = Counter(Retun_less_0per)
        Retun_less_4per_counter = Counter(Retun_less_4per)
        Retun_less_8per_counter = Counter(Retun_less_8per)
        Retun_less_12per_counter = Counter(Retun_less_12per)

        # 데이터프레임 생성
        quantity_buy_nonzero_df = pd.DataFrame(quantity_buy_nonzero_counter.items(), columns=['Stock', 'Buy Frequency'])
        quantity_sold_nonzero_df = pd.DataFrame(quantity_sold_nonzero_counter.items(), columns=['Stock', 'Sell Frequency'])
        Retun_less_0per_df = pd.DataFrame(Retun_less_0per_counter.items(), columns=['Stock', 'Retun_less_0per Frequency'])
        Retun_less_4per_df = pd.DataFrame(Retun_less_4per_counter.items(), columns=['Stock', 'Retun_less_4per Frequency'])
        Retun_less_8per_df = pd.DataFrame(Retun_less_8per_counter.items(), columns=['Stock', 'Retun_less_8per Frequency'])
        Retun_less_12per_df = pd.DataFrame(Retun_less_12per_counter.items(), columns=['Stock', 'Retun_less_12per Frequency'])

        # 데이터프레임 리스트 생성
        dfs = [quantity_buy_nonzero_df, quantity_sold_nonzero_df, 
            Retun_less_0per_df, Retun_less_4per_df, 
            Retun_less_8per_df, Retun_less_12per_df]

        # reduce 함수를 사용하여 모든 데이터프레임 병합
        merged_df = reduce(lambda left, right: pd.merge(left, right, on='Stock', how='outer'), dfs).fillna(0)

        # 'Total Frequency' 열 추가 및 3열로 마무리
        merged_df['Total Frequency'] = merged_df[['Buy Frequency', 'Sell Frequency']].sum(axis=1)

        # 'Total Frequency' 열을 3번째 열로 배치
        cols = merged_df.columns.tolist()  # 기존 열 목록 가져오기
        # 'Total Frequency'를 제거하고, 2번 인덱스 위치에 'Total Frequency'를 삽입하여 새 열 순서 생성
        new_cols = cols[:3] + ['Total Frequency'] + cols[3:-1]  
        merged_df = merged_df[new_cols]  # 새 열 순서로 데이터프레임 재구성

        # 'Buy Frequency'로 정렬
        sorted_df = merged_df.sort_values(by='Retun_less_0per Frequency', ascending=False)

        # # 결과 출력
        # print("Stocks with non-zero quantity_buy and quantity_sold:")
        # print(sorted_df)

        # sorted_df를 CSV 파일로 저장
        sorted_df.to_json('Record/sorted_stocks.json', orient='records')