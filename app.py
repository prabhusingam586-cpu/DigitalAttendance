from flask import Flask, request, render_template_string
import qrcode
import os
import requests
from datetime import date
from urllib.parse import urlencode

app = Flask(__name__)

GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxiChHGFoV-FNAnEFh17S-Vwi-hFKKDfeQyLXHIEC3B5EVdbNbmLIsziNnpPlQzF9HOMw/exec"

QR_FOLDER = "static/qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)

def get_students():
    response = requests.get(
GOOGLE_SHEET_URL,
params={"type": "students"},
timeout=20
)
response.raise_for_status()
rows = response.json()

```
students = []
for row in rows[1:]:
    if len(row) >= 3 and row[0]:
        students.append({
            "student_id": str(row[0]),
            "student_name": str(row[1]),
            "roll_number": str(row[2])
        })

return students
```

def get_attendance():
response = requests.get(
GOOGLE_SHEET_URL,
params={"type": "attendance"},
timeout=20
)
response.raise_for_status()
rows = response.json()

```
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
```

@app.route("/", methods=["GET", "POST"])
def home():
message = ""

```
if request.method == "POST":
    data = {
        "action": "register",
        "student_id": request.form["student_id"].strip(),
        "student_name": request.form["name"].strip(),
        "roll_number": request.form["roll"].strip()
    }

    try:
        response = requests.post(
            GOOGLE_SHEET_URL,
            json=data,
            timeout=20
        )
        response.raise_for_status()
        message = "Student registered successfully!"
    except requests.RequestException as error:
        message = "Registration failed. Please try again."
        print("Google Sheets Error:", error)

return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Digital Attendance System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: #f1f5fb; padding: 20px; }
        .box { max-width: 600px; margin: auto; background: white;
               padding: 25px; border-radius: 12px; }
        input, button, .link {
            box-sizing: border-box; width: 100%; padding: 12px;
            margin: 8px 0; display: block;
        }
        button, .link { background: #2563eb; color: white;
                        border: 0; text-align: center;
                        text-decoration: none; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Digital Attendance System</h1>
        <h2>Student Registration</h2>
        <form method="POST">
            <label>Student ID</label>
            <input name="student_id" required placeholder="STU006">

            <label>Roll Number</label>
            <input name="roll" required>

            <label>Student Name</label>
            <input name="name" required>

            <button type="submit">Register Student</button>
        </form>

        <p>{{ message }}</p>

        <a class="link" href="/students">Student List</a>
        <a class="link" href="/scan-qr">QR Scanner</a>
        <a class="link" href="/attendance-report">Attendance Report</a>
    </div>
</body>
</html>
""", message=message)
```

@app.route("/students")
def student_list():
try:
students = get_students()

```
    return render_template_string("""
    <h1>Registered Students</h1>
    <p>Total Students: {{ students|length }}</p>

    {% if students %}
    <table border="1" cellpadding="10">
        <tr>
            <th>Student ID</th>
            <th>Name</th>
            <th>Roll Number</th>
            <th>QR Code</th>
        </tr>
        {% for s in students %}
        <tr>
            <td>{{ s.student_id }}</td>
            <td>{{ s.student_name }}</td>
            <td>{{ s.roll_number }}</td>
            <td><a href="/generate-qr/{{ s.student_id }}">Generate QR</a></td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No students found.</p>
    {% endif %}

    <p><a href="/">Back</a></p>
    """, students=students)

except Exception as error:
    print("Student List Error:", error)
    return "Unable to load students. Check Google Sheets settings.", 500
```

@app.route("/generate-qr/<student_id>")
def generate_qr(student_id):
try:
students = get_students()
student = next(
(s for s in students if s["student_id"] == student_id),
None
)

```
    if student is None:
        return "Student not found.", 404

    filename = "student_" + student_id + ".png"
    filepath = os.path.join(QR_FOLDER, filename)

    qrcode.make(student_id).save(filepath)

    return render_template_string("""
    <h1>Student QR Code</h1>
    <p>Student ID: {{ s.student_id }}</p>
    <p>Name: {{ s.student_name }}</p>
    <p>Roll Number: {{ s.roll_number }}</p>
    <img src="/static/qrcodes/{{ filename }}" width="250">
    <p><a href="/students">Back to Student List</a></p>
    """, s=student, filename=filename)

except Exception as error:
    print("QR Error:", error)
    return "Unable to generate QR code.", 500
```

@app.route("/mark-attendance/<student_id>")
def mark_attendance(student_id):
try:
students = get_students()
student = next(
(s for s in students if s["student_id"] == student_id),
None
)

```
    if student is None:
        return "Student not found.", 404

    records = get_attendance()
    today = str(date.today())

    already_marked = any(
        r["student_id"] == student_id
        and r["attendance_date"].startswith(today)
        for r in records
    )

    if already_marked:
        return "Attendance already marked today for " + student["student_name"]

    response = requests.post(
        GOOGLE_SHEET_URL,
        json={
            "student_id": student["student_id"],
            "student_name": student["student_name"],
            "roll_number": student["roll_number"],
            "attendance_date": today
        },
        timeout=20
    )
    response.raise_for_status()

    return "Attendance marked successfully for " + student["student_name"]

except Exception as error:
    print("Attendance Error:", error)
    return "Unable to mark attendance. Please try again.", 500
```

@app.route("/attendance-report")
def attendance_report():
try:
records = get_attendance()

```
    return render_template_string("""
    <h1>Attendance Report</h1>
    {% if records %}
    <table border="1" cellpadding="10">
        <tr>
            <th>Student ID</th>
            <th>Name</th>
            <th>Roll Number</th>
            <th>Attendance Date</th>
        </tr>
        {% for r in records %}
        <tr>
            <td>{{ r.student_id }}</td>
            <td>{{ r.student_name }}</td>
            <td>{{ r.roll_number }}</td>
            <td>{{ r.attendance_date }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No attendance records found.</p>
    {% endif %}
    <p><a href="/">Back</a></p>
    """, records=records)

except Exception as error:
    print("Attendance Report Error:", error)
    return "Unable to load attendance report.", 500
```

@app.route("/scan-qr")
def scan_qr():
return render_template_string(""" <!DOCTYPE html> <html> <head> <title>QR Attendance Scanner</title> <meta name="viewport" content="width=device-width, initial-scale=1"> <script src="https://unpkg.com/html5-qrcode"></script> </head> <body> <h2>Scan Student QR Code</h2> <div id="reader" style="width:100%; max-width:400px"></div> <p id="result">Allow camera access to scan.</p>

```
    <script>
        function onScanSuccess(decodedText) {
            window.location.href =
                "/mark-attendance/" + encodeURIComponent(decodedText);
        }

        const scanner = new Html5QrcodeScanner(
            "reader",
            { fps: 10, qrbox: 250 }
        );

        scanner.render(onScanSuccess);
    </script>
    <p><a href="/">Back</a></p>
</body>
</html>
""")
```

if **name** == "**main**":
app.run(host="0.0.0.0", port=5000, debug=True)
