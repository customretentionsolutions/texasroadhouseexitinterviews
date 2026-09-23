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
    responses = sm.get_brand_responses(collector_ids, start_created_at=RESPONSES_START_DATE)

    survey_id = client_cfg["brands"][brand_name]["survey_id"]
    survey_details = sm.get_survey_details(survey_id)
    question_map, ordered_question_ids = build_question_map(survey_details)

    columns, rows = responses_to_table(responses, question_map, ordered_question_ids)

    all_question_columns = columns[1:]  # everything except "Date Submitted"
    selected_columns = request.args.getlist("cols")
    if not selected_columns:
        # Nothing chosen yet - show a short default set instead of all ~50 questions
        selected_columns = all_question_columns[:5]
    display_columns = ["Date Submitted"] + [c for c in all_question_columns if c in selected_columns]

    position_counts = Counter((r.get("Position") or "Unknown") for r in rows)
    chart_labels_json = json.dumps(list(position_counts.keys()))
    chart_values_json = json.dumps(list(position_counts.values()))	

    # --- Filters ---
    search_term = request.args.get("search", "").strip()
    filter_question = request.args.get("filter_question", "")
    filter_answer = request.args.get("filter_answer", "").strip()

    if search_term:
        needle = search_term.lower()
        rows = [
            r for r in rows
            if any(needle in str(v).lower() for k, v in r.items() if k != "_id")
        ]

    if filter_question and filter_answer:
        needle = filter_answer.lower()
        rows = [r for r in rows if needle in str(r.get(filter_question, "")).lower()]

        return render_template(
        "dashboard.html",
        client_display_name=client_cfg["display_name"],
        brands=list(client_cfg["brands"].keys()),
        active_brand=brand_name,
        columns=display_columns,
        rows=rows,
        response_count=len(rows),
        search_term=search_term,
        filter_question=filter_question,
        filter_answer=filter_answer,
        filterable_questions=all_question_columns,
        all_question_columns=all_question_columns,
        selected_columns=selected_columns,
        chart_labels_json=chart_labels_json,
        chart_values_json=chart_values_json,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
