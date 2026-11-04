from datetime import datetime
from app.extensions import db

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    head_of_department = db.Column(db.String(120), nullable=True)
    floor = db.Column(db.String(30), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctors = db.relationship('Doctor', backref='department', lazy=True, cascade='all, delete-orphan')
    patients = db.relationship('Patient', backref='assigned_department', lazy=True)
    appointments = db.relationship('Appointment', backref='department', lazy=True)
    visits = db.relationship('Visit', backref='department', lazy=True)
    beds = db.relationship('Bed', backref='department', lazy=True)
    admissions = db.relationship('Admission', backref='department', lazy=True)
    resources = db.relationship('Resource', backref='department', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'head': self.head_of_department,
            'floor': self.floor,
            'phone': self.phone,
            'is_active': self.is_active,
            'doctor_count': len(self.doctors),
            'bed_count': len(self.beds)
        }

    def __repr__(self):
        return f"<Department {self.code}: {self.name}>"
