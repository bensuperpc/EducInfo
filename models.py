from flask_login import UserMixin
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    identifiant = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    @property
    def is_admin(self):
        return self.role == 'admin'

class Absence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professeur = db.Column(db.String(100), nullable=False)
    lundi = db.Column(db.Boolean, default=False)
    mardi = db.Column(db.Boolean, default=False)
    mercredi = db.Column(db.Boolean, default=False)
    jeudi = db.Column(db.Boolean, default=False)
    vendredi = db.Column(db.Boolean, default=False)

class WidgetConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    show_menu_cantine = db.Column(db.Boolean, default=False)
    menu_entree = db.Column(db.String(200), default="")
    menu_plat = db.Column(db.String(200), default="")
    menu_dessert = db.Column(db.String(200), default="")
    show_transports = db.Column(db.Boolean, default=False)
    cts_stop_code = db.Column(db.String(20))
    cts_vehicle_mode = db.Column(db.String(20), default="undefined")
    cts_api_token = db.Column(db.String(64))
    cts_stop_name = db.Column(db.String(100))  # Nouveau champ pour le nom personnalisé

    @staticmethod
    def get_config():
        return WidgetConfig.query.first() or WidgetConfig()

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='EducInfo')
    
    @staticmethod
    def get_config():
        config = SiteConfig.query.first()
        if not config:
            config = SiteConfig()
            db.session.add(config)
            db.session.commit()
        return config

class WeatherConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(32), nullable=False, default='0b0b32c21c0e7a28f8dc6711e0c2e86b')
    city = db.Column(db.String(100), nullable=False, default='Paris')
    show_weather = db.Column(db.Boolean, default=True)
    
    @staticmethod
    def get_config():
        config = WeatherConfig.query.first()
        if not config:
            config = WeatherConfig()
            db.session.add(config)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise
        return config

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Ajout d'un timestamp de création

    def is_future(self):
        return self.date >= date.today()

    @staticmethod
    def get_upcoming_events(days=30):
        today = date.today()
        future_date = today + timedelta(days=days)
        return Event.query.filter(
            Event.date >= today,
            Event.date <= future_date
        ).order_by(Event.date).all()

class TransportConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=False)
    api_token = db.Column(db.String(100), nullable=True)
    stop_points = db.Column(db.JSON, default=list)  # Liste des arrêts à surveiller
    show_in_banner = db.Column(db.Boolean, default=False)  # Afficher dans la bannière du bas
    
    @staticmethod
    def get_config():
        config = TransportConfig.query.first()
        if not config:
            config = TransportConfig()
            db.session.add(config)
            db.session.commit()
        return config