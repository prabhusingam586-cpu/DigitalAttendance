from flask import Flask, request, redirect, url_for, session 
from pymongo import MongoClient
from functools import wraps
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import qrcode
import os
import io
import base64

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view

mongo_url = os.environ.get("MONGO_URI")

if mongo_url:
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
    db = client["digital_attendance"]
    students = db["students"]
    attendance = db["attendance"]
else:
    client = None
    db = None
    students = None
    attendance = None


def check_database():
    """Check whether MongoDB is connected."""
    if client is None:
        return False

    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False


def make_page(title, body):
    """Show a simple page with the same design."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f2f5f9;
                margin: 0;
                padding: 20px;
                color: #222;
            }}
            .box {{
                max-width: 850px;
                margin: 20px auto;
                background: white;
                padding: 24px;
                border-radius: 10px;
                box-shadow: 0 2px 10px #ddd;
            }}
            h1, h2 {{ color: #234b7a; }}
            input, button {{
                box-sizing: border-box;
                width: 100%;
                padding: 10px;
                margin: 7px 0 14px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            button, .button {{
                background: #234b7a;
                color: white;
                border: 0;
                padding: 10px 14px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                width: auto;
            }}
            a {{ color: #234b7a; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 9px; border: 1px solid #ddd; text-align: left; }}
            th {{ background: #e8eef6; }}
            .message {{ padding: 12px; background: #e8f5e9; border-radius: 5px; }}
            .nav a {{ margin-right: 12px; }}
            /* Mobile table text overflow fix */
table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
}

th, td {
    overflow-wrap: anywhere;
    word-break: break-word;
    white-space: normal;
    padding: 8px;
    box-sizing: border-box;
}

@media (max-width: 600px) {
    table {
        font-size: 12px;
    }

    th, td {
        padding: 6px 4px;
    }
}
        </style>
    </head>
    <body>
        <div class="box">
            <div class="nav">
                <a href="/">Register</a>
                <a href="/students">Students</a>
                <a href="/scan-qr">Scan QR</a>
                <a href="/attendance-report">Attendance Report</a>
            </div>
            <hr>
            {body}
        </div>
    </body>
    </html>
    """


def database_error_page():
    return make_page(
        "Database connection",
        "<h2>MongoDB connection is not ready</h2>"
        "<p>Check the MONGO_URI environment variable in Render, then try again.</p>"
    )
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == os.environ.get("ADMIN_USERNAME")
            and password == os.environ.get("ADMIN_PASSWORD")
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("home"))

        return make_page(
            "Admin Login",
            "<h2>Invalid username or password</h2><a href='/login'>Try again</a>"
        )

    body = """
    <h1>Admin Login</h1>
    <form method="POST">
        <label>Username</label>
        <input name="username" required>
        <label>Password</label>
        <input type="password" name="password" required>
        <button type="submit">Login</button>
    </form>
    """
    return make_page("Admin Login", body)

@app.route("/")
@login_required
def home():
    body = """
    <h1>Digital Attendance System</h1>
    <h2>Register Student</h2>
    <form method="POST" action="/add-student">
        <label>Student ID</label>
        <input name="student_id" required>

        <label>Student Name</label>
        <input name="student_name" required>

        <label>Roll Number</label>
        <input name="roll_number" required>

        <label>Department</label>
        <input name="department" required>

        <label>Year of Study</label>
        <input name="year_of_study" required>

        <button type="submit">Register Student</button>
    </form>
    """
    return make_page("Digital Attendance", body)


@app.route("/add-student", methods=["POST"])
@login_required
def add_student():
    if not check_database():
        return database_error_page()

    student_id = request.form.get("student_id", "").strip()
    student_name = request.form.get("student_name", "").strip()
    roll_number = request.form.get("roll_number", "").strip()
    department = request.form.get("department", "").strip()
    year_of_study = request.form.get("year_of_study", "").strip()

    if not all([student_id, student_name, roll_number, department, year_of_study]):
        return make_page("Registration", "<p>Please fill in every field.</p>")

    try:
        students.insert_one({
            "student_id": student_id,
            "student_name": student_name,
            "roll_number": roll_number,
            "department": department,
            "year_of_study": year_of_study,
            "created_at": datetime.now()
        })
    except DuplicateKeyError:
        return make_page(
            "Registration",
            "<h2>Student ID already exists.</h2><a href='/'>Go back</a>"
        )
    except Exception as error:
        return make_page("Registration", f"<h2>Could not save student.</h2><p>{error}</p>")

    return make_page(
        "Registration",
        "<h2>Student registered successfully!</h2><a href='/students'>View Students</a>"
    )



