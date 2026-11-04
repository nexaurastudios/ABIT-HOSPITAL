from datetime import datetime, date, time
from app.extensions import db

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(
        db.String(30),
        default='Scheduled',
        nullable=False,
        index=True
    )  # Scheduled, Confirmed, Waiting, In Consultation, Completed, Cancelled, No Show
    reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    visit = db.relationship('Visit', backref='appointment', uselist=False, cascade='all, delete-orphan')

    # Unique constraint: No two appointments for the same doctor at the same date and time unless Cancelled!
    __table_args__ = (
        db.Index('idx_doctor_datetime', 'doctor_id', 'appointment_date', 'appointment_time'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'patient_name': self.patient.full_name if self.patient else 'Unknown',
            'patient_code': self.patient.patient_id if self.patient else '',
            'doctor_name': f"Dr. {self.doctor.name}" if self.doctor else 'Unknown',
            'department_name': self.department.name if self.department else 'Unknown',
            'appointment_date': self.appointment_date.strftime('%Y-%m-%d'),
            'appointment_time': self.appointment_time.strftime('%H:%M'),
            'status': self.status,
            'reason': self.reason
        }

    def __repr__(self):
        return f"<Appointment {self.appointment_id} ({self.status})>"
