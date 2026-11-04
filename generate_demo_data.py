from app import create_app
from app.services.data_generator import generate_full_synthetic_dataset

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print("Starting synthetic dataset generation pipeline...")
        print("Targeting ~5,000 patients, ~1,000 appointments, ~200 beds, ~30 doctors, visits & admissions...")
        summary = generate_full_synthetic_dataset()
        print("\nGeneration Complete:")
        for k, v in summary.items():
            print(f" - {k.capitalize()}: {v}")

