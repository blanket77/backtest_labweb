from services.Client.StockPortfolio import StockPortfolio
from services.Client.strategy.day_buy_day_sell import *
import csv
from datetime import datetime

# __main__ 를 쓰기 위해 변경(위에 두줄 코드는 주석처리)
# from Client.StockPortfolio import StockPortfolio
# from Client.strategy.day_buy_day_sell import get_date_to_symbols, trade_stocks

def find_earliest_date(filename):
    earliest_date = None
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # 날짜 파싱: 'M/D/YYYY' 형식을 datetime 객체로 변환
            date = datetime.strptime(row['date'], '%m/%d/%Y')
            if earliest_date is None or date < earliest_date:
                earliest_date = date
    return earliest_date.strftime('%Y-%m-%d') if earliest_date else None

def run_portfolio_analysis():
    date_to_symbols = get_date_to_symbols("uploads/backtest.csv")
    earliest_date = find_earliest_date('uploads/backtest.csv')
    portfolio = StockPortfolio(earliest_date, 1000000000)

    # 여기서 date_to_symbols는 어딘가에서 정의되어 있어야 합니다.
    for date, symbols in date_to_symbols.items():
        trade_stocks(portfolio, date, symbols, 2)

    portfolio.plot_rate_of_return_history()

    portfolio.get_portfolio_summary()
    portfolio.calculate_return_rate()
    portfolio.get_daily_history()
    #주식 수익률 계산하고 json으로 저장
    portfolio.calculate_all_stock_return_rates('stock_rate_adj.json')
    #주식 기록 파일 생성
    portfolio.get_daily_history_file('stock_history.json')
    #주식 기록을 읽어서 데이터 전처리 이후 json으로 저장
    portfolio.statistics_stock('Record/stock_history.json', 'Record/sorted_stock.json')
    portfolio.fig.write_html("static/day_report.html")

if __name__ == '__main__':
    run_portfolio_analysis()
