import os
import tkinter as tk
from tkinter import messagebox, ttk
import openpyxl
from openpyxl import Workbook
import datetime
import matplotlib.pyplot as plt
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template, send_file

# Flask App Setup
app = Flask(__name__)

# Email Configuration
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"

# Database Setup
def init_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Send Email Notification
def send_email_notification(name, status):
    if status not in ["Absent", "Late"]:
        return  # Only send emails for absent or late cases
    
    subject = f"Attendance Alert: {name} is {status}"
    body = f"Hello,\n\n{name} was marked as {status} on {datetime.date.today()}. Please take necessary action.\n\nBest Regards,\nAttendance System"
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = "recipient_email@example.com"  # Change this to the appropriate recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, "recipient_email@example.com", msg.as_string())
        server.quit()
    except Exception as e:
        print("Error sending email:", e)

# Attendance Marking
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.json
    name = data["name"]
    status = data["status"]
    date = datetime.date.today().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance (name, date, status) VALUES (?, ?, ?)", (name, date, status))
    conn.commit()
    conn.close()
    
    update_excel(name, date, status)
    send_email_notification(name, status)
    
    return jsonify({"message": "Attendance marked successfully!"})

# Excel Integration
def update_excel(name, date, status):
    file = "attendance.xlsx"
    if not os.path.exists(file):
        wb = Workbook()
        ws = wb.active
        ws.append(["Name", "Date", "Status"])
    else:
        wb = openpyxl.load_workbook(file)
        ws = wb.active
    
    ws.append([name, date, status])
    wb.save(file)

# Generate Report (Pie Chart for Selected Student)
@app.route("/get_report/<name>")
def get_report(name):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM attendance WHERE name = ? GROUP BY status", (name,))
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        return jsonify({"message": f"No attendance records found for {name}"})
    
    labels, sizes = zip(*data)
    plt.figure()
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['green', 'red', 'orange'])
    plt.title(f"Attendance Report for {name}")
    plt.axis("equal")
    plt.show()
    
    return jsonify({"name": name, "data": data})

# Download Attendance Excel File
@app.route("/download_excel")
def download_excel():
    file = "attendance.xlsx"
    if os.path.exists(file):
        return send_file(file, as_attachment=True)
    return jsonify({"message": "No attendance records found."})

# View Student List
@app.route("/view_students")
def view_students():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM attendance")
    students = cursor.fetchall()
    conn.close()
    return render_template("students.html", students=[s[0] for s in students])

# Web UI Route
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
