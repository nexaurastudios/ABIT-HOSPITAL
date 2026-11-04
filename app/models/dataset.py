from datetime import datetime
from app.extensions import db

class DatasetImport(db.Model):
    __tablename__ = 'dataset_imports'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # Patients, Doctors, Appointments, Beds
    row_count = db.Column(db.Integer, default=0, nullable=False)
    imported_count = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(30), default='Pending', nullable=False)  # Pending, Completed, Failed, Partially Imported
    error_log = db.Column(db.Text, nullable=True)
    imported_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'row_count': self.row_count,
            'imported_count': self.imported_count,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f"<DatasetImport {self.file_name} ({self.status})>"
