"""
Client-facing portal: lets one client log in and see their own exit
interview responses, combined across collectors, grouped by brand.

This is intentionally minimal right now (login + raw response table).
Filtering, sorting, and charts get layered in once we've nailed down
exactly what the client should be able to do.
"""

import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session

from config import CLIENTS
import surveymonkey_client as sm

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("client_key"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/", methods=["GET"])
def index():
    if session.get("client_key"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        entered_password = request.form.get("password", "")

        # Check the entered password against every configured client.
        # With one client today this is simple; with more clients later,
        # each still gets its own separate password.
        matched_client_key = None
        for client_key, client_cfg in CLIENTS.items():
            expected = os.environ.get(client_cfg["password_env"])
            if expected and entered_password == expected:
                matched_client_key = client_key
                break

        if matched_client_key:
            session["client_key"] = matched_client_key
            return redirect(url_for("dashboard"))
        else:
            error = "Incorrect password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    client_key = session["client_key"]
    client_cfg = CLIENTS[client_key]

    brand_name = request.args.get("brand") or next(iter(client_cfg["brands"]))
    if brand_name not in client_cfg["brands"]:
        brand_name = next(iter(client_cfg["brands"]))

    collector_ids = client_cfg["brands"][brand_name]["collector_ids"]
    responses = sm.get_brand_responses(collector_ids, start_created_at="2026-01-01T00:00:00Z")

    return render_template(
        "dashboard.html",
        client_display_name=client_cfg["display_name"],
        brands=list(client_cfg["brands"].keys()),
        active_brand=brand_name,
        responses=responses,
        response_count=len(responses),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
