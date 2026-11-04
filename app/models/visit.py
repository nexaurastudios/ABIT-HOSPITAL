from datetime import datetime, date
from app.extensions import db

class Visit(db.Model):
    __tablename__ = 'visits'

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    visit_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    
    # Precise timestamps for waiting time analytics
    arrival_time = db.Column(db.DateTime, nullable=True)
    registration_time = db.Column(db.DateTime, nullable=True)
    consultation_start_time = db.Column(db.DateTime, nullable=True)
    consultation_end_time = db.Column(db.DateTime, nullable=True)

    # Calculated metrics in minutes
    waiting_time_minutes = db.Column(db.Float, nullable=True)  # consultation_start_time - arrival_time
    consultation_duration_minutes = db.Column(db.Float, nullable=True)  # consultation_end_time - consultation_start_time
    
    symptoms = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='In Progress', nullable=False)  # Waiting, In Consultation, Completed, Incomplete, Cancelled
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_metrics(self):
        """Calculate waiting time and duration only when timestamps are complete"""
        if self.arrival_time and self.consultation_start_time:
            delta = self.consultation_start_time - self.arrival_time
            self.waiting_time_minutes = max(0.0, round(delta.total_seconds() / 60.0, 1))
        else:
            self.waiting_time_minutes = None

        if self.consultation_start_time and self.consultation_end_time:
            delta = self.consultation_end_time - self.consultation_start_time
            self.consultation_duration_minutes = max(0.0, round(delta.total_seconds() / 60.0, 1))
        else:
            self.consultation_duration_minutes = None

    @property
    def is_complete_flow(self):
        return bool(self.arrival_time and self.consultation_start_time and self.consultation_end_time)

    def to_dict(self):
        return {
            'id': self.id,
            'visit_id': self.visit_id,
            'patient_name': self.patient.full_name if self.patient else 'Unknown',
            'doctor_name': f"Dr. {self.doctor.name}" if self.doctor else 'Unknown',
            'department_name': self.department.name if self.department else 'Unknown',
            'visit_date': self.visit_date.strftime('%Y-%m-%d'),
            'arrival_time': self.arrival_time.strftime('%H:%M') if self.arrival_time else None,
            'consultation_start_time': self.consultation_start_time.strftime('%H:%M') if self.consultation_start_time else None,
            'consultation_end_time': self.consultation_end_time.strftime('%H:%M') if self.consultation_end_time else None,
            'waiting_time_minutes': self.waiting_time_minutes,
            'consultation_duration_minutes': self.consultation_duration_minutes,
            'status': self.status
        }

    def __repr__(self):
        return f"<Visit {self.visit_id} for Pat {self.patient_id}>"
