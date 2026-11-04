from datetime import datetime
from app.extensions import db

class ModelRegistry(db.Model):
    __tablename__ = 'model_registry'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(80), nullable=False, index=True)  # patient_demand_forecast, patient_waiting_time_prediction
    algorithm_name = db.Column(db.String(80), nullable=False)           # Random Forest, Gradient Boosting, Linear Regression
    version = db.Column(db.String(30), default='1.0', nullable=False)
    mae = db.Column(db.Float, nullable=False)
    rmse = db.Column(db.Float, nullable=False)
    r2_score = db.Column(db.Float, nullable=False)
    parameters = db.Column(db.Text, nullable=True)                      # JSON string
    file_path = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    trained_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'), nullable=True)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    predictions = db.relationship('PredictionLog', backref='model', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'algorithm_name': self.algorithm_name,
            'version': self.version,
            'mae': round(self.mae, 3),
            'rmse': round(self.rmse, 3),
            'r2_score': round(self.r2_score, 4),
            'is_active': self.is_active,
            'trained_at': self.trained_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f"<ModelRegistry {self.model_name} - {self.algorithm_name} (R2: {self.r2_score:.3f})>"


class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model_registry.id', ondelete='SET NULL'), nullable=True)
    prediction_type = db.Column(db.String(60), nullable=False, index=True)
    input_data = db.Column(db.Text, nullable=False)                      # JSON representation of input features
    prediction_result = db.Column(db.Text, nullable=False)               # JSON representation of output prediction
    actual_value = db.Column(db.Float, nullable=True)                    # To calculate real-world drift later
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<PredictionLog {self.prediction_type} at {self.created_at}>"
