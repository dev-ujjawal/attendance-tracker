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
def mark_attendance(name, status):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    date = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO attendance (name, date, status) VALUES (?, ?, ?)", (name, date, status))
    conn.commit()
    conn.close()
    update_excel(name, date, status)
    send_email_notification(name, status)
    messagebox.showinfo("Success", "Attendance marked successfully!")

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
def generate_report(name):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM attendance WHERE name = ? GROUP BY status", (name,))
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        messagebox.showinfo("No Data", f"No attendance records found for {name}")
        return
    
    labels, sizes = zip(*data)
    plt.figure()
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['green', 'red', 'orange'])
    plt.title(f"Attendance Report for {name}")
    plt.axis("equal")
    plt.show()

# GUI Setup
def gui():
    root = tk.Tk()
    root.title("Attendance Tracker")
    root.geometry("400x350")
    
    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(pady=20)
    
    tk.Label(frame, text="Enter Name:").grid(row=0, column=0, padx=5, pady=5)
    name_entry = tk.Entry(frame)
    name_entry.grid(row=0, column=1, padx=5, pady=5)
    
    status_var = tk.StringVar()
    status_var.set("Present")
    status_dropdown = ttk.Combobox(frame, textvariable=status_var, values=["Present", "Absent", "Late"])
    status_dropdown.grid(row=1, column=1, padx=5, pady=5)
    
    def mark():
        mark_attendance(name_entry.get(), status_var.get())
    
    tk.Button(frame, text="Mark Attendance", command=mark).grid(row=2, column=0, columnspan=2, pady=10)
    
    tk.Label(frame, text="Select Name for Report:").grid(row=3, column=0, padx=5, pady=5)
    report_name_entry = tk.Entry(frame)
    report_name_entry.grid(row=3, column=1, padx=5, pady=5)
    
    def generate():
        generate_report(report_name_entry.get())
    
    tk.Button(frame, text="Generate Report", command=generate).grid(row=4, column=0, columnspan=2, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    init_db()
    gui()
