from flask import request
from flask_login import current_user
from app.extensions import db
from app.models.notification import ActivityLog

def log_activity(action, module, details=None, record_id=None):
    """Log an administrative or system action into the database"""
    try:
        admin_id = current_user.id if (current_user and current_user.is_authenticated) else None
        admin_email = current_user.email if (current_user and current_user.is_authenticated) else "system@hospital.internal"
        
        ip_addr = request.remote_addr if request else "127.0.0.1"
        
        log_entry = ActivityLog(
            admin_id=admin_id,
            admin_email=admin_email,
            action=action,
            module=module,
            details=str(details) if details else "",
            record_id=str(record_id) if record_id else None,
            ip_address=ip_addr
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        # Avoid breaking parent transactions on logging failure
        db.session.rollback()
        print(f"[ActivityLog Error] Failed to log activity: {e}")
