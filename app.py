from flask import Flask, render_template, request, redirect, session, jsonify
from config import get_db

app = Flask(__name__)
app.secret_key = "rail_secret"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (username, password))
        user = cur.fetchone()

        cur.close()
        db.close()

        if user:
            session["user"] = user["username"]
            session["dept"] = user["department"]
            return redirect("/entry")

        return render_template("login.html", error="Invalid login")

    return render_template("login.html")


# ---------------- ENTRY PAGE ----------------
@app.route("/entry")
def entry():
    if "user" not in session:
        return redirect("/")

    return render_template("entry.html", user=session["user"])


# ---------------- API ROUTES ----------------
@app.route("/api/data", methods=["GET"])
def get_data():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM rail ORDER BY id")
    data = cur.fetchall()

    cur.close()
    db.close()

    return jsonify(data)


@app.route("/api/save", methods=["POST"])
def save_row():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    db = get_db()
    cur = db.cursor()

    # Insert or update based on id
    if data.get("id"):
        # Update existing
        cur.execute("""
            UPDATE rail SET
                category=%s, points=%s, plan=%s, responsibility=%s, support=%s,
                assigned_date=%s, due_date=%s, revised_date=%s, priority=%s,
                status=%s, completed_percent=%s, notes=%s
            WHERE id=%s
        """, (
            data["category"], data["points"], data["plan"], data["responsibility"], data["support"],
            data["assigned_date"], data["due_date"], data["revised_date"], data["priority"],
            data["status"], data["completed_percent"], data["notes"], data["id"]
        ))
    else:
        # Insert new
        cur.execute("""
            INSERT INTO rail (category, points, plan, responsibility, support,
                              assigned_date, due_date, revised_date, priority,
                              status, completed_percent, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["category"], data["points"], data["plan"], data["responsibility"], data["support"],
            data["assigned_date"], data["due_date"], data["revised_date"], data["priority"],
            data["status"], data["completed_percent"], data["notes"]
        ))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"success": True})


@app.route("/api/delete/<int:row_id>", methods=["DELETE"])
def delete_row(row_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM rail WHERE id=%s", (row_id,))
    db.commit()

    cur.close()
    db.close()

    return jsonify({"success": True})


# ---------------- ADD ENTRY ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO rail
        (project, action_plan, responsibility, support, notes,
         date_assigned, date_due, date_of_ageing, priority, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        request.form["project"],
        request.form["action_plan"],
        request.form["responsibility"],
        request.form["support"],
        request.form["notes"],
        request.form["date_assigned"],
        request.form["date_due"],
        request.form["date_of_ageing"],
        request.form["priority"],
        request.form["status"]
    ))

    db.commit()
    cur.close()
    db.close()

    return redirect("/entry")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port="5002")