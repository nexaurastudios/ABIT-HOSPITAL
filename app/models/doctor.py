from datetime import datetime, time
from app.extensions import db

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(120), nullable=False)  # MBBS, MD, MS, etc.
    specialization = db.Column(db.String(120), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    experience_years = db.Column(db.Integer, default=1, nullable=False)
    duty_start_time = db.Column(db.Time, default=time(8, 0), nullable=False)
    duty_end_time = db.Column(db.Time, default=time(16, 0), nullable=False)
    availability_status = db.Column(db.String(30), default='Available', nullable=False)  # Available, Busy, On Leave, Not Available
    max_patient_capacity = db.Column(db.Integer, default=25, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    schedules = db.relationship('DoctorSchedule', backref='doctor', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    visits = db.relationship('Visit', backref='doctor', lazy=True)
    admissions = db.relationship('Admission', backref='doctor', lazy=True)

    def is_available_at(self, requested_time):
        """Check if requested_time is within doctor's duty hours and status is Available"""
        if self.availability_status != 'Available' or not self.is_active:
            return False, f"Doctor {self.name} is currently {self.availability_status}."
        if self.duty_start_time and self.duty_end_time:
            if not (self.duty_start_time <= requested_time <= self.duty_end_time):
                return False, f"Time {requested_time.strftime('%H:%M')} is outside duty hours ({self.duty_start_time.strftime('%H:%M')} - {self.duty_end_time.strftime('%H:%M')})."
        return True, "Available"

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'name': self.name,
            'qualification': self.qualification,
            'specialization': self.specialization,
            'department': self.department.name if self.department else 'N/A',
            'phone': self.phone,
            'email': self.email,
            'experience_years': self.experience_years,
            'duty_hours': f"{self.duty_start_time.strftime('%H:%M')} - {self.duty_end_time.strftime('%H:%M')}",
            'availability_status': self.availability_status,
            'max_patient_capacity': self.max_patient_capacity,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f"<Doctor {self.doctor_id} - Dr. {self.name}>"


class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedules'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration_minutes = db.Column(db.Integer, default=20, nullable=False)
    max_slots = db.Column(db.Integer, default=20, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DoctorSchedule Doc {self.doctor_id} on {self.day_of_week}>"
