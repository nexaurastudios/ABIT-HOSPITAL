from app import create_app
from app.ml.demand_forecaster import DemandForecaster
from app.ml.waiting_time_predictor import WaitingTimePredictor

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print("Training Machine Learning System A: Patient Demand Forecaster...")
        forecaster = DemandForecaster()
        res_demand = forecaster.train_models()
        print(f"Demand Forecaster Status: {res_demand.get('message')}")
        if res_demand.get('success'):
            print("Model Comparison Results:")
            for m_name, m_stats in res_demand['results'].items():
                print(f"  * {m_name}: MAE={m_stats['mae']}, RMSE={m_stats['rmse']}, R2={m_stats['r2_score']}")

        print("\nTraining Machine Learning System B: Patient Waiting Time Predictor...")
        predictor = WaitingTimePredictor()
        res_waiting = predictor.train_models()
        print(f"Waiting Time Predictor Status: {res_waiting.get('message')}")
        if res_waiting.get('success'):
            print("Model Comparison Results:")
            for m_name, m_stats in res_waiting['results'].items():
                print(f"  * {m_name}: MAE={m_stats['mae']} mins, RMSE={m_stats['rmse']}, R2={m_stats['r2_score']}")

        print("\nMachine Learning Training Pipeline Completed.")

