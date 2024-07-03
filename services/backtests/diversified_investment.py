import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import numpy as np
import quantstats as qs
import plotly.express as px

# Read the data into a DataFrame
origin_data = pd.read_csv("../../uploads/backtest.csv")
origin_data['date'] = pd.to_datetime(origin_data['date']).dt.date.astype(str)
origin_data = origin_data.set_index(['date']) # 이걸로 인덱스 설정하겠다.
date_to_symbols = origin_data.groupby('date')['ticker'].apply(list).to_dict()

engine = create_engine('mysql+pymysql://root:1234@127.0.0.1:3306/stock_db')
stock_price = pd.read_sql('select * from lab_assignment2_open;', con=engine)
stock_price['Date'] = pd.to_datetime(stock_price['Date']).dt.date.astype(str)
stock_price = stock_price.set_index(['Date']) # 이걸로 인덱스 설정하겠다.
engine.dispose()

for date in stock_price.index:
    if date not in date_to_symbols.keys():
        date_to_symbols[date] = []

date_to_symbols = {date: date_to_symbols[date] for date in sorted(date_to_symbols)}

i = 0
tax = 0.001

Cumulative_Return = {'Date': [], 'Price':[], 'Daily_Rerutn':[], 'Cumulative Return':[]}
initial_f = 100000

initial_f_array = [initial_f/3, initial_f/3, initial_f/3]

def trade_stocks(date, symbols, initial_f_array, i):
    if not symbols:
        return
    
    initial_funds = initial_f_array[i]
    # 주식 데이터를 가져옵니다.
    start_date = date
    end_date = (pd.Timestamp(start_date) + pd.DateOffset(days=9)).strftime('%Y-%m-%d')  # 8일간의 데이터를 포함하려면 7일을 더해야 합니다.

    # 해당 날짜 범위에 있는 데이터 선택
    data = stock_price.loc[start_date:end_date]
    data = data.dropna()

    if data.empty:
        return "데이터를 불러오는데 실패했습니다. 날짜나 주식 기호를 확인해주세요."
    
    # 첫째 날 조정 종가를 가져옵니다.
    buy_adj_prices = (data.iloc[0])[symbols]

    # 각 주식에 할당할 자금을 계산합니다.
    funds_per_stock = initial_funds / len(symbols)
    
    # 주식을 구매합니다.
    stocks_owned = {}
    for symbol, price in buy_adj_prices.items():
        if price <= funds_per_stock:
            stocks_owned[symbol] = int(funds_per_stock // price)  # 소수 주식은 제외된다.
    print("stocks_owned")
    print(stocks_owned)

    # 셋째 날 조정 종가를 가져와서 매도합니다.
    try:
        adj_closing_prices = data.iloc[3]
    except IndexError:
        # tmp_fund = sum(initial_f_array)
        # initial_f_array[i] = initial_funds
        # result_tmp_fund = sum(initial_f_array)

        # Cumulative_Return['Date'].append(data.index[0])
        # Cumulative_Return['Price'].append(result_tmp_fund)
        # Cumulative_Return['Daily_Rerutn'].append((result_tmp_fund-tmp_fund)/tmp_fund*100)
        # Cumulative_Return['Cumulative Return'].append((result_tmp_fund-initial_f)/initial_f*100)
        return

    tmp_fund = sum(initial_f_array)
    # 최종 자금을 계산합니다.
    for symbol, owned in stocks_owned.items():
        initial_funds -= owned * buy_adj_prices[symbol] 
        initial_funds += owned * adj_closing_prices[symbol] * (1 - tax)
    
    initial_f_array[i] = initial_funds
    result_tmp_fund = sum(initial_f_array)

    Cumulative_Return['Date'].append(data.index[3])
    Cumulative_Return['Price'].append(result_tmp_fund)
    Cumulative_Return['Daily_Rerutn'].append((result_tmp_fund-tmp_fund)/tmp_fund*100)
    Cumulative_Return['Cumulative Return'].append((result_tmp_fund-initial_f)/initial_f*100)

    return 

print(date_to_symbols)
initial_funds = initial_f

for date, symbols in date_to_symbols.items():
    print(date)
    trade_stocks(date, symbols, initial_f_array, i)
    i = i+1
    if i > 2:
        i = 0

result = sum(initial_f_array)

print(f"처음 자금: ${initial_funds:.2f}")
print(f"최종 자금: ${result:.2f}")
print(f"수익률: {(result-initial_funds)/initial_funds*100:.2f}%")

# 'Price' 리스트에서 MDD 계산
prices = np.array(Cumulative_Return['Price'])
peak_prices = np.maximum.accumulate(prices)  # 각 시점까지의 최대 포트폴리오 가치
drawdowns = (prices - peak_prices) / peak_prices  # 각 시점에서의 drawdown 계산
max_drawdown = drawdowns.min()  # 최대 drawdown

print(f"최대 손실율 (MDD): {max_drawdown * 100:.2f}%")

# DataFrame 생성
df = pd.DataFrame(Cumulative_Return)
df['Date'] = pd.to_datetime(df['Date'])  # 날짜 형식으로 변환
df = df.set_index('Date')  # 인덱스를 날짜로 설정

# Debugging: Print the DataFrame
print(df)

# Ensure there are no zero values in the returns calculation
df['Price'] = df['Price'].replace(0, np.nan).dropna()


# 수익률 계산
prices = df['Price']
prices.index.name = None
# 추가할 데이터
additional_data = pd.Series({"2024-05-13": 100000})
# 추가할 데이터의 인덱스를 datetime 형식으로 변환
additional_data.index = pd.to_datetime(additional_data.index)

# 기존 데이터에 추가
prices = pd.concat([pd.Series(additional_data), prices])

returns = prices.pct_change().dropna()  # 첫 번째 NaN 값을 제거

print("returns @@@@")
print(returns)
report = qs.reports.metrics(returns)
print(report)
# Ensure returns does not contain zero values
# if returns.isnull().any() or (returns == 0).any():
#     print("Returns contain zero values or NaNs, which will cause division by zero.")
# else:
#     # 수익률 데이터로 메트릭스 보고서 생성
#     # report = qs.reports.metrics(returns)
#     # print(report)
    
    # # MDD 계산 및 출력
    # qs.stats.drawdown_details(returns)

    # # 그래프 표시
    # qs.plots.snapshot(returns, figsize=(10, 6))

# Plotly Express를 사용해 선 그래프 생성
fig = px.line(df, x=df.index, y='Cumulative Return', title='Cumulative Return')

# 그래프 표시
fig.show()

# Plotly Express를 사용해 선 그래프 생성
fig = px.line(df, x=df.index, y='Daily_Rerutn', title='Daily Returns Over Time')

# 그래프 표시
fig.show()
