from flask import Flask, request, render_template_string
import qrcode
import os
import requests
from datetime import date

app = Flask(__name__)

GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxiChHGFoV-FNAnEFh17S-Vwi-hFKKDfeQyLXHIEC3B5EVdbNbmLIsziNnpPlQzF9HOMw/exec"

QR_FOLDER = "static/qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)

STYLE = """
<style>
* {
    box-sizing: border-box;
}
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #172033;
}
.nav {
    background: #173b70;
    color: white;
    padding: 18px 24px;
    font-size: 20px;
    font-weight: bold;
}
.container {
    width: 92%;
    max-width: 1050px;
    margin: 35px auto;
}
.card {
    background: white;
    padding: 28px;
    border-radius: 16px;
    border: 1px solid #e5eaf2;
    box-shadow: 0 8px 25px rgba(15, 23, 42, 0.05);
}
h1 {
    font-size: 27px;
    margin-top: 0;
}
.subtitle {
    color: #64748b;
    line-height: 1.6;
}
label {
    display: block;
    margin: 15px 0 7px;
    font-size: 14px;
    font-weight: bold;
}
input {
    width: 100%;
    padding: 13px;
    border: 1px solid #dbe2ec;
    border-radius: 8px;
    font-size: 15px;
}
input:focus {
    outline: 2px solid #93c5fd;
    border-color: #2563eb;
}
.btn {
    display: inline-block;
    padding: 12px 17px;
    border: 0;
    border-radius: 8px;
    text-decoration: none;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    text-align: center;
}
.primary {
    background: #2456a6;
    color: white;
}
.secondary {
    background: #eaf0f8;
    color: #173b70;
}
.full {
    width: 100%;
    margin-top: 20px;
}
.links {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px;
    margin-top: 25px;
}
.link-card {
    background: white;
    border: 1px solid #e1e8f2;
    border-radius: 12px;
    padding: 20px;
    text-decoration: none;
    color: #173b70;
    font-weight: bold;
}
.link-card:hover {
    border-color: #2456a6;
    background: #f8fbff;
}
.message {
    margin-top: 15px;
    color: #15803d;
    font-weight: bold;
}
.table-wrap {
    width: 100%;
    overflow-x: auto;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    background: white;
}
th, td {
    padding: 14px;
    text-align: left;
    border-bottom: 1px solid #e5eaf2;
    white-space: nowrap;
}
th {
    background: #edf3fb;
    color: #173b70;
    font-size: 13px;
}
td {
    font-size: 14px;
}
tr:hover td {
    background: #f8fbff;
}
.section-label {
    color: #64748b;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}
.student-name {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 22px;
    overflow-wrap: anywhere;
}
.details {
    border-top: 1px solid #e5eaf2;
    border-bottom: 1px solid #e5eaf2;
    padding: 15px 0;
    margin-bottom: 24px;
}
.detail-row {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    margin: 12px 0;
    font-size: 14px;
}
.detail-row span:first-child {
    color: #64748b;
}
.detail-row span:last-child {
    font-weight: bold;
    text-align: right;
    overflow-wrap: anywhere;
}
.qr-card {
    max-width: 390px;
    margin: 25px auto;
    padding: 0;
    overflow: hidden;
    text-align: center;
}
.qr-header {
    background: #173b70;
    color: white;
    padding: 25px 18px;
}
.qr-header h2 {
    margin: 0;
    font-size: 21px;
}
.qr-header p {
    font-size: 11px;
    letter-spacing: 2px;
    margin-bottom: 0;
    color: #dbeafe;
}
.qr-body {
    padding: 27px 24px;
}
.qr-image {
    width: 210px;
    height: 210px;
    max-width: 100%;
    object-fit: contain;
    border: 1px solid #e5eaf2;
    border-radius: 12px;
    padding: 10px;
}
.qr-caption {
    color: #64748b;
    font-size: 12px;
    line-height: 1.6;
    margin: 15px 0 22px;
}
.qr-actions {
    display: grid;
    gap: 10px;
}
.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    margin-top: 25px;
}
@media (max-width: 600px) {
    .container {
        margin: 20px auto;
    }
    .card {
        padding: 20px;
    }
    h1 {
        font-size: 23px;
    }
}
@media print {
    body {
        background: white;
    }
    .no-print, .footer {
        display: none !important;
    }
    .qr-card {
        box-shadow: none;
        border: 1px solid #ddd;
    }
    .qr-header {
        background: #173b70 !important;
        color: white !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}
</style>
"""


def page(content, title="Digital Attendance"):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{{ title }}</title>
        """ + STYLE + """
    </head>
    <body>
        <div class="nav">Digital Attendance System</div>
        """ + content + """
        <div class="footer">Digital Attendance Management System</div>
    </body>
    </html>
    """, title=title)


def get_students():
    response = requests.get(
        GOOGLE_SHEET_URL,
        params={"type": "students"},
        timeout=20
    )
    response.raise_for_status()
    rows = response.json()

    students = []

    for row in rows[1:]:
        if len(row) >= 3 and row[0]:
            students.append({
                "student_id": str(row[0]),
                "student_name": str(row[1]),
                "roll_number": str(row[2])
            })

    return students


def get_attendance():
    response = requests.get(
        GOOGLE_SHEET_URL,
        params={"type": "attendance"},
        timeout=20
    )
    response.raise_for_status()
    rows = response.json()

    records = []

    for row in rows[1:]:
        if len(row) >= 4 and row[0]:
            records.append({
                "student_id": str(row[0]),
                "student_name": str(row[1]),
                "roll_number": str(row[2]),
                "attendance_date": str(row[3])
            })

    return records


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        student_id = request.form["student_id"].strip()
        student_name = request.form["name"].strip()
        roll_number = request.form["roll"].strip()

        try:
            students = get_students()

            if any(s["student_id"] == student_id for s in students):
                message = "Student ID already exists."
            else:
                response = requests.post(
                    GOOGLE_SHEET_URL,
                    json={
                        "action": "register",
                        "student_id": student_id,
                        "student_name": student_name,
                        "roll_number": roll_number
                    },
                    timeout=20
                )
                response.raise_for_status()
                message = "Student registered successfully!"

        except Exception as error:
            print("Registration Error:", error)
            message = "Registration failed. Please try again."

    content = """
    <div class="container">
        <div class="card">
            <h1>Student Registration</h1>
            <p class="subtitle">
                Register students and manage attendance in one place.
            </p>

            <form method="POST">
                <label>Student ID</label>
                <input name="student_id" required placeholder="STU006">

                <label>Roll Number</label>
                <input name="roll" required placeholder="Enter roll number">

                <label>Student Name</label>
                <input name="name" required placeholder="Enter student name">

                <button class="btn primary full" type="submit">
                    Register Student
                </button>
            </form>

            {%
