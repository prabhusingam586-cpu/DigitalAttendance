from flask import Flask, request, render_template_string
import mysql.connector
import qrcode
import os
import requests

GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxiChHGFoV-FNAnEFh17S-Vwi-hFKKDfeQyLXHIEC3B5EVdbNbmLIsziNnpPlQzF9HOMw/exec"

app = Flask(__name__)
from datetime import date, datetime

QR_FOLDER = "static/qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)


# MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD"),
        database="attendance_db"
    )

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    success = False

    if request.method == "POST":
        student_id = request.form["student_id"].strip()
        roll = request.form["roll"].strip()
        name = request.form["name"].strip()
        department = request.form["department"].strip()
        year_of_study = request.form["year_of_study"]

        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO students
                (student_id, roll_number, student_name,
                 department, year_of_study)
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (
                    student_id,
                    roll,
                    name,
                    department,
                    year_of_study
                )
            )

            conn.commit()

            message = "Student registered successfully!"
            success = True

        except mysql.connector.Error as error:
            if conn is not None:
                conn.rollback()

            print("MySQL Error:", error)
            message = "Registration failed: " + str(error)

        finally:
            if cursor is not None:
                cursor.close()

            if conn is not None:
                conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digital Attendance System</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }

            body {
                margin: 0;
                background: #f1f5fb;
                color: #1e293b;
            }

            header {
                background: #1e40af;
                color: white;
                padding: 22px 30px;
            }

            header h2 {
                margin: 0;
            }

            .container {
                max-width: 650px;
                margin: 35px auto;
                padding: 30px;
                background: white;
                border-radius: 14px;
                box-shadow: 0 5px 22px #dbe3ef;
            }

            h1 {
                color: #1e40af;
                margin-top: 0;
            }

            label {
                display: block;
                margin: 15px 0 7px;
                font-weight: bold;
            }

            input, select {
                width: 100%;
                padding: 12px;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                font-size: 15px;
            }

            button, .link-button {
                display: block;
                width: 100%;
                padding: 13px;
                margin-top: 20px;
                border: none;
                border-radius: 7px;
                background: #2563eb;
                color: white;
                font-size: 16px;
                text-align: center;
                text-decoration: none;
                cursor: pointer;
            }

            button:hover, .link-button:hover {
                background: #1d4ed8;
            }

            .message {
                margin-top: 18px;
                padding: 12px;
                border-radius: 7px;
                font-weight: bold;
                overflow-wrap: anywhere;
            }

            .success {
                background: #dcfce7;
                color: #166534;
            }

            .failure {
                background: #fee2e2;
                color: #991b1b;
            }

            @media (max-width: 700px) {
                .container {
                    margin: 20px;
                    padding: 22px;
                }
            }
        </style>
    </head>

    <body>
        <header>
            <h2>Digital Attendance System</h2>
        </header>

        <div class="container">
            <h1>Student Registration</h1>
            <p>Enter the student details below.</p>

            <form method="POST">
                <label>Student ID</label>
                <input
                    type="text"
                    name="student_id"
                    required
                >

                <label>Roll Number</label>
                <input
                    type="text"
                    name="roll"
                    required
                >

                <label>Student Name</label>
                <input
                    type="text"
                    name="name"
                    required
                >

                <label>Department</label>
                <input
                    type="text"
                    name="department"
                    required
                >

                <label>Year of Study</label>
                <select name="year_of_study" required>
                    <option value="">Select Year</option>
                    <option value="1">First Year</option>
                    <option value="2">Second Year</option>
                    <option value="3">Third Year</option>
                    <option value="4">Fourth Year</option>
                </select>

                <button type="submit">
                    Register Student
                </button>
            </form>

            {% if message %}
            <p class="message {{ 'success' if success else 'failure' }}">
                {{ message }}
            </p>
            {% endif %}

            <a class="link-button" href="/students">
                View Student List
            </a>
            <a class="link-button" href="/scan-qr">
    QR Scanner
</a>

<a class="link-button" href="/attendance-report">
    Attendance Report
