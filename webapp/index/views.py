from flask import Blueprint, render_template

blueprint = Blueprint('index', __name__)


@blueprint.route("/")
def index():
    title = "CryptoCandle"
    return render_template('index/index.html', page_title=title)