@app.route("/students")
@login_required
def student_list():
    if not check_database():
        return database_error_page()

    student_rows = list(students.find().sort("student_name", 1))
    rows = ""

    for student in student_rows:
        student_id = student.get("student_id", "")
        name = student.get("student_name", "")
        roll = student.get("roll_number", "")
        department = student.get("department", "")
        year = student.get("year_of_study", "")

        rows += f"""
        <tr>
            <td>{student_id}</td>
            <td>{name}</td>
            <td>{roll}</td>
            <td>{department}</td>
            <td>{year}</td>
            <td><a href="/generate-qr/{student_id}">Generate QR</a></td>
        </tr>
        """

    body = f"""
    <h1>Student List</h1>
    <table>
        <tr>
            <th>Student ID</th><th>Name</th><th>Roll Number</th>
            <th>Department</th><th>Year</th><th>QR Code</th>
        </tr>
        {rows}
    </table>
    """
    return make_page("Students", body)


@app.route("/generate-qr/<student_id>")
@login_required
def generate_qr(student_id):
    if not check_database():
        return database_error_page()

    student = students.find_one({"student_id": student_id})
    if student is None:
        return make_page("QR Code", "<h2>Student not found.</h2>")

    attendance_url = request.url_root.rstrip("/") + url_for(
        "mark_attendance", student_id=student_id
    )

    qr = qrcode.make(attendance_url)
    image_file = io.BytesIO()
    qr.save(image_file, format="PNG")
    qr_image = base64.b64encode(image_file.getvalue()).decode("utf-8")

    body = f"""
    <h1>Student QR Code</h1>
    <p><b>Name:</b> {student.get('student_name', '')}</p>
    <p><b>Student ID:</b> {student_id}</p>
    <img src="data:image/png;base64,{qr_image}" alt="Student QR Code">
    <p>Scan this QR code to open the attendance page.</p>
    """
    return make_page("QR Code", body)


@app.route("/mark-attendance/<student_id>")
def mark_attendance(student_id):
    if not check_database():
        return database_error_page()

    student = students.find_one({"student_id": student_id})
    if student is None:
        return make_page("Attendance", "<h2>Student not found.</h2>")

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    try:
        attendance.insert_one({
            "student_id": student_id,
            "student_name": student.get("student_name", ""),
            "attendance_date": today,
            "attendance_time": now.strftime("%H:%M:%S"),
            "status": "Present"
        })
    except DuplicateKeyError:
        return make_page(
            "Attendance",
            f"<h2>Attendance already marked for {student.get('student_name', '')} today.</h2>"
        )
    except Exception as error:
        return make_page("Attendance", f"<h2>Could not mark attendance.</h2><p>{error}</p>")

    return make_page(
        "Attendance",
        f"<h2>Attendance marked successfully!</h2>"
        f"<p>Name: {student.get('student_name', '')}</p>"
        f"<p>Student ID: {student_id}</p>"
        f"<p>Date: {today}</p><p>Time: {now.strftime('%H:%M:%S')}</p>"
    )


