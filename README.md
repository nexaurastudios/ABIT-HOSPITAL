# Hospital Resource Optimization and Patient Analytics System (AI/ML Integrated)

A complete, fully functional, enterprise-grade web application for hospital resource planning, inpatient bed management, outpatient flow optimization, and machine learning prediction of patient volumes and queue waiting times.

Developed with **Python, Flask, MySQL, SQLAlchemy, Pandas, NumPy, Scikit-learn, Bootstrap 5, and Chart.js**.

---

## 🏥 Project Overview & Objectives

In modern healthcare delivery, misallocated bed capacities, clinician shortages, and bottlenecked patient queues lead to elevated waiting times, staff burnout, and suboptimal clinical outcomes. 

This academic Data Analytics & Artificial Intelligence project provides an end-to-end operational software suite that demonstrates how:
1. **Dynamic Relational Operations** (MySQL & SQLAlchemy) maintain transactional integrity for hospital bed assignments, preventing duplicate allocations and tracking admissions.
2. **Patient Flow Analytics** (Pandas & NumPy) calculate empirical arrival-to-consultation waiting times and monitor department bottlenecks.
3. **Machine Learning Algorithms** (Random Forest, Gradient Boosting, Linear Regression) accurately forecast upcoming patient inflow and predict waiting times for newly arriving outpatients.
4. **Role-Based Access Control** (Super Admin, Hospital Administrator, Data Analyst) enforces server-side security boundaries.
5. **Automated Multi-Format Reporting** generates publication-quality CSV, Excel (.xlsx), and PDF reports on demand.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.10+, Flask 3.x, Flask-Login, Flask-WTF (CSRF Protection), Flask-Migrate, Werkzeug Security |
| **Database & ORM** | MySQL 8.x/9.x, PyMySQL, SQLAlchemy 2.x (with connection pooling, pre-ping, atomic transactions) |
| **Data Analytics** | Pandas 2.x, NumPy 1.x/2.x |
| **Machine Learning** | Scikit-learn, Random Forest Regressor, Gradient Boosting Regressor, Linear Regression, Joblib |
| **Reporting & Export** | OpenPyXL (Excel), ReportLab (PDF), in-memory CSV Streaming |
| **Frontend UI/UX** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4, FullCalendar |

---

## 🏛️ Database Design & Relational Tables (19 Tables)

The database schema strictly adheres to third normal form (3NF) with foreign keys, cascading constraints, and uniqueness guarantees:

```
 hospital_analytics_db
 ├── 1. admins                  (Administrator user accounts, bcrypt hashed passwords, last login)
 ├── 2. roles                   (Super Admin, Hospital Administrator, Data Analyst)
 ├── 3. permissions             (Granular permission codes: manage_patients, manage_ml, etc.)
 ├── 4. admin_roles             (Many-to-Many association linking admins to roles)
 ├── 5. role_permissions        (Many-to-Many association linking roles to permissions)
 ├── 6. departments             (10 Clinical divisions: Cardiology, Neurology, Orthopaedics, etc.)
 ├── 7. doctors                 (Medical staff, qualification, specialization, duty hours, capacity)
 ├── 8. doctor_schedules        (Weekly recurring schedules, duty slots, shift durations)
 ├── 9. patients                (Demographics, blood group, emergency contact, admission status)
 ├── 10. appointments           (Consultation bookings, time slots, scheduling conflict checks)
 ├── 11. visits                 (Arrival, registration, consult start & end timestamps, waiting times)
 ├── 12. beds                   (Wards, bed types: General, ICU, Private, Semi-Private, Emergency)
 ├── 13. admissions             (Inpatient hospitalizations, reason, discharge condition, notes)
 ├── 14. resources              (Clinical equipment: ventilators, monitors, defibrillators, etc.)
 ├── 15. notifications          (High occupancy alerts, long queue alerts, unread counter)
 ├── 16. activity_logs          (Audit trail of all administrative actions, timestamps, and IP addresses)
 ├── 17. model_registry         (Serialized ML algorithms, versioning, MAE, RMSE, R² scores)
 ├── 18. prediction_logs        (Logged live inference inputs, outputs, and actual outcomes)
 └── 19. hospital_settings      (Operational thresholds, consultation fee, hospital branding)
```

---

## 🧠 Machine Learning Engines

### System A: Patient Demand Forecaster
- **Objective:** Predict future daily patient inflow across the hospital and individual departments for upcoming days.
- **Feature Engineering:**
  - Day of week (0 to 6)
  - Month and day of month
  - Weekend flag indicator
  - Lag-1 patient volume (yesterday's count)
  - Lag-2 patient volume
  - Lag-7 patient volume (same weekday previous week)
  - Rolling 7-day moving average
- **Algorithms Compared:**
  1. *Random Forest Regressor* (Selected Model)
  2. *Gradient Boosting Regressor*
  3. *Linear Regression*
- **Evaluation:** Evaluated on an 80/20 chronological train/test split using Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE).
- **Output:** 7-day day-by-day forecast with 95% confidence intervals and automated staffing recommendations.

