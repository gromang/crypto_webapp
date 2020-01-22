import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import offline

from webapp.get_data import CryptoData


def candle_chart(pair: str, interval: int, depth: int):
    crypto_data = CryptoData(pair, interval, depth).data_for_plotly()
    #fig = make_subplots(rows=2, cols=1)
    fig = go.Figure(data=[go.Candlestick(
        x=crypto_data["datetime"],
        open=crypto_data["open"],
        high=crypto_data["high"],
        low=crypto_data["low"],
        close=crypto_data["close"])],
        layout=go.Layout(
            # xaxis=dict(showgrid=False),
            # yaxis=dict(showgrid=False),
            template="plotly_dark",

    ))
    #fig.show()
    div = offline.plot(fig, include_plotlyjs=False, output_type='div')
    return div

if __name__ == "__main__":
    candle_chart("BTCUSD", 30, 50)
#fig.write_html('test.html', auto_open=True)

# https://plot.ly/python/creating-and-updating-figures/
# https://plot.ly/python/reference/#candlestick
# https://plot.ly/python/candlestick-charts/
# https://community.plot.ly/t/how-to-plot-both-ohlc-and-volume/32761
# https://plot.ly/python/subplots/#subplots-with-shared-xaxes

