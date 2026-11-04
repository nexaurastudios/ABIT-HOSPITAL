from datetime import datetime
from app.extensions import db

class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(120), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # Ventilator, Monitor, Wheelchair, Oxygen Concentrator, Ambulance
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    total_quantity = db.Column(db.Integer, default=1, nullable=False)
    available_quantity = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(30), default='Operational', nullable=False)  # Operational, Maintenance, Low Stock
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def utilization_percentage(self):
        if self.total_quantity > 0:
            in_use = self.total_quantity - self.available_quantity
            return round((in_use / self.total_quantity) * 100, 1)
        return 0.0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.resource_name,
            'type': self.resource_type,
            'department': self.department.name if self.department else 'N/A',
            'total': self.total_quantity,
            'available': self.available_quantity,
            'in_use': self.total_quantity - self.available_quantity,
            'utilization': self.utilization_percentage,
            'status': self.status
        }

    def __repr__(self):
        return f"<Resource {self.resource_name} ({self.available_quantity}/{self.total_quantity})>"
