import pytest
from datetime import datetime, timedelta, date
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.visit import Visit

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_waiting_time_and_duration_calculation(app):
    with app.app_context():
        now = datetime.utcnow()
        arr = now - timedelta(minutes=45)
        start = now - timedelta(minutes=15)
        end = now

        # Complete visit
        v = Visit(
            visit_id='VIS-TEST-001',
            patient_id=1,
            doctor_id=1,
            department_id=1,
            visit_date=date.today(),
            arrival_time=arr,
            consultation_start_time=start,
            consultation_end_time=end,
            status='Completed'
        )
        v.calculate_metrics()
        db.session.add(v)
        db.session.commit()

        assert v.waiting_time_minutes == 30.0  # 45 - 15 = 30 minutes
        assert v.consultation_duration_minutes == 15.0  # 15 - 0 = 15 minutes
        assert v.is_complete_flow is True

def test_incomplete_visit_handles_none(app):
    with app.app_context():
        # Incomplete visit (arrival recorded, but consultation hasn't started yet)
        v = Visit(
            visit_id='VIS-TEST-002',
            patient_id=2,
            doctor_id=1,
            department_id=1,
            arrival_time=datetime.utcnow(),
            consultation_start_time=None,
            status='Waiting'
        )
        v.calculate_metrics()
        assert v.waiting_time_minutes is None
        assert v.consultation_duration_minutes is None
        assert v.is_complete_flow is False

