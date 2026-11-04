from datetime import datetime, date, time
from app import create_app
from app.extensions import db
from app.models.auth import Admin, Role, Permission
from app.models.settings import HospitalSetting
from app.models.department import Department
from app.services.data_generator import seed_departments, seed_doctors, seed_beds, seed_resources

app = create_app()

def seed_database():
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # 1. Initialize Hospital Settings
        setting = HospitalSetting.query.first()
        if not setting:
            setting = HospitalSetting(
                hospital_name="Apex Health & Analytics Center",
                logo_path="/static/img/logo.svg",
                phone="+1 (800) 555-0199",
                email="admin@apexhealth.org",
                address="742 Healthcare Boulevard, Medical District",
                bed_capacity_alert_threshold=85,
                waiting_time_alert_threshold=45,
                currency="$",
                consultation_fee=75.0,
                system_mode="Production"
            )
            db.session.add(setting)
            db.session.commit()
            print("Hospital operational settings initialized.")

        # 2. Initialize Permissions
        permissions_data = [
            ("manage_users", "Manage Administrators", "Create, edit, and deactivate administrative user accounts"),
            ("manage_patients", "Manage Patients", "Full access to register, modify, and archive patient profiles"),
            ("manage_doctors", "Manage Doctors", "Manage doctor profiles, schedules, and availability statuses"),
            ("manage_departments", "Manage Departments", "Create and maintain hospital departments"),
            ("manage_appointments", "Manage Appointments", "Schedule, reschedule, and manage appointment bookings"),
            ("manage_beds", "Manage Beds & Resources", "Allocate, maintain, and manage hospital beds and equipment"),
            ("manage_admissions", "Manage Inpatient Flow", "Process inpatient admissions and patient discharges"),
            ("view_analytics", "View Analytics", "Access statistical dashboards and patient flow data"),
            ("manage_ml", "Manage ML Models", "Access machine learning predictions and model retraining pipelines"),
            ("manage_datasets", "Manage Datasets", "Upload CSV data and generate demonstration benchmarks"),
            ("export_reports", "Export Reports", "Generate and download CSV, Excel, and PDF reports"),
            ("system_settings", "System Settings", "Configure hospital parameters, database backups, and environment")
        ]

        created_perms = {}
        for code, name, desc in permissions_data:
            p = Permission.query.filter_by(code=code).first()
            if not p:
                p = Permission(code=code, name=name, description=desc)
                db.session.add(p)
            created_perms[code] = p
        db.session.commit()
        print(f"Verified {len(created_perms)} system permissions.")

        # 3. Initialize Roles
        roles_data = [
            ("Super Admin", "Complete omnipotent control over all modules, settings, users, and ML models."),
            ("Hospital Administrator", "Operational control over patients, doctors, appointments, beds, admissions, and reports."),
            ("Data Analyst", "Access to analytics, machine learning forecasts, reports, and dataset management.")
        ]

        created_roles = {}
        for r_name, r_desc in roles_data:
            role = Role.query.filter_by(name=r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc)
                db.session.add(role)
            created_roles[r_name] = role
        db.session.commit()

        # Bind permissions to roles
        # Super Admin gets all permissions
        super_admin_role = created_roles["Super Admin"]
        super_admin_role.permissions = list(created_perms.values())

        # Hospital Administrator gets operational permissions
        hosp_admin_role = created_roles["Hospital Administrator"]
        hosp_admin_role.permissions = [
            created_perms[c] for c in [
                "manage_patients", "manage_doctors", "manage_departments",
                "manage_appointments", "manage_beds", "manage_admissions",
                "view_analytics", "export_reports"
            ]
        ]

        # Data Analyst gets analytical permissions
        analyst_role = created_roles["Data Analyst"]
        analyst_role.permissions = [
            created_perms[c] for c in [
                "view_analytics", "manage_ml", "manage_datasets", "export_reports"
            ]
        ]
        db.session.commit()
        print("Role hierarchy and backend permissions established.")

        # 4. Create Initial Administrator Accounts
        admins_data = [
            ("Dr. Samantha Reed", "admin@apexhealth.org", "Admin@12345", "+1 (555) 019-2001", "Super Admin"),
            ("Marcus Sterling", "operations@apexhealth.org", "HospAdmin@12345", "+1 (555) 019-2002", "Hospital Administrator"),
            ("Elena Rostova", "analyst@apexhealth.org", "Analyst@12345", "+1 (555) 019-2003", "Data Analyst")
        ]

        for full_name, email, pwd, phone, r_name in admins_data:
            admin = Admin.query.filter_by(email=email).first()
            if not admin:
                admin = Admin(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    is_active=True
                )
                admin.set_password(pwd)
                admin.roles.append(created_roles[r_name])
                db.session.add(admin)
                print(f"Created admin account: {email} ({r_name}) / Password: {pwd}")
        db.session.commit()

        # 5. Seed Core Departments, Doctors, Beds, and Resources
        print("Seeding default 10 departments...")
        seed_departments()

        print("Seeding baseline doctor records...")
        seed_doctors(30)

        print("Seeding hospital beds...")
        seed_beds(200)

        print("Seeding hospital clinical resources...")
        seed_resources()

        print("\nDatabase initialization complete!")
        print("="*60)
        print("Super Admin Login: admin@apexhealth.org")
        print("Password:          Admin@12345")
        print("="*60)

if __name__ == '__main__':
    seed_database()
