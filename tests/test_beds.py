import pytest
from datetime import datetime, time
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.auth import Admin, Role
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.bed import Bed, Admission

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        role = Role(name='Super Admin', description='Full admin')
        admin = Admin(full_name='Admin User', email='admin@test.org', is_active=True)
        admin.set_password('Admin@123')
        admin.roles.append(role)
        db.session.add(admin)

        dept = Department(name='Cardiology', code='CARD', is_active=True)
        db.session.add(dept)
        db.session.flush()

        doc = Doctor(
            doctor_id='DOC-2001',
            name='Marcus Brody',
            qualification='MD',
            specialization='Cardiology',
            department_id=dept.id,
            phone='555-0199',
            email='brody@test.org',
            duty_start_time=time(8, 0),
            duty_end_time=time(16, 0),
            availability_status='Available',
            is_active=True
        )
        db.session.add(doc)

        pat = Patient(
            patient_id='PAT-TEST-001',
            full_name='Alice Wonderland',
            age=32,
            gender='Female',
            phone='555-4433',
            blood_group='A+',
            status='Outpatient'
        )
        db.session.add(pat)

        bed = Bed(
            bed_id='BED-ICU-001',
            bed_number='001',
            department_id=dept.id,
            ward='ICU Ward A',
            bed_type='ICU',
            occupancy_status='Available'
        )
        db.session.add(bed)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    client = app.test_client()
    client.post('/auth/login', data={'email': 'admin@test.org', 'password': 'Admin@123'}, follow_redirects=True)
    return client

def test_atomic_admission_and_discharge(client, app):
    # 1. Admit Patient to Bed
    response = client.post('/admissions/new', data={
        'patient_id': '1',
        'department_id': '1',
        'doctor_id': '1',
        'bed_id': '1',
        'admission_reason': 'Post-infarct observation',
        'diagnosis': 'Stable'
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        bed = Bed.query.get(1)
        pat = Patient.query.get(1)
        adm = Admission.query.get(1)

        assert bed.occupancy_status == 'Occupied'
        assert bed.current_patient_id == pat.id
        assert pat.status == 'Admitted'
        assert adm.status == 'Active'

    # 2. Prevent double allocation of same occupied bed
    response2 = client.post('/admissions/new', data={
        'patient_id': '1',
        'department_id': '1',
        'doctor_id': '1',
        'bed_id': '1',
        'admission_reason': 'Duplicate attempt'
    }, follow_redirects=True)

    assert b'already admitted' in response2.data or b'no longer available' in response2.data

    # 3. Discharge Patient
    response3 = client.post('/admissions/1/discharge', data={
        'discharge_condition': 'Recovered',
        'discharge_notes': 'Normal vitals'
    }, follow_redirects=True)

    assert response3.status_code == 200

    with app.app_context():
        bed = Bed.query.get(1)
        pat = Patient.query.get(1)
        adm = Admission.query.get(1)

        assert bed.occupancy_status == 'Available'
        assert bed.current_patient_id is None
        assert pat.status == 'Discharged'
        assert adm.status == 'Discharged'

