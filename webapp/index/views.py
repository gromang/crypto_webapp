from flask import Blueprint, render_template

blueprint = Blueprint('index', __name__)


@blueprint.route("/")
def index():
    title = "Diagram"
    return render_template('index/index.html', page_title=title)

@blueprint.errorhandler(404)
def page_not_found(error):
    return render_template('index/page_not_found.html'), 404