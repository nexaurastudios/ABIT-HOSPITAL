#!/usr/bin/env python3
"""
Generate high-resolution System Flowchart & Architecture Diagram for
Hospital Resource Optimization and Patient Analytics System.
Uses Pillow to create a publication-ready graphic without external font cache dependencies.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_flowchart():
    # Dimensions: 2200 x 2900 px (Ultra-high resolution, crisp on 4K/Retina displays)
    width = 2200
    height = 2900
    
    # Base canvas
    img = Image.new('RGBA', (width, height), color=(248, 250, 252, 255)) # Slate 50 background
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        
    title_font = ImageFont.truetype(font_path, 42, index=1 if "Helvetica" in font_path else 0)
    subtitle_font = ImageFont.truetype(font_path, 22, index=0)
    section_font = ImageFont.truetype(font_path, 24, index=1 if "Helvetica" in font_path else 0)
    card_title_font = ImageFont.truetype(font_path, 20, index=1 if "Helvetica" in font_path else 0)
    body_font = ImageFont.truetype(font_path, 15, index=0)
    bold_body_font = ImageFont.truetype(font_path, 15, index=1 if "Helvetica" in font_path else 0)
    badge_font = ImageFont.truetype(font_path, 13, index=1 if "Helvetica" in font_path else 0)
    arrow_font = ImageFont.truetype(font_path, 14, index=1 if "Helvetica" in font_path else 0)
    
    # Helper to draw rounded rectangle with optional fill and outline
    def draw_rounded_card(xy, fill, outline, radius=12, width_outline=2):
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width_outline)

    # Helper to draw badges
    def draw_badge(x, y, text, bg_color, text_color):
        bbox = badge_font.getbbox(text)
        bw = (bbox[2] - bbox[0]) + 16
        bh = (bbox[3] - bbox[1]) + 8
        draw.rounded_rectangle([x, y, x + bw, y + bh], radius=4, fill=bg_color)
        draw.text((x + 8, y + 3), text, font=badge_font, fill=text_color)
        return bw

    # Helper to draw arrows
    def draw_down_arrow(x, y1, y2, label="", color=(2, 132, 199, 255)): # Sky 600
        draw.line([(x, y1), (x, y2)], fill=color, width=4)
        # Arrowhead
        draw.polygon([(x - 9, y2 - 14), (x + 9, y2 - 14), (x, y2 + 2)], fill=color)
        if label:
            tbox = arrow_font.getbbox(label)
            tw = tbox[2] - tbox[0] + 16
            th = tbox[3] - tbox[1] + 8
            mid_y = (y1 + y2) // 2
            draw.rounded_rectangle([x - tw//2, mid_y - th//2, x + tw//2, mid_y + th//2], radius=4, fill=(255, 255, 255, 230), outline=(203, 213, 225, 255))
            draw.text((x - tw//2 + 8, mid_y - th//2 + 3), label, font=arrow_font, fill=color)

    def draw_right_arrow(x1, x2, y, label="", color=(2, 132, 199, 255)):
        draw.line([(x1, y), (x2, y)], fill=color, width=4)
        draw.polygon([(x2 - 14, y - 9), (x2 - 14, y + 9), (x2 + 2, y)], fill=color)
        if label:
            tbox = arrow_font.getbbox(label)
            tw = tbox[2] - tbox[0] + 16
            th = tbox[3] - tbox[1] + 8
            mid_x = (x1 + x2) // 2
            draw.rounded_rectangle([mid_x - tw//2, y - th//2, mid_x + tw//2, y + th//2], radius=4, fill=(255, 255, 255, 230), outline=(203, 213, 225, 255))
            draw.text((mid_x - tw//2 + 8, y - th//2 + 3), label, font=arrow_font, fill=color)

    # -------------------------------------------------------------
    # 0. HEADER BANNER
    # -------------------------------------------------------------
    draw.rounded_rectangle([60, 40, 2140, 160], radius=16, fill=(15, 23, 42, 255)) # Dark Slate
    # Accent top border
    draw.rounded_rectangle([60, 40, 2140, 48], radius=4, fill=(14, 165, 233, 255)) # Sky Blue Accent
    
    draw.text((100, 65), "HOSPITAL RESOURCE OPTIMIZATION & PATIENT ANALYTICS", font=title_font, fill=(255, 255, 255, 255))
    draw.text((100, 118), "Complete End-to-End System Architecture, Operational Patient Journey & AI / Machine Learning Engine", font=subtitle_font, fill=(148, 163, 184, 255))
    
    # Status pills on right
    draw_badge(1850, 85, "FLASK 3.1", (30, 41, 59, 255), (56, 189, 248, 255))
    draw_badge(1955, 85, "MYSQL 9.6", (30, 41, 59, 255), (74, 222, 128, 255))
    draw_badge(2055, 85, "SCIKIT-LEARN", (30, 41, 59, 255), (250, 204, 21, 255))

    # -------------------------------------------------------------
    # 1. LAYER 1: USER ROLES & ACCESS CONTROL (Y: 200 - 450)
    # -------------------------------------------------------------
    draw_rounded_card([60, 190, 2140, 440], fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), radius=16)
    draw.text((90, 210), "LAYER 1: USER ROLES, AUTHENTICATION & ACCESS CONTROL", font=section_font, fill=(30, 41, 59, 255))
    
    roles = [
        {
            "title": "Super Administrator",
            "subtitle": "Complete System Governance",
            "items": ["• Full CRUD across all 19 DB tables", "• Role & permission assignment", "• DB backup & dataset restoration", "• ML model retraining trigger"],
            "box": [90, 255, 560, 415],
            "accent": (59, 130, 246, 255), # Blue
            "bg": (239, 246, 255, 255)
        },
        {
            "title": "Hospital Administrator",
            "subtitle": "Clinical & Resource Operations",
            "items": ["• Bed management & ward allocation", "• Doctor shift & capacity planning", "• Patient admissions & discharges", "• Department workload tracking"],
            "box": [590, 255, 1060, 415],
            "accent": (16, 185, 129, 255), # Emerald
            "bg": (240, 253, 244, 255)
        },
        {
            "title": "Data Analyst",
            "subtitle": "AI Analytics & Performance",
            "items": ["• Dedicated Analyst Command Panel", "• Waiting time anomaly heatmaps", "• Resource occupancy forecasting", "• Export reports (CSV / XLSX / PDF)"],
            "box": [1090, 255, 1560, 415],
            "accent": (234, 179, 8, 255), # Amber
            "bg": (254, 252, 232, 255)
        },
        {
            "title": "Clinical Reception & Triage",
            "subtitle": "Frontline Patient Handling",
            "items": ["• Register outpatient / inpatient", "• Book appointments & time slots", "• Capture arrival & registration times", "• View queue status & doctor roster"],
            "box": [1590, 255, 2110, 415],
            "accent": (236, 72, 153, 255), # Pink
            "bg": (253, 242, 248, 255)
        }
    ]

    for r in roles:
        draw_rounded_card(r["box"], fill=r["bg"], outline=r["accent"], radius=10, width_outline=2)
        draw.text((r["box"][0] + 15, r["box"][1] + 12), r["title"], font=card_title_font, fill=(15, 23, 42, 255))
        draw.text((r["box"][0] + 15, r["box"][1] + 36), r["subtitle"], font=badge_font, fill=r["accent"])
        y_text = r["box"][1] + 62
        for itm in r["items"]:
            draw.text((r["box"][0] + 15, y_text), itm, font=body_font, fill=(51, 65, 85, 255))
            y_text += 22

    # Down arrows from Layer 1 to Layer 2
    draw_down_arrow(325, 440, 490)
    draw_down_arrow(825, 440, 490)
    draw_down_arrow(1325, 440, 490)
    draw_down_arrow(1850, 440, 490, label="Role-Based Protected Routing (Flask-Login + WTForms CSRF)")

    # -------------------------------------------------------------
    # 2. LAYER 2: PATIENT LIFECYCLE & WORKFLOW (Y: 490 - 920)
    # -------------------------------------------------------------
    draw_rounded_card([60, 490, 2140, 920], fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), radius=16)
    draw.text((90, 510), "LAYER 2: PATIENT LIFECYCLE & CLINICAL OPERATIONAL WORKFLOW", font=section_font, fill=(30, 41, 59, 255))

    steps = [
        {
            "step": "STEP 1",
            "title": "Patient Registration",
            "subtitle": "Demographics & Triage",
            "items": ["• Auto-gen ID: PAT-XXXXXX", "• Demographics, Age, Gender", "• Blood Group & Contact", "• Logs Initial Arrival Timestamp"],
            "box": [90, 560, 450, 780],
            "accent": (2, 132, 199, 255),
            "bg": (240, 249, 255, 255)
        },
        {
            "step": "STEP 2",
            "title": "Appointment Booking",
            "subtitle": "Scheduling & Conflict Check",
            "items": ["• Select Department & Doctor", "• Validate Doctor Duty Hours", "• Enforce Daily Patient Quota", "• Check for Double Booking"],
            "box": [500, 560, 860, 780],
            "accent": (79, 70, 229, 255),
            "bg": (238, 242, 255, 255)
        },
        {
            "step": "STEP 3",
            "title": "Consultation & Queue",
            "subtitle": "Waiting Time Tracking",
            "items": ["• Queue Waiting Timestamp", "• Doctor Consultation Start", "• Doctor Consultation End", "• Exact Wait & Duration Computed"],
            "box": [910, 560, 1280, 780],
            "accent": (13, 148, 136, 255),
            "bg": (240, 253, 250, 255)
        },
        {
            "step": "STEP 4",
            "title": "Admission & Bed Allocation",
            "subtitle": "Inpatient Resource Control",
            "items": ["• Check ICU / General / Ward", "• Atomic DB Lock (Single Occupant)", "• Auto Bed Status: Occupied", "• Record Clinical Diagnosis"],
            "box": [1330, 560, 1700, 780],
            "accent": (217, 119, 6, 255),
            "bg": (255, 251, 235, 255)
        },
        {
            "step": "STEP 5",
            "title": "Discharge & Release",
            "subtitle": "Bed Sanitization & Analytics",
            "items": ["• Record Discharge Timestamp", "• Bed Released -> Maintenance", "• Bed Automatically Available", "• Historical Analytics Preserved"],
            "box": [1750, 560, 2110, 780],
            "accent": (22, 163, 74, 255),
            "bg": (240, 253, 244, 255)
        }
    ]

    for s in steps:
        draw_rounded_card(s["box"], fill=s["bg"], outline=s["accent"], radius=10, width_outline=2)
        draw_badge(s["box"][0] + 15, s["box"][1] + 12, s["step"], s["accent"], (255, 255, 255, 255))
        draw.text((s["box"][0] + 15, s["box"][1] + 36), s["title"], font=card_title_font, fill=(15, 23, 42, 255))
        draw.text((s["box"][0] + 15, s["box"][1] + 62), s["subtitle"], font=badge_font, fill=s["accent"])
        y_text = s["box"][1] + 88
        for itm in s["items"]:
            draw.text((s["box"][0] + 15, y_text), itm, font=body_font, fill=(51, 65, 85, 255))
            y_text += 22

    # Step Horizontal Arrows
    draw_right_arrow(450, 500, 670)
    draw_right_arrow(860, 910, 670)
    draw_right_arrow(1280, 1330, 670)
    draw_right_arrow(1700, 1750, 670)

    # Workflow summary banner inside Layer 2
    draw_rounded_card([90, 810, 2110, 895], fill=(241, 245, 249, 255), outline=(203, 213, 225, 255), radius=8)
    draw.text((115, 825), "OPERATIONAL TIMESTAMP INTEGRITY AUDIT:", font=bold_body_font, fill=(30, 41, 59, 255))
    draw.text((115, 850), "Waiting Time = (Consultation Start - Patient Arrival Time) | Consultation Duration = (Consultation End - Consultation Start)", font=body_font, fill=(71, 85, 105, 255))
    draw.text((115, 870), "Strict Validation: Incomplete/null timestamps are isolated into separate quarantine views to avoid corrupting hospital mean KPI statistics.", font=body_font, fill=(100, 116, 139, 255))

    # Down arrow to Layer 3
    draw_down_arrow(1100, 920, 970, label="Real-Time Transactional Persistence & Data Streaming")

    # -------------------------------------------------------------
    # 3. LAYER 3: FLASK APP CONTROLLER & MYSQL DATABASE (Y: 970 - 1530)
    # -------------------------------------------------------------
    draw_rounded_card([60, 970, 2140, 1530], fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), radius=16)
    draw.text((90, 990), "LAYER 3: MODULAR FLASK BACKEND ARCHITECTURE & RELATIONAL DATABASE", font=section_font, fill=(30, 41, 59, 255))

    # Flask Blueprints Box (Left)
    draw_rounded_card([90, 1030, 1080, 1500], fill=(248, 250, 252, 255), outline=(148, 163, 184, 255), radius=12)
    draw.text((115, 1050), "Flask Application Server (Modular Blueprints)", font=card_title_font, fill=(15, 23, 42, 255))
    draw_badge(580, 1050, "PYTHON 3.14 + WERKZEUG", (224, 242, 254, 255), (2, 132, 199, 255))

    bp_items = [
        ("auth_bp", "User Login, Session Auth, Password Hash, Role Permissions"),
        ("dashboard_bp", "12 Real-Time KPI Cards, Quick Actions, Live Alerts"),
        ("patients_bp", "Patient Master Register, Medical History, Search/Filters"),
        ("doctors_bp", "Specialist Directory, Shift Schedules, Workload Capacity"),
        ("departments_bp", "10 Specialty Departments, Resource Quotas, Lead Staff"),
        ("appointments_bp", "Calendar Scheduling, Daily/Weekly Views, Conflict Engine"),
        ("waiting_time_bp", "Queue Analytics, Waiting Time Heatmaps, Bottlenecks"),
        ("beds_bp", "ICU, Emergency, Ward Bed Inventory & Live Status Grid"),
        ("admissions_bp", "Inpatient Check-In, Discharge Processing, Bed Locks"),
        ("analytics_bp", "Data Analyst Panel, Statistical Aggregations (Pandas)"),
        ("ml_bp", "Model Inference Interface, Retraining Triggers, Metric Logs"),
        ("reports_bp", "CSV, Excel (.xlsx OpenPyXL), PDF (ReportLab) Exporters")
    ]
    
    y_bp = 1090
    for name, desc in bp_items:
        draw_badge(115, y_bp, name, (241, 245, 249, 255), (30, 41, 59, 255))
        draw.text((250, y_bp + 2), desc, font=body_font, fill=(71, 85, 105, 255))
        y_bp += 33

    # MySQL Database Box (Right)
    draw_rounded_card([1120, 1030, 2110, 1500], fill=(240, 253, 244, 255), outline=(34, 197, 94, 255), radius=12)
    draw.text((1145, 1050), "MySQL Relational Schema (19 Normalized Tables)", font=card_title_font, fill=(15, 23, 42, 255))
    draw_badge(1650, 1050, "hospital_analytics_db (InnoDB / Foreign Keys / ACID)", (220, 252, 231, 255), (21, 128, 61, 255))

    tables = [
        ("admins & roles", "RBAC security, hashed credentials, permissions"),
        ("patients", "Demographics, contact info, blood group, triage tags"),
        ("doctors & schedules", "Specialization, duty start/end, max patient capacity"),
        ("departments", "10 Specialty units, target wait times, bed quotas"),
        ("appointments", "Scheduled visits, status tracking, assigned doctors"),
        ("visits", "Timestamped clinical encounters (Arrival, Reg, Consult)"),
        ("beds", "ICU, General, Private, Emergency, Semi-Private slots"),
        ("admissions", "Inpatient records, admission reason, bed occupancy history"),
        ("resources", "Critical medical equipment, diagnostic assets & state"),
        ("model_registry", "Trained ML models, algorithms, R2, RMSE, hyperparameters"),
        ("prediction_logs", "Input feature logs & ML inference tracking for auditing"),
        ("activity_logs & notes", "System-wide audit trail, alerts, and operational events")
    ]

    y_tbl = 1090
    for t_name, t_desc in tables:
        draw_badge(1145, y_tbl, t_name, (255, 255, 255, 255), (22, 101, 52, 255))
        draw.text((1350, y_tbl + 2), t_desc, font=body_font, fill=(51, 65, 85, 255))
        y_tbl += 33

    # Bidirectional arrows between Flask & MySQL
    draw_right_arrow(1080, 1120, 1260, label="SQLAlchemy ORM")

    # Down arrow to Layer 4
    draw_down_arrow(1100, 1530, 1580, label="Feature Extraction & Historical Training Data")

    # -------------------------------------------------------------
    # 4. LAYER 4: AI & MACHINE LEARNING PIPELINE (Y: 1580 - 2190)
    # -------------------------------------------------------------
    draw_rounded_card([60, 1580, 2140, 2190], fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), radius=16)
    draw.text((90, 1600), "LAYER 4: MACHINE LEARNING & PREDICTIVE ANALYTICS ENGINE", font=section_font, fill=(30, 41, 59, 255))

    # Pipeline 1: Patient Demand Forecaster (Left Column)
    draw_rounded_card([90, 1640, 1080, 2160], fill=(254, 252, 232, 255), outline=(234, 179, 8, 255), radius=12)
    draw.text((115, 1660), "PIPELINE A: Patient Demand & Admission Forecaster", font=card_title_font, fill=(133, 77, 14, 255))
    draw_badge(750, 1660, "TIME-SERIES ML REGRESSION", (254, 240, 138, 255), (113, 63, 18, 255))

    p1_steps = [
        ("1. Data Aggregation", "Extract daily visit counts grouped by department from visits & admissions tables"),
        ("2. Feature Engineering", "Lag_1, Lag_2, Lag_7 (weekly seasonality), Rolling 7-day mean, Day of Week, Month"),
        ("3. Model Benchmarking", "Compares 3 Regression Algorithms on Chronological Train/Test Split:\n  • Random Forest Regressor (Ensemble of Decision Trees)\n  • Gradient Boosting Regressor (Sequential Loss Minimization)\n  • Linear Regression (Baseline Benchmark)"),
        ("4. Metric Evaluation", "Evaluates Root Mean Squared Error (RMSE), MAE, and R² Score.\nAutomatically selects champion model based on lowest test RMSE"),
        ("5. Model Serialization", "Champion model serialized via Joblib -> demand_model.joblib\nHyperparameters & metadata persisted to model_registry table"),
        ("6. Forecasting Output", "Generates 7-Day Forward Admission Volume with 95% Confidence Intervals\nUsed by Hospital Admins for dynamic bed & staffing capacity planning")
    ]

    y_p1 = 1700
    for st_title, st_desc in p1_steps:
        draw.text((115, y_p1), st_title, font=bold_body_font, fill=(113, 63, 18, 255))
        y_p1 += 20
        for line in st_desc.split("\n"):
            draw.text((130, y_p1), line, font=body_font, fill=(68, 64, 60, 255))
            y_p1 += 18
        y_p1 += 12

    # Pipeline 2: Waiting Time Predictor (Right Column)
    draw_rounded_card([1120, 1640, 2110, 2160], fill=(240, 253, 250, 255), outline=(13, 148, 136, 255), radius=12)
    draw.text((1145, 1660), "PIPELINE B: Real-Time Patient Waiting Time Predictor", font=card_title_font, fill=(17, 94, 89, 255))
    draw_badge(1780, 1660, "SUPERVISED QUEUE ML", (204, 251, 241, 255), (19, 78, 74, 255))

    p2_steps = [
        ("1. Clinical Queue Features", "Arrival Hour, Day of Week, Department ID (One-Hot Encoded),\nCurrent Department Queue Size, Available Doctors on Active Shift"),
        ("2. Data Sanitization", "Filters out incomplete records with missing consultation timestamps\nEliminates negative or anomalous waiting durations prior to model training"),
        ("3. Model Benchmarking", "Trains and compares:\n  • Gradient Boosting Regressor (Champion Model: MAE ~6.1 mins)\n  • Random Forest Regressor\n  • Linear Regression"),
        ("4. Real-Time Inference", "Triggered upon patient registration or triage check-in.\nInstant prediction of estimated minutes before doctor consultation begins"),
        ("5. Anomaly Detection", "Flags bottleneck departments where average waiting time exceeds 45 mins\nDispatches real-time alerts to the administrative dashboard notification center"),
        ("6. Model Registry & Audit", "Serialized to waiting_time_model.joblib. Every live prediction is logged to\nprediction_logs table with input features for drift & audit analysis")
    ]

    y_p2 = 1700
    for st_title, st_desc in p2_steps:
        draw.text((1145, y_p2), st_title, font=bold_body_font, fill=(17, 94, 89, 255))
        y_p2 += 20
        for line in st_desc.split("\n"):
            draw.text((1160, y_p2), line, font=body_font, fill=(51, 65, 85, 255))
            y_p2 += 18
        y_p2 += 12

    # Down arrow to Layer 5
    draw_down_arrow(600, 2190, 2240)
    draw_down_arrow(1600, 2190, 2240, label="Dynamic KPI Aggregates & Model Inference Results")

    # -------------------------------------------------------------
    # 5. LAYER 5: PRESENTATION, ANALYTICS & EXPORTS (Y: 2240 - 2780)
    # -------------------------------------------------------------
    draw_rounded_card([60, 2240, 2140, 2780], fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), radius=16)
    draw.text((90, 2260), "LAYER 5: PRESENTATION, VISUALIZATION & REPORTING INTERFACE", font=section_font, fill=(30, 41, 59, 255))

    dashboards = [
        {
            "title": "Main Admin Dashboard",
            "tag": "12 Dynamic KPI Cards",
            "desc": "Real-time hospital vital statistics dynamically computed directly from MySQL database",
            "items": [
                "• Total Patients, Doctors, Bed Occupancy %",
                "• Daily / Monthly Patient Registration Trends",
                "• Department-wise Patient Distribution (Chart.js)",
                "• Real-Time Hospital Activity Notification Stream"
            ],
            "box": [90, 2300, 730, 2740],
            "accent": (59, 130, 246, 255),
            "bg": (239, 246, 255, 255)
        },
        {
            "title": "Data Analyst Command Panel",
            "tag": "Statistical Intelligence",
            "desc": "In-depth clinical & operational analytics built with Pandas & NumPy data pipelines",
            "items": [
                "• Hourly Waiting Time Bottleneck Heatmaps",
                "• Doctor Workload & Consult Duration Analysis",
                "• Inpatient Length of Stay & Ward Utilization",
                "• 1-Click Interactive ML Model Retraining Trigger"
            ],
            "box": [760, 2300, 1440, 2740],
            "accent": (13, 148, 136, 255),
            "bg": (240, 253, 250, 255)
        },
        {
            "title": "Multi-Format Export Engine",
            "tag": "Audit & Compliance",
            "desc": "Production-grade report generation across 3 standard business document formats",
            "items": [
                "• CSV Export: Streaming UTF-8 clinical datasets",
                "• Excel (.xlsx): Styled spreadsheets with OpenPyXL",
                "• PDF Reports: ReportLab executive hospital summary",
                "• Historical Dataset Backup & Restore Manager"
            ],
            "box": [1470, 2300, 2110, 2740],
            "accent": (99, 102, 241, 255),
            "bg": (238, 242, 255, 255)
        }
    ]

    for d in dashboards:
        draw_rounded_card(d["box"], fill=d["bg"], outline=d["accent"], radius=10, width_outline=2)
        draw.text((d["box"][0] + 15, d["box"][1] + 15), d["title"], font=card_title_font, fill=(15, 23, 42, 255))
        draw_badge(d["box"][0] + 15, d["box"][1] + 45, d["tag"], d["accent"], (255, 255, 255, 255))
        draw.text((d["box"][0] + 15, d["box"][1] + 75), d["desc"], font=body_font, fill=(71, 85, 105, 255))
        y_d = d["box"][1] + 115
        for itm in d["items"]:
            draw.text((d["box"][0] + 15, y_d), itm, font=bold_body_font, fill=(30, 41, 59, 255))
            y_d += 26

    # -------------------------------------------------------------
    # 6. FOOTER
    # -------------------------------------------------------------
    draw.text((100, 2810), "Hospital Resource Optimization & Patient Analytics System | Academic AI/Data Analytics Project | Full-Stack Production Implementation", font=body_font, fill=(100, 116, 139, 255))
    draw.text((1800, 2810), "Rendered at 2200x2900 px (Ultra-HD)", font=badge_font, fill=(148, 163, 184, 255))

    # Destinations
    destinations = [
        "/Users/asitkumarsahoo/Downloads/project abit /system_flowchart.png",
        "/Users/asitkumarsahoo/Downloads/project abit /app/static/img/system_flowchart.png",
        "/Users/asitkumarsahoo/.gemini/antigravity/brain/597cede5-45e4-43b0-90d1-f40b12bb44d6/system_flowchart.png"
    ]

    for dest in destinations:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        img.save(dest, format='PNG', optimize=True)
        print(f"Saved: {dest}")

if __name__ == "__main__":
    create_flowchart()
