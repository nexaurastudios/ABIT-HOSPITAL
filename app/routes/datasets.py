import os
import io
import pandas as pd
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.dataset import DatasetImport
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.bed import Bed
from app.services.data_generator import generate_full_synthetic_dataset
from app.services.activity_logger import log_activity

datasets_bp = Blueprint('datasets', __name__, url_prefix='/datasets')

UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'sample_data')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Expected schemas for validation
SCHEMAS = {
    'Patients': ['full_name', 'age', 'gender', 'phone', 'blood_group'],
    'Doctors': ['name', 'qualification', 'specialization', 'phone', 'email'],
    'Departments': ['name', 'code', 'head_of_department'],
    'Beds': ['bed_number', 'ward', 'bed_type']
}

@datasets_bp.route('/')
@login_required
def index():
    imports = DatasetImport.query.order_by(DatasetImport.created_at.desc()).all()
    
    # Counts
    counts = {
        'patients': Patient.query.count(),
        'doctors': Doctor.query.count(),
        'departments': Department.query.count(),
        'beds': Bed.query.count()
    }

    return render_template('datasets/index.html', imports=imports, counts=counts)

@datasets_bp.route('/upload-preview', methods=['POST'])
@login_required
def upload_preview():
    if 'file' not in request.files:
        flash('No file provided.', 'danger')
        return redirect(url_for('datasets.index'))

    file = request.files['file']
    dataset_type = request.form.get('dataset_type', 'Patients')

    if file.filename == '' or not file.filename.endswith('.csv'):
        flash('Please upload a valid CSV (.csv) file.', 'danger')
        return redirect(url_for('datasets.index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, f"temp_{filename}")
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        total_rows = len(df)
        cols = list(df.columns)
        
        # Validation checks
        expected = SCHEMAS.get(dataset_type, [])
        missing_cols = [c for c in expected if c not in cols]
        
        missing_values_count = int(df.isnull().sum().sum())
        duplicate_rows_count = int(df.duplicated().sum())

        preview_rows = df.head(10).to_dict(orient='records')

        # Persist filepath in session or form for confirmation
        return render_template(
            'datasets/preview.html',
            filename=filename,
            temp_path=filepath,
            dataset_type=dataset_type,
            total_rows=total_rows,
            columns=cols,
            missing_cols=missing_cols,
            missing_values=missing_values_count,
            duplicates=duplicate_rows_count,
            preview_rows=preview_rows,
            is_valid=(len(missing_cols) == 0)
        )
    except Exception as e:
        flash(f"Error reading CSV file: {str(e)}", 'danger')
        return redirect(url_for('datasets.index'))

@datasets_bp.route('/commit-import', methods=['POST'])
@login_required
def commit_import():
    temp_path = request.form.get('temp_path')
    dataset_type = request.form.get('dataset_type')
    filename = request.form.get('filename')

    if not temp_path or not os.path.exists(temp_path):
        flash('Uploaded file expired. Please upload again.', 'warning')
        return redirect(url_for('datasets.index'))

    try:
        df = pd.read_csv(temp_path)
        imported_count = 0

        if dataset_type == 'Patients':
            year_month = datetime.utcnow().strftime('%Y%m')
            curr_max = Patient.query.count() + 1
            for idx, row in df.iterrows():
                pat_id = f"PAT-{year_month}-{(curr_max + idx):04d}"
                p = Patient(
                    patient_id=pat_id,
                    full_name=str(row.get('full_name', 'Patient')),
                    age=int(row.get('age', 30)),
                    gender=str(row.get('gender', 'Other')),
                    phone=str(row.get('phone', '555-0000')),
                    email=str(row.get('email', '')) if pd.notna(row.get('email')) else None,
                    blood_group=str(row.get('blood_group', 'O+')),
                    status='Outpatient',
                    is_demo=False
                )
                db.session.add(p)
                imported_count += 1

        db.session.commit()

        # Record dataset import audit
        rec = DatasetImport(
            file_name=filename,
            file_type=dataset_type,
            row_count=len(df),
            imported_count=imported_count,
            status='Completed',
            imported_by_admin_id=current_user.id
        )
        db.session.add(rec)
        db.session.commit()

        log_activity("CSV_DATASET_IMPORT", "Datasets", f"Imported {imported_count} records from {filename}")
        flash(f"Successfully imported {imported_count} records into {dataset_type}!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Failed to import dataset: {str(e)}", "danger")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return redirect(url_for('datasets.index'))

@datasets_bp.route('/generate-synthetic', methods=['POST'])
@login_required
def generate_synthetic():
    """Trigger the idempotent 5,000 patients, 1,000 appts generator"""
    try:
        summary = generate_full_synthetic_dataset()
        flash(
            f"Synthetic Demonstration Data generated successfully! Created: "
            f"{summary['patients']} Patients, {summary['appointments']} Appointments, "
            f"{summary['doctors']} Doctors, {summary['beds']} Beds, {summary['departments']} Departments.",
            "success"
        )
    except Exception as e:
        flash(f"Error during synthetic data generation: {str(e)}", "danger")

    return redirect(url_for('datasets.index'))

@datasets_bp.route('/template/<entity>')
@login_required
def download_template(entity):
    """Download clean sample CSV templates"""
    templates = {
        'patients': "full_name,age,gender,phone,email,address,blood_group,emergency_contact\nJohn Doe,42,Male,+1 555-0123,john.doe@example.com,123 Main St,A+,+1 555-9876\nJane Smith,34,Female,+1 555-0124,jane.smith@example.com,456 Oak Ave,O+,+1 555-9875\n",
        'doctors': "name,qualification,specialization,phone,email,experience_years\nRobert Chen,MD (Cardiology),Interventional Cardiology,+1 555-0201,robert.chen@apexhealth.org,12\nAlice Wong,MS (Ortho),Joint Replacement,+1 555-0202,alice.wong@apexhealth.org,9\n",
        'departments': "name,code,head_of_department,floor,phone\nCardiology,CARD,Dr. Arthur Vance,Floor 3 East,ext. 301\nNeurology,NEUR,Dr. Eleanor Vance,Floor 4 West,ext. 402\n",
        'beds': "bed_number,ward,bed_type\n101,Cardiology Ward A,General Ward\nICU-01,Trauma ICU,ICU\n"
    }

    content = templates.get(entity.lower())
    if not content:
        flash('Invalid template requested.', 'warning')
        return redirect(url_for('datasets.index'))

    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=template_{entity}.csv"}
    )