</a>

        </div>
    </body>
    </html>
    """, message=message, success=success)


@app.route("/test-db")
def test_db():
    conn = None

    try:
        conn = get_db_connection()
        return "MySQL Connection Successful!"

    except mysql.connector.Error as error:
        return "Database Error: " + str(error), 500

    finally:
        if conn is not None:
            conn.close()


@app.route("/students")
def student_list():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT student_id, roll_number, student_name,
                   department, year_of_study
            FROM students
            ORDER BY student_id
        """)

        students = cursor.fetchall()

        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Student List</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">

            <style>
                * {
                    box-sizing: border-box;
                    font-family: Arial, sans-serif;
                }

                body {
                    margin: 0;
                    padding: 25px;
                    background: #f1f5fb;
                    color: #1e293b;
                }

                .container {
                    max-width: 1100px;
                    margin: 20px auto;
                    padding: 25px;
                    background: white;
                    border-radius: 14px;
                    box-shadow: 0 5px 22px #dbe3ef;
                }

                h1 {
                    color: #1e40af;
                }

                .count {
                    color: #1e40af;
                    font-weight: bold;
                }

                .table-wrapper {
                    overflow-x: auto;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }

                th, td {
                    padding: 13px;
                    border-bottom: 1px solid #ddd;
                    text-align: left;
                }

                th {
                    background: #1e40af;
                    color: white;
                }

                tr:hover {
                    background: #edf3ff;
                }

                .button {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 11px 18px;
                    background: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 7px;
                }

                .empty {
                    padding: 20px;
                    background: #eff6ff;
                    border-radius: 8px;
                }
            </style>
        </head>

        <body>
            <div class="container">
                <h1>Registered Students</h1>

                <p>
                    Total Students:
                    <span class="count">{{ students|length }}</span>
                </p>

                {% if students %}
                <div class="table-wrapper">
                    <table>
                        <tr>
                            <th>Student ID</th>
                            <th>Roll Number</th>
                            <th>Name</th>
                            <th>Department</th>
                            <th>Year</th>
                            <th>QR Code</th>
                        </tr>

                        {% for s in students %}
                        <tr>
                            <td>{{ s.student_id }}</td>
                            <td>{{ s.roll_number }}</td>
                            <td>{{ s.student_name }}</td>
                            <td>{{ s.department }}</td>
                            <td>{{ s.year_of_study }}</td>
                            <td>
    <a href="/generate-qr/{{ s.student_id }}">Generate QR</a>
</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                {% else %}
                    <p class="empty">
                        No students registered yet.
                    </p>
                {% endif %}

                <a class="button" href="/">Back to Registration</a>
            </div>
        </body>
        </html>
        """, students=students)

    except Exception as e:
        print("Registration Error:",e)
        return "Registration failed:" + str(e)

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()
            
@app.route("/generate-qr/<int:student_id>")
def generate_qr(student_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT student_id, roll_number, student_name
            FROM students
            WHERE student_id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:
            return "Student not found!", 404

        qr_data = str(student["student_id"])

        filename = f"student_{student['student_id']}.png"
        filepath = os.path.join(QR_FOLDER, filename)

        img = qrcode.make(qr_data)
        img.save(filepath)

        return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Student QR Code</title>
                <meta name="viewport"
                      content="width=device-width, initial-scale=1">
            </head>
            <body style="font-family: Arial; text-align: center;
                         padding: 30px;">

                <h1>Student QR Code</h1>

                <p><b>Student ID:</b> {student['student_id']}</p>
                <p><b>Name:</b> {student['student_name']}</p>
                <p><b>Roll Number:</b> {student['roll_number']}</p>

                <img src="/static/qrcodes/{filename}"
                     width="250"
                     alt="Student QR Code">

                <br><br>

                <a href="/students">Back to Student List</a>

            </body>
            </html>
        """

    except Exception as e:
        print("QR Code Error:", e)
        return "QR Code Error: " + str(e), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()
@app.route("/mark-attendance/<int:student_id>")
def mark_attendance(student_id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD"),
        database="attendance_db"
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE student_id = %s",
        (student_id,)
    )
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found"

    try:
        cursor.execute(
            """
            INSERT INTO attendance
            (student_id, attendance_date, attendance_time, status)
            VALUES (%s, %s, %s, %s)
            """,
            (student_id, date.today(), datetime.now().time(), "Present")
        )
        conn.commit()
        requests.post(
    GOOGLE_SHEET_URL,
    json={
        "student_id": student["student_id"],
        "student_name": student["student_name"],
        "roll_number": student["roll_number"],
        "attendance_date": str(date.today())
    }
)
        message = f"Attendance marked successfully for {student['student_name']}!"

    except mysql.connector.IntegrityError:
        message = "Attendance already marked for today!"

    cursor.close()
    conn.close()

    return message

@app.route("/attendance-report")
def attendance_report():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT attendance.*, students.student_name, students.roll_number
        FROM attendance
        JOIN students ON attendance.student_id = students.student_id
        ORDER BY attendance.attendance_date DESC
    """)

    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template_string("""
        <h1>Attendance Report</h1>
        <table border="1" cellpadding="10">
            <tr>
                <th>Student ID</th>
                <th>Name</th>
                <th>Roll Number</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
            </tr>
            {% for r in records %}
            <tr>
                <td>{{ r.student_id }}</td>
                <td>{{ r.student_name }}</td>
                <td>{{ r.roll_number }}</td>
                <td>{{ r.attendance_date }}</td>
                <td>{{ r.attendance_time }}</td>
                <td>{{ r.status }}</td>
            </tr>
            {% endfor %}
        </table>
        <a href="/">Back</a>
    """, records=records)


@app.route("/scan-qr")
def scan_qr():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>QR Attendance Scanner</title>
        <script src="https://unpkg.com/html5-qrcode"></script>
    </head>
    <body>
        <h2>Digital Attendance System</h2>
        <h3>Scan Student QR Code</h3>

        <div id="reader" style="width:400px"></div>
        <script>
    function onScanSuccess(decodedText) {
        window.location.href = "/mark-attendance/" + decodedText;
    }

    const scanner = new Html5QrcodeScanner(
        "reader",
        {
            fps: 10,
            qrbox: { width: 250, height: 250 }
        }
    );

    scanner.render(onScanSuccess);
</script>
        <p id="result">PLEASE SCAN YOUR QR CODE.</p>
    </body>
    </html>
    """)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
