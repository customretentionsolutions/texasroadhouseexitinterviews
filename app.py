"""
Client-facing portal: lets one client log in and see their own exit
interview responses, combined across collectors, grouped by brand, as
a searchable/filterable table of actual questions and answers.
"""

import os
import json
from collections import Counter
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify

from config import CLIENTS
import surveymonkey_client as sm
from response_utils import build_question_map, responses_to_table

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")

# Only pull responses from this date forward - keeps memory/load reasonable
# and matches what the client actually wants to see.
RESPONSES_START_DATE = "2026-01-01T00:00:00Z"


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