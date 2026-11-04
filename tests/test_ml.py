import pytest
from app import create_app
from app.config import Config
from app.extensions import db
from app.ml.demand_forecaster import DemandForecaster
from app.ml.waiting_time_predictor import WaitingTimePredictor

@pytest.fixture
def app():
    app = create_app(Config)
    with app.app_context():
        yield app

def test_demand_forecaster_generates_forecast(app):
    with app.app_context():
        forecaster = DemandForecaster()
        data = forecaster.forecast_next_days(days=7)
        assert 'forecasts' in data
        assert len(data['forecasts']) == 7
        assert 'predicted_patients' in data['forecasts'][0]
        assert data['forecasts'][0]['predicted_patients'] > 0

def test_waiting_time_predictor(app):
    with app.app_context():
        predictor = WaitingTimePredictor()
        res = predictor.predict(dept_id=1, queue_size=5, available_doctors=2, arrival_hour=10.0, day_of_week=2)
        assert 'predicted_waiting_time_minutes' in res
        assert res['predicted_waiting_time_minutes'] >= 2.0
        assert 'disclaimer' in res
