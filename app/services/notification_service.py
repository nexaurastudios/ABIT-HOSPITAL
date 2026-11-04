from datetime import datetime, timedelta
from app.extensions import db
from app.models.notification import Notification
from app.models.bed import Bed
from app.models.visit import Visit
from app.models.settings import HospitalSetting

def create_notification(title, message, category='info', related_url=None):
    """Create a persistent notification in the database"""
    try:
        # Check if identical unread notification exists within last 30 minutes to avoid duplicates
        half_hour_ago = datetime.utcnow() - timedelta(minutes=30)
        existing = Notification.query.filter(
            Notification.title == title,
            Notification.is_read == False,
            Notification.created_at >= half_hour_ago
        ).first()

        if not existing:
            note = Notification(
                title=title,
                message=message,
                category=category,
                related_url=related_url
            )
            db.session.add(note)
            db.session.commit()
            return note
        return existing
    except Exception as e:
        db.session.rollback()
        print(f"[Notification Error] {e}")
        return None

def check_and_trigger_alerts():
    """Check hospital capacity & waiting times and create notifications if thresholds exceeded"""
    try:
        settings = HospitalSetting.get_settings()
        
        # 1. Check Bed Occupancy Threshold
        total_beds = Bed.query.count()
        if total_beds > 0:
            occupied_beds = Bed.query.filter_by(occupancy_status='Occupied').count()
            occupancy_pct = (occupied_beds / total_beds) * 100
            
            if occupancy_pct >= settings.bed_capacity_alert_threshold:
                create_notification(
                    title="High Bed Occupancy Alert",
                    message=f"Hospital bed occupancy reached {occupancy_pct:.1f}% ({occupied_beds}/{total_beds} beds occupied), exceeding {settings.bed_capacity_alert_threshold}% threshold.",
                    category="danger",
                    related_url="/beds"
                )

        # 2. Check Average Patient Waiting Time for today
        today = datetime.utcnow().date()
        today_visits = Visit.query.filter(
            Visit.visit_date == today,
            Visit.waiting_time_minutes.isnot(None)
        ).all()
        
        if today_visits:
            avg_wait = sum(v.waiting_time_minutes for v in today_visits) / len(today_visits)
            if avg_wait >= settings.waiting_time_alert_threshold:
                create_notification(
                    title="Elevated Patient Waiting Time",
                    message=f"Today's average waiting time is {avg_wait:.1f} minutes, which exceeds the target threshold of {settings.waiting_time_alert_threshold} minutes.",
                    category="warning",
                    related_url="/waiting-time"
                )
    except Exception as e:
        print(f"[Alert Check Error] {e}")
