"""
Helpers for turning SurveyMonkey's raw response/question JSON into a
simple table: one row per response, one column per question.
"""


def build_question_map(survey_details):
    """
    Walks a survey's page/question structure and returns:
      - question_map: question_id -> {"text": str, "choices": {id: text}, "position": int}
      - ordered_question_ids: list of question_ids in survey order
    """
    question_map = {}
    ordered_question_ids = []
    position = 0

    for page in survey_details.get("pages", []):
        for question in page.get("questions", []):
            qid = question["id"]
            headings = question.get("headings", [{}])
            heading = headings[0].get("heading") if headings else None
            heading = heading or question.get("family", "Question")

            choices = {}
            for choice in (question.get("answers", {}).get("choices") or []):
                choices[choice["id"]] = choice.get("text", "")
            # Matrix-style questions also have "rows" - store those labels too
            for row in (question.get("answers", {}).get("rows") or []):
                choices[row["id"]] = row.get("text", "")

            question_map[qid] = {
                "text": heading,
                "choices": choices,
                "position": position,
            }
            ordered_question_ids.append(qid)
            position += 1

    return question_map, ordered_question_ids


def flatten_response(response, question_map):
    """
    Converts one raw response object into a flat dict keyed by question
    text, plus "_id" and "_date_submitted". Multiple answers to the same
    question (checkboxes, matrix rows) are joined with '; '.
    """
    flat = {
        "_id": response.get("id"),
        "_date_submitted": response.get("date_created"),
    }

    for page in response.get("pages", []):
        for question in page.get("questions", []):
            qid = question.get("id")
            qinfo = question_map.get(qid)
            if not qinfo:
                continue

            texts = []
            for answer in question.get("answers", []):
                if "text" in answer:
                    texts.append(answer["text"])
                elif "row_id" in answer and "choice_id" in answer:
                    row_label = qinfo["choices"].get(answer["row_id"], "")
                    choice_label = qinfo["choices"].get(answer["choice_id"], "")
                    combined = f"{row_label}: {choice_label}".strip(": ")
                    if combined:
                        texts.append(combined)
                elif "choice_id" in answer:
                    label = qinfo["choices"].get(answer["choice_id"], "")
                    if label:
                        texts.append(label)

            flat[qinfo["text"]] = "; ".join(t for t in texts if t)

    return flat


def responses_to_table(responses, question_map, ordered_question_ids):
    """
    Returns (columns, rows):
      columns: ["Date Submitted"] + question texts, in survey order
      rows: list of dicts keyed by those same column names, plus "_id"
    """
    question_texts = []
    seen = set()
    for qid in ordered_question_ids:
        qinfo = question_map.get(qid)
        if qinfo and qinfo["text"] not in seen:
            question_texts.append(qinfo["text"])
            seen.add(qinfo["text"])

    columns = ["Date Submitted"] + question_texts

    rows = []
    for r in responses:
        flat = flatten_response(r, question_map)
        row = {"Date Submitted": flat.get("_date_submitted", ""), "_id": flat["_id"]}
        for qtext in question_texts:
            row[qtext] = flat.get(qtext, "")
        rows.append(row)

    return columns, rows
