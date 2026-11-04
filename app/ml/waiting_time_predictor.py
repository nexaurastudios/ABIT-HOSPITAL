import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.extensions import db
from app.models.visit import Visit
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.ml import ModelRegistry, PredictionLog

MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'models_store')
os.makedirs(MODEL_DIR, exist_ok=True)

class WaitingTimePredictor:
    def __init__(self):
        self.model_file = os.path.join(MODEL_DIR, 'waiting_time_model.joblib')
        self.meta_file = os.path.join(MODEL_DIR, 'waiting_time_meta.json')
        self.model = None
        self.metadata = {}
        self._load_if_exists()

    def _load_if_exists(self):
        if os.path.exists(self.model_file) and os.path.exists(self.meta_file):
            try:
                self.model = joblib.load(self.model_file)
                with open(self.meta_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"[ML WaitingTime] Error loading model: {e}")
                self.model = None

    def prepare_dataset(self):
        """Prepare clean historical training records from completed visits with valid waiting times"""
        visits = Visit.query.filter(
            Visit.waiting_time_minutes.isnot(None),
            Visit.waiting_time_minutes > 0,
            Visit.arrival_time.isnot(None),
            Visit.consultation_start_time.isnot(None)
        ).all()

        if len(visits) < 30:
            return None, "Insufficient data: At least 30 historical visit records with verified arrival and consultation timestamps are required."

        records = []
        for v in visits:
            # Derive arrival hour and day of week
            arr_hour = v.arrival_time.hour + (v.arrival_time.minute / 60.0)
            dow = v.arrival_time.weekday()
            
            # Consult duration if completed, else fallback to 15.0 mins
            consult_dur = v.consultation_duration_minutes if v.consultation_duration_minutes else 15.0
            
            # Estimate queue size and available doctors at that time/dept
            dept_id = v.department_id
            
            records.append({
                'dept_id': dept_id,
                'arrival_hour': arr_hour,
                'day_of_week': dow,
                'avg_consult_duration': consult_dur,
                # In real historical replay, synthetic/real queue proxy:
                'queue_size': max(1, int(v.waiting_time_minutes / max(5.0, consult_dur))),
                'available_doctors': 2, # default baseline
                'target_waiting_time': v.waiting_time_minutes
            })

        df = pd.DataFrame(records)
        return df, None

    def train_models(self, admin_id=None):
        """Train regression models, pick best based on MAE/RMSE, serialize with joblib"""
        df, err = self.prepare_dataset()
        if err:
            return {'success': False, 'message': err}

        features = ['dept_id', 'arrival_hour', 'day_of_week', 'avg_consult_duration', 'queue_size', 'available_doctors']
        X = df[features]
        y = df['target_waiting_time']

        # 80/20 train/test split
        split_idx = int(len(df) * 0.8)
        indices = np.random.RandomState(42).permutation(len(df))
        train_idx, test_idx = indices[:split_idx], indices[split_idx:]

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        candidates = {
            'Gradient Boosting Regressor': GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=3, random_state=42),
            'Random Forest Regressor': RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42),
            'Linear Regression': LinearRegression()
        }

        results = {}
        best_name = None
        best_rmse = float('inf')
        best_model = None

        for name, model_instance in candidates.items():
            model_instance.fit(X_train, y_train)
            preds = model_instance.predict(X_test)
            preds = np.clip(preds, 2.0, None)  # Waiting time at least 2 minutes

            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
            r2 = float(r2_score(y_test, preds)) if len(y_test) > 1 else 0.0

            results[name] = {
                'mae': round(mae, 2),
                'rmse': round(rmse, 2),
                'r2_score': round(max(0.0, r2), 3)
            }

            if rmse < best_rmse:
                best_rmse = rmse
                best_name = name
                best_model = model_instance

        joblib.dump(best_model, self.model_file)
        self.model = best_model

        metadata = {
            'best_algorithm': best_name,
            'features': features,
            'training_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': results,
            'disclaimer': "These predictions are estimates for hospital operational planning and are not guaranteed waiting times or medical advice."
        }

        with open(self.meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.metadata = metadata

        # Save to database ModelRegistry
        try:
            ModelRegistry.query.filter_by(model_name='patient_waiting_time_prediction').update({'is_active': False})
            
            for name, res in results.items():
                is_best = (name == best_name)
                reg_entry = ModelRegistry(
                    model_name='patient_waiting_time_prediction',
                    algorithm_name=name,
                    version='1.0',
                    mae=res['mae'],
                    rmse=res['rmse'],
                    r2_score=res['r2_score'],
                    parameters=json.dumps({'features': features}),
                    file_path=self.model_file if is_best else '',
                    is_active=is_best,
                    trained_by_admin_id=admin_id,
                    trained_at=datetime.utcnow()
                )
                db.session.add(reg_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[ML WaitingTime ModelRegistry Error] {e}")

        return {
            'success': True,
            'message': f"Waiting time predictor trained successfully. Selected '{best_name}' (MAE: {results[best_name]['mae']} mins).",
            'best_algorithm': best_name,
            'results': results
        }

    def predict(self, dept_id, queue_size, available_doctors, arrival_hour=None, day_of_week=None):
        """Predict expected waiting time for an incoming patient"""
        if not self.model:
            self._load_if_exists()
        if not self.model:
            return {'error': 'Waiting time model not trained yet. Please train models in Machine Learning module.'}

        now = datetime.utcnow()
        if arrival_hour is None:
            arrival_hour = now.hour + (now.minute / 60.0)
        if day_of_week is None:
            day_of_week = now.weekday()

        # Query department historical average consultation duration
        recent_visits = Visit.query.filter(
            Visit.department_id == dept_id,
            Visit.consultation_duration_minutes.isnot(None)
        ).limit(50).all()
        
        if recent_visits:
            avg_consult = sum(v.consultation_duration_minutes for v in recent_visits) / len(recent_visits)
        else:
            avg_consult = 15.0

        avail_docs = max(1, int(available_doctors))
        q_size = max(0, int(queue_size))

        input_df = pd.DataFrame([{
            'dept_id': int(dept_id),
            'arrival_hour': float(arrival_hour),
            'day_of_week': int(day_of_week),
            'avg_consult_duration': float(avg_consult),
            'queue_size': q_size,
            'available_doctors': avail_docs
        }])

        raw_pred = float(self.model.predict(input_df)[0])
        # Operational baseline adjustment: queue / doctors * avg_consult
        physical_estimate = (q_size / avail_docs) * avg_consult
        # Blend model prediction with physical queue law
        predicted_wait = max(3.0, round(0.7 * raw_pred + 0.3 * physical_estimate, 1))

        mae = self.metadata.get('metrics', {}).get(self.metadata.get('best_algorithm', ''), {}).get('mae', 6.0)
        lower_bound = max(2.0, round(predicted_wait - mae, 1))
        upper_bound = round(predicted_wait + mae, 1)

        dept = Department.query.get(dept_id)
        dept_name = dept.name if dept else f"Department #{dept_id}"

        result = {
            'department_id': dept_id,
            'department_name': dept_name,
            'predicted_waiting_time_minutes': predicted_wait,
            'lower_bound_minutes': lower_bound,
            'upper_bound_minutes': upper_bound,
            'queue_size': q_size,
            'available_doctors': avail_docs,
            'average_consultation_duration': round(avg_consult, 1),
            'prediction_timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            'disclaimer': "These predictions are estimates for hospital operational planning and are not guaranteed waiting times or medical advice."
        }

        # Log prediction to prediction_logs
        try:
            active_model = ModelRegistry.query.filter_by(
                model_name='patient_waiting_time_prediction',
                is_active=True
            ).first()

            pred_log = PredictionLog(
                model_id=active_model.id if active_model else None,
                prediction_type='Patient Waiting Time',
                input_data=json.dumps(input_df.to_dict(orient='records')[0]),
                prediction_result=json.dumps(result),
                created_at=now
            )
            db.session.add(pred_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[PredictionLog Error] {e}")

        return result
