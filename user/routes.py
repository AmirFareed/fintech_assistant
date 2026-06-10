from flask import render_template

from . import user_bp


@user_bp.get("/")
def user_widget_demo():
    return render_template("user/demo.html")
