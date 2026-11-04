from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.notification import Notification, ActivityLog
from app.services.activity_logger import log_activity

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(100).all()
    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/mark-read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)
    notif.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('notifications.index'))

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(request.referrer or url_for('notifications.index'))

@notifications_bp.route('/activity-logs')
@login_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    module_filter = request.args.get('module', '').strip()

    query = ActivityLog.query
    if module_filter:
        query = query.filter(ActivityLog.module == module_filter)

    pagination = query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=20, error_out=False)

    modules = db.session.query(ActivityLog.module).distinct().all()
    module_list = [m[0] for m in modules if m[0]]

    return render_template(
        'notifications/activity_logs.html',
        pagination=pagination,
        logs=pagination.items,
        modules=module_list,
        module_filter=module_filter
    )
