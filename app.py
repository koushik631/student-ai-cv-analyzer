
import os
from datetime import datetime, timezone

import docx
import PyPDF2
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import students, cv_analyses
from Ai import analyze_resume

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")


# HOME
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# SIGNUP
# Keep /singnup temporarily as an alias for older template links.
@app.route("/signup", methods=["GET", "POST"])
@app.route("/singnup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return "Email and password are required.", 400

        if students.find_one({"email": email}):
            return "User already exists. Please log in."

        students.insert_one({
            "email": email,
            "password": generate_password_hash(
    password,
    method="pbkdf2:sha256"
),
            "created_at": datetime.now(timezone.utc)
        })

        return redirect("/login")

    return render_template("signup.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = students.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            return redirect("/dashboard")

        return "Invalid email or password.", 401

    return render_template("login.html")


# DASHBOARD AND CV ANALYSIS
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":
        user_goal = request.form.get("role", "").strip()
        resume_text = request.form.get("resume", "").strip()
        uploaded_file = request.files.get("file")

        # Read an uploaded PDF or DOCX resume.
        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename.lower()

            try:
                if filename.endswith(".pdf"):
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = "\n".join(
                        page.extract_text() or ""
                        for page in pdf_reader.pages
                    )
                    resume_text = "\n".join(
                        part for part in [resume_text, extracted_text] if part
                    )

                elif filename.endswith(".docx"):
                    document = docx.Document(uploaded_file)
                    extracted_text = "\n".join(
                        paragraph.text for paragraph in document.paragraphs
                    )
                    resume_text = "\n".join(
                        part for part in [resume_text, extracted_text] if part
                    )

                else:
                    result = {
                        "error": "Please upload a PDF or DOCX file."
                    }

            except Exception as error:
                result = {"error": f"Could not read resume: {error}"}

        if result is None:
            if not resume_text:
                result = {"error": "Please enter resume text or upload a resume."}
            elif not user_goal:
                result = {"error": "Please enter your target job role."}
            else:
                try:
                    result = analyze_resume(resume_text, user_goal)

                    if not isinstance(result, dict):
                        result = {"error": "The AI returned an invalid result."}

                    # Save the analysis in MongoDB only if AI analysis succeeded.
                    if "error" not in result:
                        cv_analyses.insert_one({
                            "email": session["user"],
                            "resume_text": resume_text,
                            "user_goal": user_goal,
                            "result": result,
                            "created_at": datetime.now(timezone.utc)
                        })

                except Exception as error:
                    result = {"error": f"Analysis failed: {error}"}

    return render_template(
        "dashboard.html",
        user=session["user"],
        result=result
    )


# ANALYSIS HISTORY
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    reports = list(
        cv_analyses.find(
            {"email": session["user"]},
            {"email": 0}
        ).sort("created_at", -1)
    )

    # Provide both names for compatibility with existing templates.
    for report in reports:
        report["resume"] = report.get("resume_text", "")
        report["result"] = report.get("result", {})

    return render_template(
        "history.html",
        user=session["user"],
        reports=reports
    )


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