### System B: Patient Waiting Time Predictor
- **Objective:** Provide newly arriving outpatients and reception staff with an immediate estimation of consultation waiting time in minutes.
- **Features:** Department ID, current department queue size (waiting patients), number of doctors on active duty, arrival hour, day of the week, historical average consultation duration.
- **Algorithms Compared:**
  1. *Gradient Boosting Regressor* (MAE ~6.1 mins, R² ~0.53)
  2. *Random Forest Regressor*
  3. *Linear Regression*
- **Operational Disclaimer:** Displayed prominently on all inference outputs:
  > *"These predictions are estimates for hospital operational planning and are not guaranteed waiting times or medical advice."*

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.14)
- **MySQL Server 8.0+ / 9.x** running locally on port 3306

### 2. Clone / Open Project
```bash
cd "/Users/asitkumarsahoo/Downloads/project abit "
```

### 3. Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (already configured with local defaults):
```bash
# MySQL Database Configuration
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
DB_NAME=hospital_analytics_db
DATABASE_URL=mysql+pymysql://root:@localhost:3306/hospital_analytics_db
```

Ensure MySQL has the database created:
```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS hospital_analytics_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 5. Seed the Database
Initialize tables, default permissions, administrator accounts, departments, and clinical resources:
```bash
python seed.py
```

### 6. Generate Demonstration Dataset
Generate ~5,000 synthetic patient records, ~1,000 appointments, ~200 beds, and historical visits with realistic timestamps:
```bash
python generate_demo_data.py
```

### 7. Train Machine Learning Models
Train all regression models, compare performance metrics, and serialize the best models with Joblib:
```bash
python train_ml.py
```

### 8. Start the Flask Application
```bash
python run.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5050`**

---

## 🔑 Pre-Configured Administrator Credentials

| Role | Email Address | Password | Permissions |
|---|---|---|---|
| **Super Admin** | `admin@apexhealth.org` | `Admin@12345` | Full control across all modules, settings, users, and backup tools |
| **Hospital Administrator** | `operations@apexhealth.org` | `HospAdmin@12345` | Operational control over patients, doctors, beds, appointments, admissions |
| **Data Analyst** | `analyst@apexhealth.org` | `Analyst@12345` | Analytics dashboards, ML inference, reports generation, and dataset management |

*(Convenient one-click credential buttons are available directly on the login screen for seamless demonstration).*

---

## 🧪 Automated Testing Suite

The application includes a comprehensive test suite covering all operational modules:
```bash
PYTHONPATH=. ./venv/bin/pytest -v
```

Tests verify:
- **Authentication:** Valid logins, invalid credentials, deactivated account blocks, password hashing.
- **Patient Management:** Registration, profile history, status updates.
- **Bed Allocation:** Atomic row locking, double allocation prevention, discharge release.
- **Waiting Time Flow:** Timestamp difference arithmetic, duration calculation, handling of incomplete records.
- **Machine Learning:** 7-day multi-step demand forecasting, live waiting time inference.
- **Report Exporters:** Byte stream generation for CSV, Excel (.xlsx), and ReportLab PDF formats.

---

## 🎓 College Project Presentation Walkthrough

When presenting this project for an academic defense or viva, follow this recommended walkthrough:

1. **Administrator Login & Role Security (`/auth/login`)**:
   - Demonstrate role-based access. Log in as Super Admin (`admin@apexhealth.org`).
   - Highlight Werkzeug password hashing and session management.

2. **Main Dashboard (`/`)**:
   - Point out the 12 dynamic KPI cards (Total Patients, Doctors, Available Beds, Bed Occupancy %, Avg Waiting Time).
   - Change the department filter dropdown to show dynamic Chart.js chart updates without page reload.

3. **Inpatient Bed Flow & Atomic Transactions (`/beds` & `/admissions`)**:
   - Show how a bed's status changes from `Available` to `Occupied` when a patient is admitted.
   - Show that the bed cannot be double-assigned.
   - Process a discharge: demonstrate how the bed automatically becomes `Available` again and the patient status updates to `Discharged`.

4. **Patient Waiting Time Analysis (`/waiting-time`)**:
   - Explain the 4 timestamp checkpoints: Arrival $\to$ Registration $\to$ Consultation Start $\to$ Consultation End.
   - Show how waiting time is calculated ($T_{\text{start}} - T_{\text{arrival}}$).
   - Display departments that trigger the $> 45\text{ min}$ threshold warning. Show that incomplete records are isolated and never corrupt averages.

5. **Machine Learning Predictions (`/ml`)**:
   - **System A:** Show the 7-day patient demand forecast table with upper/lower bounds.
   - Show the algorithm comparison table (Random Forest vs Gradient Boosting vs Linear Regression).
   - **System B:** Enter live queue parameters (e.g. 8 patients waiting, 2 doctors available) and click **Run Waiting Time Inference**. Show the predicted waiting time output and point out the academic operational disclaimer.
   - Click the **Retrain ML Models** button to show that the system retrains algorithms on real database data and registers new metrics in `model_registry`.

6. **Dataset & Report Exports (`/datasets` & `/reports`)**:
   - Download sample CSV templates.
   - Generate and download a PDF, Excel (.xlsx), and CSV report with the click of a button.
   - Point out the clean ReportLab formatting and hospital header.

---

## 📄 License
Academic Project &copy; 2026. Designed and developed for demonstration and study of Applied Artificial Intelligence and Healthcare Resource Analytics.

