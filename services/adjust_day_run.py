import pandas as pd
from sqlalchemy import create_engine
from Client.StockPortfolio import StockPortfolio
from Client.strategy.day_buy_day_sell import *

# CSV 파일 읽기
df = pd.read_csv('signal_dass_open_d3_us_sp500.csv')
remove_tickers = input("Enter the tickers separated by commas (e.g., AAPL,MSFT,GOOGL): ")

# 입력 문자열을 대문자로 변환하고, 쉼표로 구분하여 리스트로 변환
remove_tickers = [ticker.strip().upper() for ticker in remove_tickers.split(',')]

# 리스트에 포함된 종목 제거
df_filtered = df[~df['ticker'].isin(remove_tickers)]

# 날짜별로 그룹화하고 각 그룹에 대해 가중치 조정
adjusted_weights = []
for date, group in df_filtered.groupby('date'):
    total_weight = group['weight'].sum()
    adjusted_group = group.copy()
    adjusted_group['weight'] = group['weight'] / total_weight  # 가중치 조정
    adjusted_weights.append(adjusted_group)

# 조정된 데이터프레임 생성
adjusted_df = pd.concat(adjusted_weights)

# 조정된 데이터를 새로운 CSV 파일로 저장
adjusted_df.to_csv('./signal_dass_open_d3_us_sp500_readjust.csv', index=False)

portfolio2 = StockPortfolio('2024-06-20', 1000000)
date_to_symbols = get_date_to_symbols("signal_dass_open_d3_us_sp500_readjust.csv")

for date, symbols in date_to_symbols.items():
    trade_stocks(portfolio2, date, symbols)

portfolio2.plot_rate_of_return_history()

print(portfolio2.get_portfolio_summary())
print(f"Overall Return Rate: {portfolio2.calculate_return_rate()}%")
print(f"Daily History: {portfolio2.get_daily_history()}")
print(f"\n\nIndividual Stock Return Rates: {portfolio2.calculate_all_stock_return_rates()}")
portfolio2.get_daily_history_file()

