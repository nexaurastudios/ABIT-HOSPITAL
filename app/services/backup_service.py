import os
import json
from datetime import datetime
from app.extensions import db
from app.models.department import Department
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed, Admission
from app.models.resource import Resource
from app.models.settings import HospitalSetting
from app.services.activity_logger import log_activity

BACKUP_DIR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

def generate_database_backup():
    """Serialize entire database state into a structured JSON backup archive"""
    backup_data = {
        'metadata': {
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'system': 'Hospital Resource Optimization and Patient Analytics'
        },
        'departments': [d.to_dict() for d in Department.query.all()],
        'doctors': [doc.to_dict() for doc in Doctor.query.all()],
        'beds': [b.to_dict() for b in Bed.query.all()],
        'patients_count': Patient.query.count(),
        'appointments_count': Appointment.query.count(),
        'admissions_count': Admission.query.count(),
    }

    filename = f"backup_hospital_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(BACKUP_DIR, filename)

    with open(filepath, 'w') as f:
        json.dump(backup_data, f, indent=2)

    log_activity("DATABASE_BACKUP", "Settings", f"Created database backup: {filename}")
    return filepath, filename

def clear_demo_data():
    """Safely clear only DEMO DATA records, leaving primary user and configuration intact"""
    try:
        # 1. Clear admissions marked is_demo
        demo_admissions = Admission.query.filter_by(is_demo=True).all()
        for a in demo_admissions:
            db.session.delete(a)

        # 2. Reset occupied beds that were demo
        Bed.query.filter_by(is_demo=True).update({
            'occupancy_status': 'Available',
            'current_patient_id': None,
            'current_admission_id': None
        })

        # 3. Clear visits marked is_demo
        Visit.query.filter_by(is_demo=True).delete()

        # 4. Clear appointments marked is_demo
        Appointment.query.filter_by(is_demo=True).delete()

        # 5. Clear demo patients
        Patient.query.filter_by(is_demo=True).delete()

        # 6. Clear demo doctors
        Doctor.query.filter_by(is_demo=True).delete()

        db.session.commit()
        log_activity("CLEAR_DEMO_DATA", "Settings", "Cleared all demo data records successfully")
        return True, "Demo data successfully cleared."
    except Exception as e:
        db.session.rollback()
        return False, str(e)
