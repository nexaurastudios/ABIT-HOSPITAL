import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.auth import Admin, Role, Permission

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Create Super Admin role and admin
        role = Role(name='Super Admin', description='Full admin access')
        db.session.add(role)

        admin = Admin(full_name='Test Admin', email='test@hospital.org', is_active=True)
        admin.set_password('Secret@123')
        admin.roles.append(role)
        db.session.add(admin)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_success(client):
    response = client.post('/auth/login', data={
        'email': 'test@hospital.org',
        'password': 'Secret@123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back' in response.data or b'Dashboard' in response.data

def test_login_invalid_password(client):
    response = client.post('/auth/login', data={
        'email': 'test@hospital.org',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    assert b'Invalid email or password' in response.data

def test_login_deactivated_account(client, app):
    with app.app_context():
        admin = Admin.query.filter_by(email='test@hospital.org').first()
        admin.is_active = False
        db.session.commit()

    response = client.post('/auth/login', data={
        'email': 'test@hospital.org',
        'password': 'Secret@123'
    }, follow_redirects=True)
    assert b'deactivated' in response.data

