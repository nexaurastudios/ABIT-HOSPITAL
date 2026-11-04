from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.department import Department
from app.models.ml import ModelRegistry, PredictionLog
from app.ml.demand_forecaster import DemandForecaster
from app.ml.waiting_time_predictor import WaitingTimePredictor
from app.services.activity_logger import log_activity
from app.services.notification_service import create_notification

ml_bp = Blueprint('ml', __name__, url_prefix='/ml')

forecaster = DemandForecaster()
waiting_predictor = WaitingTimePredictor()

@ml_bp.route('/')
@login_required
def index():
    # Demand forecast models registry
    demand_models = ModelRegistry.query.filter_by(model_name='patient_demand_forecast').order_by(ModelRegistry.rmse.asc()).all()
    active_demand_model = next((m for m in demand_models if m.is_active), None)

    # Waiting time models registry
    waiting_models = ModelRegistry.query.filter_by(model_name='patient_waiting_time_prediction').order_by(ModelRegistry.mae.asc()).all()
    active_waiting_model = next((m for m in waiting_models if m.is_active), None)

    # Generate multi-day patient volume forecast
    forecast_data = forecaster.forecast_next_days(days=7)
    
    # Departments list for live predictor
    departments = Department.query.filter_by(is_active=True).all()

    # Recent prediction logs
    recent_predictions = PredictionLog.query.order_by(PredictionLog.created_at.desc()).limit(8).all()

    return render_template(
        'ml/index.html',
        demand_models=demand_models,
        active_demand_model=active_demand_model,
        waiting_models=waiting_models,
        active_waiting_model=active_waiting_model,
        forecast_data=forecast_data,
        departments=departments,
        recent_predictions=recent_predictions
    )

@ml_bp.route('/predict-waiting-time', methods=['POST'])
@login_required
def predict_waiting_time():
    dept_id = request.form.get('department_id', type=int)
    queue_size = request.form.get('queue_size', default=5, type=int)
    available_doctors = request.form.get('available_doctors', default=2, type=int)
    arrival_time_str = request.form.get('arrival_time')

    if not dept_id:
        flash('Please select a department for waiting time prediction.', 'danger')
        return redirect(url_for('ml.index'))

    arrival_hour = None
    if arrival_time_str:
        try:
            t = datetime.strptime(arrival_time_str, '%H:%M').time()
            arrival_hour = t.hour + (t.minute / 60.0)
        except ValueError:
            pass

    prediction = waiting_predictor.predict(
        dept_id=dept_id,
        queue_size=queue_size,
        available_doctors=available_doctors,
        arrival_hour=arrival_hour
    )

    if 'error' in prediction:
        flash(prediction['error'], 'warning')
        return redirect(url_for('ml.index'))

    return render_template(
        'ml/index.html',
        demand_models=ModelRegistry.query.filter_by(model_name='patient_demand_forecast').all(),
        active_demand_model=ModelRegistry.query.filter_by(model_name='patient_demand_forecast', is_active=True).first(),
        waiting_models=ModelRegistry.query.filter_by(model_name='patient_waiting_time_prediction').all(),
        active_waiting_model=ModelRegistry.query.filter_by(model_name='patient_waiting_time_prediction', is_active=True).first(),
        forecast_data=forecaster.forecast_next_days(days=7),
        departments=Department.query.filter_by(is_active=True).all(),
        recent_predictions=PredictionLog.query.order_by(PredictionLog.created_at.desc()).limit(8).all(),
        active_prediction=prediction
    )

@ml_bp.route('/retrain', methods=['POST'])
@login_required
def retrain():
    model_type = request.form.get('model_type', 'all')
    admin_id = current_user.id if current_user.is_authenticated else None

    results = []

    if model_type in ['all', 'demand']:
        res_demand = forecaster.train_models(admin_id=admin_id)
        results.append(('Demand Forecaster', res_demand))

    if model_type in ['all', 'waiting_time']:
        res_waiting = waiting_predictor.train_models(admin_id=admin_id)
        results.append(('Waiting Time Predictor', res_waiting))

    success = all(r[1].get('success') for r in results)
    msg = "; ".join(f"{r[0]}: {r[1].get('message')}" for r in results)

    if success:
        log_activity("TRAIN_ML_MODELS", "Machine Learning", f"Retrained models ({model_type}): {msg}")
        create_notification(
            title="Machine Learning Models Retrained",
            message=f"Model retraining completed successfully. {msg}",
            category="success",
            related_url="/ml"
        )
        flash(f"ML Models retrained successfully! {msg}", "success")
    else:
        flash(f"Retraining encountered an issue: {msg}", "danger")

    return redirect(url_for('ml.index'))
