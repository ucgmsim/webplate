import flask

bp = flask.Blueprint("views", __name__)


@bp.route("/", methods=["GET"])
def index() -> str:
    """Serve the standard index page."""
    return flask.render_template("views/index.html")