@app.route("/scan-qr")
@login_required
def scan_qr():
    body = """
    <style>
        .box { max-width: 1000px; }
        .scanner-page { color: #edf3ff; }
        .scanner-hero {
            background: linear-gradient(135deg, #101a35, #233f73 60%, #286c88);
            color: white;
            padding: 30px;
            border-radius: 18px;
            margin: 18px 0;
            box-shadow: 0 14px 35px rgba(25, 48, 88, .18);
        }
        .scanner-hero h1 { color: white; font-size: 30px; margin: 8px 0; }
        .scanner-hero p { color: #d8e5ff; line-height: 1.6; }
        .eyebrow { text-transform: uppercase; letter-spacing: 2px; font-size: 12px; font-weight: bold; color: #a9d9ff; }
        .scanner-layout { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(220px, .8fr); gap: 20px; }
        .scanner-card, .guide-card { background: #fff; border: 1px solid #e4eaf2; border-radius: 16px; padding: 22px; box-shadow: 0 8px 24px rgba(26, 48, 80, .07); }
        .scanner-card h2, .guide-card h2 { margin-top: 0; }
        #reader { width: 100%; overflow: hidden; border-radius: 12px; }
        #reader video { border-radius: 12px; }
        #reader button { width: auto; margin: 6px; }
        #reader select { max-width: 100%; padding: 8px; border-radius: 8px; }
        .status-pill { display: inline-block; padding: 7px 11px; background: #edf7f2; color: #18794e; border-radius: 20px; font-size: 13px; font-weight: bold; }
        .guide-item { display: flex; gap: 12px; margin: 18px 0; align-items: flex-start; }
        .guide-number { min-width: 30px; height: 30px; display: grid; place-items: center; background: #eaf1ff; color: #234b7a; border-radius: 9px; font-weight: bold; }
        .guide-item p { margin: 4px 0 0; color: #667085; font-size: 14px; line-height: 1.5; }
        #message { padding: 12px; background: #f3f6fb; color: #344054; border-radius: 10px; min-height: 20px; }
        @media (max-width: 700px) { .scanner-layout { grid-template-columns: 1fr; } .scanner-hero { padding: 22px; } .scanner-hero h1 { font-size: 25px; } }
    </style>

    <div class="scanner-page">
        <div class="scanner-hero">
            <div class="eyebrow">Digital Attendance · Live Scanner</div>
            <h1>Scan student QR code</h1>
            <p>Use your camera to scan a registered student's QR code and open their attendance page.</p>
            <span class="status-pill">● Scanner ready</span>
        </div>

        <div class="scanner-layout">
            <section class="scanner-card">
                <h2>Camera scanner</h2>
                <p style="color:#667085">Allow camera access when your browser asks.</p>
                <div id="reader"></div>
                <p id="message" role="status">Starting scanner…</p>
            </section>

            <aside class="guide-card">
                <h2>How to use</h2>
                <div class="guide-item">
                    <span class="guide-number">1</span>
                    <div><b>Allow camera</b><p>Choose Allow when the browser requests camera permission.</p></div>
                </div>
                <div class="guide-item">
                    <span class="guide-number">2</span>
                    <div><b>Point at the QR</b><p>Keep the code inside the scanner frame and hold your device steady.</p></div>
                </div>
                <div class="guide-item">
                    <span class="guide-number">3</span>
                    <div><b>Confirm attendance</b><p>After scanning, the student attendance page will open.</p></div>
                </div>
                <hr style="border:0;border-top:1px solid #e8edf4;margin:20px 0"
            </aside>
        </div>
    </div>

    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        function qrSuccess(decodedText) {
            document.getElementById("message").innerText = "QR code found. Opening attendance page…";
            window.location.href = decodedText;
        }

        if (typeof Html5QrcodeScanner !== "undefined") {
            const scanner = new Html5QrcodeScanner("reader", {
                fps: 10,
                qrbox: { width: 230, height: 230 },
                rememberLastUsedCamera: true
            });
            scanner.render(qrSuccess, function () {});
            document.getElementById("message").innerText = "Ready. Point the camera at a student QR code.";
        } else {
            document.getElementById("message").innerText = "Scanner could not load. Check your internet connection and refresh the page.";
        }
    </script>
    """
    return make_page("Scan QR | Digital Attendance", body)


@app.route("/attendance-report")
@login_required
def attendance_report():
    if not check_database():
        return database_error_page()

    records = list(attendance.find().sort([
        ("attendance_date", -1),
        ("attendance_time", -1)
    ]))

    rows = ""
    for record in records:
        rows += f"""
        <tr>
            <td>{record.get('student_id', '')}</td>
            <td>{record.get('student_name', '')}</td>
            <td>{record.get('attendance_date', '')}</td>
            <td>{record.get('attendance_time', '')}</td>
            <td>{record.get('status', '')}</td>
        </tr>
        """

    body = f"""
    <h1>Attendance Report</h1>
    <table>
        <tr>
            <th>Student ID</th><th>Name</th><th>Date</th>
            <th>Time</th><th>Status</th>
        </tr>
        {rows}
    </table>
    """
    return make_page("Attendance Report", body)


if __name__ == "__main__":
    if check_database():
        students.create_index("student_id", unique=True)
        attendance.create_index(
            [("student_id", 1), ("attendance_date", 1)],
            unique=True
        )

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
