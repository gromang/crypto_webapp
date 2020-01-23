from flask import Flask, render_template, request
from webapp.plotter import candle_chart
from webapp.forms import ChartForm
from webapp.config import intervals


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    @app.route('/')
    def index():
        title = "CryptoCandle"
        
        return render_template('index.html', page_title=title)

    @app.route('/api', methods=["GET"])
    def api():
        pair = request.args.get("pair", "BTCUSD")
        interval = int(request.args.get("interval", 1))
        depth = int(request.args.get("depth", 40))
        chart = candle_chart(pair, interval, depth)
        title = "API"
        return render_template('api.html', page_title=title, chart=chart)

    @app.route('/chart', methods=["GET"])
    def chart():
        title = "Chart"
        chart_menu = ChartForm()
        if chart_menu.is_submitted():
            interval = intervals[chart_menu.interval.data]
            pair = str(chart_menu.pair.data)
            depth = int(chart_menu.depth.data)
        else:
            interval = intervals[chart_menu.interval.default]
            pair = str(chart_menu.pair.default)
            depth = int(chart_menu.depth.default)

        chart = candle_chart(pair, interval, depth)
        return render_template(
            'chart.html',
            page_title=title,
            chart=chart,
            form=chart_menu)

    @app.route('/demo')
    def demo():
        title = "Demo"
        chart = candle_chart("BTCUSD", 30, 50)
        return render_template('demo.html', page_title=title, chart=chart)

    @app.route('/chart_example')
    def chart_example():
        title = "Example"
        chart = candle_chart("BTCUSD", 30, 50)
        return render_template('chart_example.html', page_title=title, chart=chart)

    return app
