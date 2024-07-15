import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from sqlalchemy import create_engine
import numpy as np
from datetime import timedelta

# 데이터베이스에서 데이터 불러오기
engine = create_engine('mysql+pymysql://root:1234@127.0.0.1:3306/stock_db')
stock_price_df = pd.read_sql('select * from lab_assignment;', con=engine)
engine.dispose()

# JSON 파일에서 데이터 불러오기
file_path = 'Record/stock_history.json'
data = pd.read_json(file_path).to_dict()

def one_stock_plotly(stock_symbol):
    dates = []
    prices = []
    buys = []
    sells = []
    return_stock_selling = []
    cash_plus_stock_values = []

    for date, details in data.items():
        cash_plus_stock_values.append(details['cash_plus_stock'])
        if stock_symbol in details['stocks']:
            stock_data = details['stocks'][stock_symbol]
            buys.append(stock_data['quantity_buy'])
            sells.append(stock_data['quantity_sold'])
            return_stock_selling.append(stock_data['return_stock_selling']*100)
        else:
            buys.append(0)
            sells.append(0)
            return_stock_selling.append(0)


    dates = stock_price_df['Date'].tolist()
    prices = stock_price_df[stock_symbol].tolist()
    prices = [round(price, 2) for price in prices]
    # prices 리스트를 numpy 배열로 변환
    prices_array = np.array(prices)

    for i in range(len(dates)-len(buys)):
        buys.append(0)
        sells.append(0)
        return_stock_selling.append(0)
        cash_plus_stock_values.append(0)

    # 누적 수익률 계산
    cumulative_returns = (prices_array - prices_array[0]) / prices_array[0] * 100

    # Creating a plotly figure
    fig = make_subplots(rows=1, cols=1)

    # Adding hovertext for the stock price line
    price_hovertext = [
        f"Date: {dates[i].strftime('%d/%m/%Y')}<br>"
        f"CR: {cumulative_returns[i]:.1f}%"
        for i in range(len(dates))
    ]

    # Adding stock price line
    fig.add_trace(go.Scatter(x=dates, y=cumulative_returns, mode='lines', name='Price', 
                             line=dict(color='purple'),
                             hoverlabel=dict(font=dict(size=20)),
                             hovertext=price_hovertext, hoverinfo='text'), row=1, col=1)
    
    # Adding buy points
    buy_hovertext = [
        f"Date: {dates[i].strftime('%d/%m/%Y')}<br>"
        f"CR: {cumulative_returns[i]:.1f}%<br>"
        f"{stock_symbol}: {prices[i] * buys[i] / cash_plus_stock_values[i]*100:.1f}%"
        for i in range(len(dates)) if buys[i] > 0
    ]
    fig.add_trace(go.Scatter(x=[dates[i] + timedelta(minutes=400) for i in range(len(dates)) if buys[i] > 0], 
                             y=[cumulative_returns[i] for i in range(len(dates)) if buys[i] > 0], 
                             mode='markers', name='Buy', 
                             marker=dict(color='red', symbol='triangle-up', size=15),
                             hoverlabel=dict(font=dict(size=20)),
                             hovertext=buy_hovertext,
                             hoverinfo='text'), row=1, col=1)
    
    # Adding sell points
    sell_hovertext = [
        f"Date: {dates[i].strftime('%d/%m/%Y')}<br>"
        f"CR: {cumulative_returns[i]:.1f}%<br>"
        f"{stock_symbol} : {prices[i] * sells[i] / cash_plus_stock_values[i]*100:.1f}%<br>"
        f"ROI: {return_stock_selling[i]:.1f}%"
        for i in range(len(dates)) if sells[i] > 0
    ]
    fig.add_trace(go.Scatter(x=[dates[i] - timedelta(minutes=400) for i in range(len(dates)) if sells[i] > 0], 
                             y=[cumulative_returns[i] for i in range(len(dates)) if sells[i] > 0], 
                             mode='markers', name='Sell', 
                             marker=dict(color='blue', symbol='triangle-down', size=15),
                             hoverlabel=dict(font=dict(size=20)),
                             hovertext=sell_hovertext,
                             hoverinfo='text'), row=1, col=1)

    # Updating layout
    fig.update_layout(
                hoverlabel_align = 'right',
                title={'text': f'{stock_symbol} Stock Cumulative Returns(CR) with Buy/Sell Points',
                        'font': {'size': 24}},
                xaxis_title='Date',
                yaxis_title='Cumulative Returns(%)',
                xaxis=dict(title=dict(font=dict(size=17))),  # Increase the x-axis title font size
                yaxis=dict(title=dict(font=dict(size=17))),  # Increase the y-axis title font size
                showlegend=True
                )

    fig.write_html("C:/Users/ggp05/OneDrive/Desktop/myproject/static/stock_plot.html")

if __name__ == '__main__':
    one_stock_plotly('HPQ')
