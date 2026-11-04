from datetime import datetime
from app.extensions import db

class HospitalSetting(db.Model):
    __tablename__ = 'hospital_settings'

    id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(150), default='Apex Health & Analytics Center', nullable=False)
    logo_path = db.Column(db.String(255), default='/static/img/logo.svg', nullable=True)
    phone = db.Column(db.String(40), default='+1 (800) 555-0199', nullable=True)
    email = db.Column(db.String(120), default='info@apexhealth.org', nullable=True)
    address = db.Column(db.String(255), default='742 Healthcare Boulevard, Medical District', nullable=True)
    bed_capacity_alert_threshold = db.Column(db.Integer, default=85, nullable=False)  # % occupancy threshold
    waiting_time_alert_threshold = db.Column(db.Integer, default=45, nullable=False)  # minutes threshold
    currency = db.Column(db.String(10), default='$', nullable=False)
    consultation_fee = db.Column(db.Float, default=75.0, nullable=False)
    system_mode = db.Column(db.String(30), default='Production', nullable=False)      # Production, Demonstration, Maintenance
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_settings(cls):
        setting = cls.query.first()
        if not setting:
            setting = cls()
            db.session.add(setting)
            db.session.commit()
        return setting

    def __repr__(self):
        return f"<HospitalSetting {self.hospital_name}>"
