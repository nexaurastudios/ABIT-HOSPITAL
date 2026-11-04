from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.models.bed import Bed, Admission
from app.models.department import Department
from app.models.patient import Patient
from app.services.activity_logger import log_activity
from app.services.notification_service import check_and_trigger_alerts

beds_bp = Blueprint('beds', __name__, url_prefix='/beds')

@beds_bp.route('/')
@login_required
def list_beds():
    check_and_trigger_alerts()

    type_filter = request.args.get('type', '').strip()
    status_filter = request.args.get('status', '').strip()
    dept_filter = request.args.get('department_id', type=int)

    query = Bed.query

    if type_filter:
        query = query.filter(Bed.bed_type == type_filter)
    if status_filter:
        query = query.filter(Bed.occupancy_status == status_filter)
    if dept_filter:
        query = query.filter(Bed.department_id == dept_filter)

    beds = query.order_by(Bed.department_id.asc(), Bed.bed_number.asc()).all()
    departments = Department.query.filter_by(is_active=True).all()

    # Dynamic metrics
    total_beds = Bed.query.count()
    occupied_beds = Bed.query.filter_by(occupancy_status='Occupied').count()
    available_beds = Bed.query.filter_by(occupancy_status='Available').count()
    reserved_beds = Bed.query.filter_by(occupancy_status='Reserved').count()
    maintenance_beds = Bed.query.filter_by(occupancy_status='Maintenance').count()
    occupancy_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    # Department-wise breakdown
    dept_breakdown = db.session.query(
        Department.name,
        func.count(Bed.id),
        func.sum(db.case((Bed.occupancy_status == 'Occupied', 1), else_=0))
    ).join(Bed, Bed.department_id == Department.id)\
     .group_by(Department.name).all()

    dept_occupancy = []
    for d_name, total, occ in dept_breakdown:
        occ_int = int(occ or 0)
        pct = round((occ_int / total * 100), 1) if total > 0 else 0.0
        dept_occupancy.append({
            'name': d_name,
            'total': total,
            'occupied': occ_int,
            'rate': pct
        })

    metrics = {
        'total': total_beds,
        'occupied': occupied_beds,
        'available': available_beds,
        'reserved': reserved_beds,
        'maintenance': maintenance_beds,
        'occupancy_pct': occupancy_pct
    }

    return render_template(
        'beds/list.html',
        beds=beds,
        departments=departments,
        dept_occupancy=dept_occupancy,
        metrics=metrics,
        type_filter=type_filter,
        status_filter=status_filter,
        dept_filter=dept_filter
    )

@beds_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_bed():
    if request.method == 'POST':
        bed_number = request.form.get('bed_number', '').strip()
        dept_id = request.form.get('department_id', type=int)
        ward = request.form.get('ward', '').strip()
        bed_type = request.form.get('bed_type', 'General Ward')

        if not bed_number or not dept_id or not ward:
            flash('Bed Number, Department, and Ward are required.', 'danger')
            return redirect(url_for('beds.create_bed'))

        prefix = bed_type[:3].upper()
        bed_id = f"BED-{prefix}-{bed_number}"

        if Bed.query.filter_by(bed_id=bed_id).first():
            flash(f"A bed with ID '{bed_id}' already exists in the system.", 'danger')
            return redirect(url_for('beds.create_bed'))

        bed = Bed(
            bed_id=bed_id,
            bed_number=bed_number,
            department_id=dept_id,
            ward=ward,
            bed_type=bed_type,
            occupancy_status='Available',
            is_demo=False
        )

        db.session.add(bed)
        db.session.commit()

        log_activity("CREATE_BED", "Beds", f"Added bed {bed_id} in {ward}", record_id=bed_id)
        flash(f"Bed {bed_id} added successfully.", "success")
        return redirect(url_for('beds.list_beds'))

    departments = Department.query.filter_by(is_active=True).all()
    return render_template('beds/form.html', departments=departments, bed=None)

@beds_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    bed = Bed.query.get_or_404(id)
    new_status = request.form.get('status')

    if bed.occupancy_status == 'Occupied' and new_status != 'Occupied':
        flash('Cannot change status of an occupied bed directly. Please discharge or transfer the assigned patient in the Admissions module.', 'danger')
        return redirect(url_for('beds.list_beds'))

    if new_status in ['Available', 'Reserved', 'Maintenance']:
        bed.occupancy_status = new_status
        db.session.commit()
        log_activity("BED_STATUS_CHANGE", "Beds", f"Changed bed {bed.bed_id} status to {new_status}", record_id=bed.bed_id)
        flash(f"Bed {bed.bed_id} status updated to {new_status}.", "info")

    return redirect(url_for('beds.list_beds'))

@beds_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_bed(id):
    bed = Bed.query.get_or_404(id)
    if bed.occupancy_status == 'Occupied':
        flash(f"Cannot delete Bed {bed.bed_id} while it is currently occupied by a patient.", 'danger')
        return redirect(url_for('beds.list_beds'))

    bed_code = bed.bed_id
    db.session.delete(bed)
    db.session.commit()
    log_activity("DELETE_BED", "Beds", f"Deleted bed {bed_code}", record_id=bed_code)
    flash(f"Bed {bed_code} deleted successfully.", "info")
    return redirect(url_for('beds.list_beds'))
