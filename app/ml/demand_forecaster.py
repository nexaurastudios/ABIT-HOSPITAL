import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.extensions import db
from app.models.visit import Visit
from app.models.appointment import Appointment
from app.models.department import Department
from app.models.ml import ModelRegistry

MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'models_store')
os.makedirs(MODEL_DIR, exist_ok=True)

class DemandForecaster:
    def __init__(self):
        self.model_file = os.path.join(MODEL_DIR, 'demand_model.joblib')
        self.meta_file = os.path.join(MODEL_DIR, 'demand_meta.json')
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
                print(f"[ML Forecaster] Error loading model: {e}")
                self.model = None

    def prepare_dataset(self):
        """Extract daily patient volumes from actual database visits & appointments"""
        # Retrieve date, department from all visits and appointments
        visits = db.session.query(Visit.visit_date, Visit.department_id).all()
        appts = db.session.query(Appointment.appointment_date, Appointment.department_id).filter(
            Appointment.status.in_(['Completed', 'Confirmed', 'Scheduled', 'Waiting', 'In Consultation'])
        ).all()

        data = []
        for v_date, dept_id in visits:
            if v_date:
                data.append({'date': pd.to_datetime(v_date), 'dept_id': dept_id or 1})
        for a_date, dept_id in appts:
            if a_date:
                data.append({'date': pd.to_datetime(a_date), 'dept_id': dept_id or 1})

        if not data or len(data) < 30:
            return None, "Insufficient data: At least 30 historical patient records are required to train the forecasting model."

        df = pd.DataFrame(data)
        
        # Aggregate daily patient counts overall
        daily = df.groupby('date').size().reset_index(name='patient_count')
        daily = daily.sort_values('date').set_index('date')

        # Fill missing calendar dates with rolling interpolation or 0
        idx = pd.date_range(daily.index.min(), daily.index.max())
        daily = daily.reindex(idx, fill_value=0).reset_index()
        daily.rename(columns={'index': 'date'}, inplace=True)

        # Feature Engineering: Lag and Time Features
        daily['day_of_week'] = daily['date'].dt.dayofweek
        daily['month'] = daily['date'].dt.month
        daily['day_of_month'] = daily['date'].dt.day
        daily['is_weekend'] = daily['day_of_week'].isin([5, 6]).astype(int)
        
        # Lag features
        daily['lag_1'] = daily['patient_count'].shift(1)
        daily['lag_2'] = daily['patient_count'].shift(2)
        daily['lag_7'] = daily['patient_count'].shift(7)
        daily['rolling_7_mean'] = daily['patient_count'].shift(1).rolling(window=7, min_periods=1).mean()

        daily = daily.dropna().reset_index(drop=True)
        if len(daily) < 15:
            return None, "Insufficient chronological date range after computing lag features."

        return daily, None

    def train_models(self, admin_id=None):
        """Train Linear Regression, Random Forest, and Gradient Boosting; select best; register metrics"""
        df, err = self.prepare_dataset()
        if err:
            return {'success': False, 'message': err}

        features = ['day_of_week', 'month', 'day_of_month', 'is_weekend', 'lag_1', 'lag_2', 'lag_7', 'rolling_7_mean']
        X = df[features]
        y = df['patient_count']

        # Chronological split (80% train, 20% test) to prevent temporal data leakage
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        candidates = {
            'Random Forest Regressor': RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
            'Gradient Boosting Regressor': GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42),
            'Linear Regression': LinearRegression()
        }

        results = {}
        best_model_name = None
        best_rmse = float('inf')
        best_model = None

        for name, model_instance in candidates.items():
            model_instance.fit(X_train, y_train)
            preds = model_instance.predict(X_test)
            preds = np.clip(preds, 0, None)  # Patients volume cannot be negative

            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
            r2 = float(r2_score(y_test, preds)) if len(y_test) > 1 else 0.0

            results[name] = {
                'mae': round(mae, 2),
                'rmse': round(rmse, 2),
                'r2_score': round(max(0.0, r2), 3),
                'model': model_instance
            }

            if rmse < best_rmse:
                best_rmse = rmse
                best_model_name = name
                best_model = model_instance

        # Save best model to disk
        joblib.dump(best_model, self.model_file)
        self.model = best_model

        metadata = {
            'best_algorithm': best_model_name,
            'features': features,
            'training_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {k: {m: v[m] for m in ['mae', 'rmse', 'r2_score']} for k, v in results.items()},
            'last_known_count': float(df['patient_count'].iloc[-1]),
            'last_known_date': df['date'].iloc[-1].strftime('%Y-%m-%d')
        }

        with open(self.meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.metadata = metadata

        # Save to database ModelRegistry
        try:
            # Deactivate previous active entries for demand forecast
            ModelRegistry.query.filter_by(model_name='patient_demand_forecast').update({'is_active': False})
            
            for name, res in results.items():
                is_best = (name == best_model_name)
                reg_entry = ModelRegistry(
                    model_name='patient_demand_forecast',
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
            print(f"[ML ModelRegistry Error] {e}")

        return {
            'success': True,
            'message': f"Model trained successfully. Selected '{best_model_name}' as best model (RMSE: {results[best_model_name]['rmse']}).",
            'best_algorithm': best_model_name,
            'results': results
        }

    def forecast_next_days(self, days=7):
        """Generate dynamic multi-day demand forecast"""
        if not self.model:
            self._load_if_exists()
        if not self.model:
            return {'error': 'Forecasting model not yet trained. Please train the model in the Machine Learning module.'}

        df, err = self.prepare_dataset()
        if err:
            return {'error': err}

        recent_counts = list(df['patient_count'].tail(14).values)
        last_date = df['date'].iloc[-1]

        forecasts = []
        for i in range(1, days + 1):
            next_date = last_date + timedelta(days=i)
            dow = next_date.dayofweek
            month = next_date.month
            dom = next_date.day
            is_wknd = 1 if dow in [5, 6] else 0

            lag1 = recent_counts[-1]
            lag2 = recent_counts[-2]
            lag7 = recent_counts[-7] if len(recent_counts) >= 7 else np.mean(recent_counts)
            roll7 = float(np.mean(recent_counts[-7:]))

            row = pd.DataFrame([{
                'day_of_week': dow,
                'month': month,
                'day_of_month': dom,
                'is_weekend': is_wknd,
                'lag_1': lag1,
                'lag_2': lag2,
                'lag_7': lag7,
                'rolling_7_mean': roll7
            }])

            pred = float(self.model.predict(row)[0])
            pred_count = max(5, int(round(pred)))
            recent_counts.append(pred_count)

            forecasts.append({
                'date': next_date.strftime('%Y-%m-%d'),
                'day_name': next_date.strftime('%A'),
                'predicted_patients': pred_count,
                'lower_bound': max(0, int(pred_count - 1.96 * self.metadata.get('metrics', {}).get(self.metadata.get('best_algorithm', ''), {}).get('rmse', 5))),
                'upper_bound': int(pred_count + 1.96 * self.metadata.get('metrics', {}).get(self.metadata.get('best_algorithm', ''), {}).get('rmse', 5))
            })

        return {
            'forecasts': forecasts,
            'metadata': self.metadata,
            'next_day_prediction': forecasts[0]['predicted_patients'] if forecasts else 0,
            'seven_day_total': sum(f['predicted_patients'] for f in forecasts)
        }
