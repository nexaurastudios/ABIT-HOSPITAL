import os
from datetime import datetime
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, login_manager, migrate, csrf
from app.models.auth import Admin
from app.models.settings import HospitalSetting
from app.models.notification import Notification

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    # Register Route Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.patients import patients_bp
    from app.routes.doctors import doctors_bp
    from app.routes.departments import departments_bp
    from app.routes.appointments import appointments_bp
    from app.routes.waiting_time import waiting_time_bp
    from app.routes.beds import beds_bp
    from app.routes.admissions import admissions_bp
    from app.routes.analytics import analytics_bp
    from app.routes.ml import ml_bp
    from app.routes.datasets import datasets_bp
    from app.routes.reports import reports_bp
    from app.routes.notifications import notifications_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(waiting_time_bp)
    app.register_blueprint(beds_bp)
    app.register_blueprint(admissions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(settings_bp)

    # Context processors for global UI elements (hospital name, notification badge)
    @app.context_processor
    def inject_global_data():
        try:
            settings = HospitalSetting.get_settings()
            unread_count = Notification.query.filter_by(is_read=False).count()
            top_notifs = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
        except Exception:
            settings = None
            unread_count = 0
            top_notifs = []

        return {
            'hospital_settings': settings,
            'unread_notifications_count': unread_count,
            'top_notifications': top_notifs,
            'current_year': datetime.utcnow().year,
            'now': datetime.utcnow()
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
