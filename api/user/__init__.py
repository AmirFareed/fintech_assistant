from flask import Blueprint


user_bp = Blueprint(
    "user_widget",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


from . import routes  # noqa: E402,F401
