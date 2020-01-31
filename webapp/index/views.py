from flask import Blueprint, render_template

blueprint = Blueprint('index', __name__)


@blueprint.route("/")
def index():
    title = "Diagram"
    return render_template('index/index.html', page_title=title)


@blueprint.errorhandler(404)
def page_not_found(error):
    title = "404 page"
    error_msg = "Sorry, page not found"
    return render_template(
        'index/error_page.html',
        error_msg=error_msg,
        page_title=title), 404


@blueprint.route("/error_page")
def error_page():
    title = "Error Page"
    error_msg = "Pizdec ti vse slomal"
    return render_template(
        'index/error_page.html',
        error_msg=error_msg,
        page_title=title)
