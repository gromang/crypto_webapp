from webapp.config import intervals
from webapp.plotter import candle_chart
from flask import Blueprint, render_template, request
from webapp.chart.forms import ChartForm

blueprint = Blueprint('chart', __name__)


@blueprint.route('/api', methods=["GET"])
def api():
    pair = request.args.get("pair", "BTCUSD")
    interval = int(request.args.get("interval", 1))
    depth = int(request.args.get("depth", 40))
    chart = candle_chart(pair, interval, depth)
    title = "API"
    return render_template('chart/api.html', page_title=title, chart=chart)


@blueprint.route('/chart', methods=["GET", "POST"])
def chart():
    title = "Chart"
    chart_menu = ChartForm()
    if request.method == "POST":
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
        'chart/chart.html',
        page_title=title,
        chart=chart,
        form=chart_menu)


@blueprint.route('/demo')
def demo():
    title = "Demo"
    chart = candle_chart("BTCUSD", 30, 50)
    return render_template('chart/demo.html', page_title=title, chart=chart)
