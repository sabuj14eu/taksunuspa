from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from flask_login import login_user, logout_user

from ...config import Config
from ...models.user import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        u = User.query.filter_by(phone=phone).first()
        if u and u.is_active_flag and u.check_password(request.form.get("password", "")):
            login_user(u)
            nxt = request.args.get("next", "")
            # Only same-site redirects — an open redirect here is a phishing gift.
            if nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect(url_for("admin.dashboard"))
        flash("Wrong phone or password")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.home"))


@bp.route("/lang/<code>")
def set_lang(code):
    if code in Config.LANGUAGES:
        session["lang"] = code
    ref = request.referrer or ""
    if ref.startswith(request.host_url):
        return redirect(ref)
    return redirect(url_for("public.home"))
