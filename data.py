import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup
import time

# 데이터베이스 연결
engine = create_engine('mysql+pymysql://root:1234@127.0.0.1:3306/stock_db')

# S&P 500 종목 리스트와 섹터 정보 가져오기 (Wikipedia)
wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
response = requests.get(wiki_url)
soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table', {'id': 'constituents'})
sp500_df = pd.read_html(str(table))[0]

# Ticker 리스트 추출
tickers = sp500_df['Symbol'].tolist()

# 데이터를 저장할 DataFrame 생성
all_data = pd.DataFrame()

# 각 종목의 데이터 가져오기
for ticker in tickers:
    try:
        print(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y")  # 지난 5년간의 데이터 가져오기
        hist.reset_index(inplace=True)
        hist['Ticker'] = ticker

        # 섹터 정보 가져오기
        info = stock.info
        sector = info.get('sector', 'Unknown')
        hist['Sector'] = sector

        all_data = pd.concat([all_data, hist])

        # 요청 사이에 대기 시간 추가
        time.sleep(1)  # 1초 대기

    except Exception as e:
        print(f"Could not fetch data for {ticker}: {e}")

# 데이터베이스에 삽입
all_data.to_sql('stock_data', engine, if_exists='append', index=False, 
                dtype={
                    'Date': 'DATETIME',
                    'Ticker': 'VARCHAR(10)',
                    'Open': 'FLOAT',
                    'High': 'FLOAT',
                    'Low': 'FLOAT',
                    'Close': 'FLOAT',
                    'Volume': 'BIGINT',
                    'Sector': 'VARCHAR(50)'
                })

print("Data fetching and insertion completed.")
