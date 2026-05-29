from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)

app.secret_key = "studyvault_secret_key_2026"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "StudyVault@2026"


# ==========================
# DATABASE CREATION
# ==========================

def create_database():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,

        subject TEXT,

        filename TEXT,

        status TEXT
    )
    """)

    conn.commit()
    conn.close()


create_database()


# ==========================
# HOME PAGE
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# UPLOAD PAGE
# ==========================

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        title = request.form.get("title")

        subject = request.form.get("subject")

        file = request.files.get("file")

        if file and file.filename.endswith(".pdf"):

            filepath = os.path.join(
                "uploads",
                file.filename
            )

            file.save(filepath)

            conn = sqlite3.connect("database.db")

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO materials
                (title, subject, filename, status)

                VALUES (?, ?, ?, ?)
                """,
                (
                    title,
                    subject,
                    file.filename,
                    "Pending"
                )
            )

            conn.commit()
            conn.close()

            return redirect("/upload")

    return render_template("upload.html")


# ==========================
# SUBJECT PAGE
# ==========================

@app.route("/subject/<subject_name>")
def subject(subject_name):

    db_subject = subject_name.title()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM materials
        WHERE subject=?
        AND status='Approved'
        """,
        (db_subject,)
    )

    materials = cursor.fetchall()

    conn.close()

    return render_template(
        "subject.html",
        subject_name=db_subject,
        materials=materials
    )


# ==========================
# ADMIN LOGIN
# ==========================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect("/dashboard")

        return "Invalid Username or Password"

    return render_template("admin.html")


# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materials ORDER BY id DESC")
    materials = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM materials")
    total_uploads = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM materials WHERE status='Pending'"
    )
    pending_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM materials WHERE status='Approved'"
    )
    approved_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        materials=materials,
        total_uploads=total_uploads,
        pending_count=pending_count,
        approved_count=approved_count
    )
@app.route("/approve/<int:id>")
def approve(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE materials
        SET status='Approved'
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")
@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT filename FROM materials WHERE id=?",
        (id,)
    )

    result = cursor.fetchone()

    if result:

        filename = result[0]

        filepath = os.path.join(
            "uploads",
            filename
        )

        if os.path.exists(filepath):
            os.remove(filepath)

    cursor.execute(
        "DELETE FROM materials WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/admin")


# ==========================
# START APP
# ==========================

@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        "uploads",
        filename,
        as_attachment=True
    )
@app.route("/search")
def search():

    query = request.args.get("q", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM materials
        WHERE status='Approved'
        AND (
            title LIKE ?
            OR subject LIKE ?
        )
        """,
        (
            "%" + query + "%",
            "%" + query + "%"
        )
    )

    results = cursor.fetchall()

    conn.close()

    return render_template(
        "search.html",
        query=query,
        results=results
    )
@app.route("/admin-upload", methods=["POST"])
def admin_upload():

    if not session.get("admin"):
        return redirect("/admin")

    title = request.form["title"]

    subject = request.form["subject"]

    file = request.files["file"]

    if file:

        filepath = os.path.join(
            "uploads",
            file.filename
        )

        file.save(filepath)

        conn = sqlite3.connect(
            "database.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO materials
            (title, subject, filename, status)

            VALUES (?, ?, ?, ?)
            """,
            (
                title,
                subject,
                file.filename,
                "Approved"
            )
        )

        conn.commit()

        conn.close()

    return redirect("/dashboard")
@app.route("/contact")
def contact():

    return render_template("contact.html")
if __name__ == "__main__":
    app.run(debug=True)