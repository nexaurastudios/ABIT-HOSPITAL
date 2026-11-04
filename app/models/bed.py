from datetime import datetime
from app.extensions import db

class Bed(db.Model):
    __tablename__ = 'beds'

    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(db.String(30), unique=True, nullable=False, index=True)  # e.g., BED-GEN-101
    bed_number = db.Column(db.String(20), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    ward = db.Column(db.String(50), nullable=False)  # Ward A, Ward B, West Wing, etc.
    bed_type = db.Column(
        db.String(30),
        default='General Ward',
        nullable=False
    )  # General Ward, ICU, Private Room, Emergency, Semi-Private
    occupancy_status = db.Column(
        db.String(30),
        default='Available',
        nullable=False,
        index=True
    )  # Available, Occupied, Reserved, Maintenance
    current_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    current_admission_id = db.Column(db.Integer, nullable=True)  # Links to active admission
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    admissions = db.relationship('Admission', backref='bed', lazy=True)
    current_patient = db.relationship('Patient', foreign_keys=[current_patient_id], lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'bed_id': self.bed_id,
            'bed_number': self.bed_number,
            'department_name': self.department.name if self.department else 'N/A',
            'ward': self.ward,
            'bed_type': self.bed_type,
            'occupancy_status': self.occupancy_status,
            'current_patient': self.current_patient.full_name if self.current_patient else None
        }

    def __repr__(self):
        return f"<Bed {self.bed_id} ({self.bed_type} - {self.occupancy_status})>"


class Admission(db.Model):
    __tablename__ = 'admissions'

    id = db.Column(db.Integer, primary_key=True)
    admission_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id', ondelete='RESTRICT'), nullable=False)
    
    admission_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    discharge_date = db.Column(db.DateTime, nullable=True)
    admission_reason = db.Column(db.String(255), nullable=False)
    diagnosis = db.Column(db.Text, nullable=True)
    discharge_notes = db.Column(db.Text, nullable=True)
    discharge_condition = db.Column(db.String(50), nullable=True)  # Recovered, Improved, Transferred, Against Medical Advice
    status = db.Column(db.String(30), default='Active', nullable=False, index=True)  # Active, Discharged
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Helper properties
    @property
    def duration_days(self):
        end = self.discharge_date or datetime.utcnow()
        delta = end - self.admission_date
        return max(1, delta.days)

    def to_dict(self):
        return {
            'id': self.id,
            'admission_id': self.admission_id,
            'patient_name': self.patient.full_name if self.patient else 'Unknown',
            'patient_code': self.patient.patient_id if self.patient else '',
            'doctor_name': f"Dr. {self.doctor.name}" if self.doctor else 'Unknown',
            'department_name': self.department.name if self.department else 'Unknown',
            'bed_id': self.bed.bed_id if self.bed else 'N/A',
            'admission_date': self.admission_date.strftime('%Y-%m-%d %H:%M'),
            'discharge_date': self.discharge_date.strftime('%Y-%m-%d %H:%M') if self.discharge_date else 'Active',
            'status': self.status,
            'admission_reason': self.admission_reason
        }

    def __repr__(self):
        return f"<Admission {self.admission_id} ({self.status})>"
