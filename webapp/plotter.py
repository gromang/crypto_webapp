import plotly.graph_objects as go
from plotly import offline

from webapp.get_data import CryptoData


def candle_chart(pair: str, interval: int, depth: int):
    crypto_data = CryptoData(pair, interval, depth).data_for_plotly()
    fig = go.Figure(
            data=[go.Candlestick(
                    x=crypto_data["datetime"],
                    open=crypto_data["open"],
                    high=crypto_data["high"],
                    low=crypto_data["low"],
                    close=crypto_data["close"])],
            layout=go.Layout(
                annotations=[
                    go.layout.Annotation(
                        name="chart_name",
                        text = f"{pair} {interval}",
                        opacity=0.3,
                        font=dict(color='white', size=30),
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.9,
                        showarrow=False,)
                    ],
                autosize=True,
                xaxis=dict(showgrid=True),
                yaxis=dict(showgrid=True, side="right"),
                template="plotly_dark",
                plot_bgcolor="#343a40",
                paper_bgcolor="#343a40",
                margin=go.layout.Margin(l=5, r=15, b=10, t=30, pad=10),
                xaxis_rangeslider_visible=False,
                 ),
    )

    div = offline.plot(fig, include_plotlyjs=False, output_type='div')
    return div

# https://community.plot.ly/t/how-to-plot-both-ohlc-and-volume/32761
# https://plot.ly/~jackp/17421/plotly-candlestick-chart-in-python/#/
