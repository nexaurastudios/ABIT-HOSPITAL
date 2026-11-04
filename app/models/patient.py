from datetime import datetime, date
from app.extensions import db

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=False)  # Male, Female, Other
    phone = db.Column(db.String(30), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    blood_group = db.Column(db.String(10), nullable=False)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    emergency_contact = db.Column(db.String(50), nullable=True)
    registration_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    assigned_department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(30), default='Outpatient', nullable=False)  # Outpatient, Admitted, Discharged
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')
    visits = db.relationship('Visit', backref='patient', lazy=True, cascade='all, delete-orphan')
    admissions = db.relationship('Admission', backref='patient', lazy=True, cascade='all, delete-orphan')

    @property
    def active_admission(self):
        for adm in self.admissions:
            if adm.status == 'Active':
                return adm
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'full_name': self.full_name,
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'blood_group': self.blood_group,
            'registration_date': self.registration_date.strftime('%Y-%m-%d') if self.registration_date else '',
            'status': self.status,
            'department': self.assigned_department.name if self.assigned_department else 'Unassigned'
        }

    def __repr__(self):
        return f"<Patient {self.patient_id} - {self.full_name}>"
