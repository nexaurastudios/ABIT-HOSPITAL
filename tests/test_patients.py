import pytest
from datetime import date
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.auth import Admin, Role
from app.models.patient import Patient
from app.models.department import Department

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
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    client = app.test_client()
    client.post('/auth/login', data={'email': 'admin@test.org', 'password': 'Admin@123'}, follow_redirects=True)
    return client

def test_create_and_view_patient(client, app):
    response = client.post('/patients/new', data={
        'full_name': 'Robert Taylor',
        'age': '48',
        'dob': '1978-05-12',
        'gender': 'Male',
        'phone': '+1 555-8899',
        'email': 'robert.taylor@test.org',
        'address': '124 Healthcare Way',
        'blood_group': 'O+',
        'assigned_department_id': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Robert Taylor' in response.data

    with app.app_context():
        patient = Patient.query.filter_by(full_name='Robert Taylor').first()
        assert patient is not None
        assert patient.blood_group == 'O+'
        assert patient.status == 'Outpatient'

