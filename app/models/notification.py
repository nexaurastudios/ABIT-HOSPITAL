from datetime import datetime
from app.extensions import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default='info', nullable=False)  # info, warning, success, danger
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    related_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'category': self.category,
            'is_read': self.is_read,
            'related_url': self.related_url,
            'time_ago': self.created_at.strftime('%b %d, %H:%M')
        }

    def __repr__(self):
        return f"<Notification {self.title}>"


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'), nullable=True)
    admin_email = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'CREATE_PATIENT', 'DISCHARGE', 'TRAIN_ML_MODEL'
    module = db.Column(db.String(50), nullable=False, index=True)   # Patients, Doctors, Beds, Machine Learning, etc.
    details = db.Column(db.Text, nullable=True)
    record_id = db.Column(db.String(60), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'admin': self.admin_email,
            'action': self.action,
            'module': self.module,
            'details': self.details,
            'record_id': self.record_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.admin_email} on {self.module}>"
