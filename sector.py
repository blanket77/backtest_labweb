import yfinance as yf

def get_stock_sector(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    sector = info.get('sector', 'Sector information not available')
    return sector

# 예시: 애플(AAPL)의 섹터 정보 가져오기
ticker = 'AAPL'
sector = get_stock_sector(ticker)
print(f"The sector for {ticker} is: {sector}")