import plotly.graph_objects as go

# 예제 데이터
x_data = ['2023-07-01', '2023-07-02', '2023-07-03', '2023-07-04', '2023-07-05']
y_data = [10, 15, 13, 17, 14]
annotations = ["SBAC: 1551.0 (Buy)", "PARA: 26200.0 (Buy)", "GM: 8663.0 (Buy)"]

# hovertemplate 설정
hovertemplate = (
    '<b>Date:</b> %{x|%m/%d/%Y}<br>' +
    '<table style="width:100%;">' +
    '<tr><td style="text-align:left;">CR:</td><td style="text-align:right;">%{y:.2f}%</td></tr>' +
    ''.join(f'<tr><td colspan="2">{annotation}</td></tr>' for annotation in annotations) +
    '</table>'
)

# 그래프 생성
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x_data,
    y=y_data,
    mode='lines+markers',
    hovertemplate=hovertemplate
))

# 그래프 출력
fig.show()
