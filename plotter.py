import plotly.graph_objects as go

fig = go.Figure(data=go.Bar(y=[2, 3, 1]))
fig.write_html('first_figure.html', auto_open=True)

# https://plot.ly/python/creating-and-updating-figures/
# https://plot.ly/python/reference/#candlestick
# https://plot.ly/python/candlestick-charts/
# https://community.plot.ly/t/how-to-plot-both-ohlc-and-volume/32761
# https://plot.ly/python/subplots/#subplots-with-shared-xaxes
