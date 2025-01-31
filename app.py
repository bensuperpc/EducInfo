import os
from datetime import datetime  # Ajout de l'import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, abort, g, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from extensions import db, csrf, login_manager, logger
from models import User, Absence, WidgetConfig, Event, SiteConfig, WeatherConfig
from forms import LoginForm, AbsenceForm, WidgetConfigForm, EventForm, ChangePasswordForm, SiteConfigForm, WeatherConfigForm
import requests

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def initialize_database():
    """Initialise la base de données avec les configurations par défaut"""
    try:
        with app.app_context():
            # Créer toutes les tables
            db.create_all()
            
            # Créer l'admin par défaut si nécessaire
            if not User.query.filter_by(identifiant='admin').first():
                admin = User(identifiant='admin', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                
            # S'assurer que les configurations existent
            if not WeatherConfig.query.first():
                db.session.add(WeatherConfig())
            if not SiteConfig.query.first():
                db.session.add(SiteConfig())
            if not WidgetConfig.query.first():
                db.session.add(WidgetConfig())
                
            db.session.commit()
            logger.info('Base de données initialisée avec succès')
            
    except Exception as e:
        logger.error(f"Erreur d'initialisation: {e}")
        db.session.rollback()
        raise

### ROUTES

@app.context_processor
def utility_processor():
    """Ajoute des fonctions utilitaires aux templates"""
    def get_absence_status(absence, jour):
        """Récupère le statut d'absence pour un jour donné"""
        return getattr(absence, jour, False)
    
    return {
        'get_absence_status': get_absence_status
    }

@app.context_processor
def inject_config():
    """Injecte toutes les configurations nécessaires dans tous les templates"""
    return {
        'site_config': SiteConfig.get_config(),
        'weather_city': app.config['WEATHER_CITY'],
        'current_datetime': datetime.now()
    }

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

@app.route('/')
def home():
    try:
        # Récupération des configurations avec gestion d'erreurs
        config = WidgetConfig.query.first()
        if not config:
            config = WidgetConfig()
            db.session.add(config)
            db.session.commit()
            
        # Récupération des absences et événements
        absences = Absence.query.all()
        events = Event.get_upcoming_events()
        
        # Vérification des données avant le rendu
        logger.info(f'Chargement page d\'accueil: {len(absences)} absences, {len(events)} événements')
        
        return render_template('home.html', 
                             config=config, 
                             absences=absences, 
                             events=events)
    except Exception as e:
        logger.error(f'Erreur page d\'accueil: {str(e)}')
        # Pour le développement, afficher l'erreur complète
        return f"Erreur : {str(e)}", 500

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(identifiant=form.identifiant.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants invalides', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin-dashboard', methods=['GET','POST'])
@login_required
def admin_dashboard():
    forms = {
        'absence_form': AbsenceForm(),
        'event_form': EventForm(),
        'password_form': ChangePasswordForm(),
        'site_form': SiteConfigForm(),
        'weather_form': WeatherConfigForm(),
        'widget_form': WidgetConfigForm()
    }
    
    configs = {
        'widget': WidgetConfig.query.first() or WidgetConfig(),
        'site': SiteConfig.get_config(),
        'weather': WeatherConfig.get_config()
    }
    
    # Pré-remplir les formulaires
    if not forms['widget_form'].is_submitted():
        forms['widget_form'] = WidgetConfigForm(obj=configs['widget'])
    if not forms['site_form'].is_submitted():
        forms['site_form'].site_name.data = configs['site'].site_name
    if not forms['weather_form'].is_submitted():
        forms['weather_form'].api_key.data = configs['weather'].api_key
        forms['weather_form'].city.data = configs['weather'].city
        forms['weather_form'].show_weather.data = configs['weather'].show_weather

    if request.method == 'POST':
        form_handlers = {
            'delete_absence': handle_absence_deletion,
            'submit_widget': handle_widget_update,
            'submit_absence': handle_absence_update,
            'submit_password': handle_password_change,
            'submit_event': handle_event_creation,
            'delete_event': handle_event_deletion,
            'submit_site': handle_site_config,
            'submit_weather': handle_weather_config
        }

        for action, handler in form_handlers.items():
            if action in request.form:
                return handler(request, forms, configs)

    return render_template('admin_dashboard.html',
                         absences=Absence.query.all(),
                         widget_config=configs['widget'],
                         future_events=Event.get_upcoming_events(),
                         **forms)

# Handlers pour les différentes actions
def handle_absence_deletion(request, forms, configs):
    absence_id = request.form.get('delete_absence')
    absence = Absence.query.get(absence_id)
    if absence:
        db.session.delete(absence)
        db.session.commit()
        flash('Absence supprimée avec succès', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_widget_update(request, forms, configs):
    if forms['widget_form'].validate_on_submit():
        widget_config = configs['widget']
        widget_config.show_menu_cantine = forms['widget_form'].show_menu_cantine.data
        widget_config.menu_cantine = forms['widget_form'].menu_cantine.data
        db.session.commit()
        flash('Configuration widgets mise à jour', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_absence_update(request, forms, configs):
    """Gère l'ajout ou la mise à jour d'une absence"""
    if forms['absence_form'].validate_on_submit():
        professeur = forms['absence_form'].professeur.data
        jours = request.form.getlist('jours')
        
        # Recherche ou création d'une absence
        absence = Absence.query.filter_by(professeur=professeur).first()
        if not absence:
            absence = Absence(professeur=professeur)
            db.session.add(absence)
            flash(f'Nouvelle absence ajoutée pour {professeur}', 'success')
        else:
            flash(f'Absence mise à jour pour {professeur}', 'info')

        # Mise à jour des jours
        absence.lundi = 'lundi' in jours
        absence.mardi = 'mardi' in jours
        absence.mercredi = 'mercredi' in jours
        absence.jeudi = 'jeudi' in jours
        absence.vendredi = 'vendredi' in jours

        db.session.commit()
    return redirect(url_for('admin_dashboard'))

def handle_weather_config(request, forms, configs):
    if forms['weather_form'].validate_on_submit():
        weather_config = configs['weather']
        weather_config.api_key = forms['weather_form'].api_key.data
        weather_config.city = forms['weather_form'].city.data
        weather_config.show_weather = forms['weather_form'].show_weather.data
        db.session.commit()
        
        app.config['WEATHER_API_KEY'] = weather_config.api_key
        app.config['WEATHER_CITY'] = weather_config.city
        
        flash('Configuration météo mise à jour', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_password_change(request, forms, configs):
    """Gère le changement de mot de passe"""
    if forms['password_form'].validate_on_submit():
        user = User.query.filter_by(identifiant=current_user.identifiant).first()
        if user and user.check_password(forms['password_form'].current_password.data):
            user.set_password(forms['password_form'].new_password.data)
            db.session.commit()
            flash('Mot de passe modifié avec succès', 'success')
            return redirect(url_for('logout'))
        else:
            flash('Mot de passe actuel incorrect', 'error')
    return redirect(url_for('admin_dashboard'))

def handle_event_creation(request, forms, configs):
    """Gère la création d'un événement"""
    if forms['event_form'].validate_on_submit():
        evt = Event(
            title=forms['event_form'].title.data,
            date=forms['event_form'].date.data,
            description=forms['event_form'].description.data
        )
        db.session.add(evt)
        db.session.commit()
        flash('Événement ajouté', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_event_deletion(request, forms, configs):
    """Gère la suppression d'un événement"""
    event_id = request.form.get('delete_event')
    evt = Event.query.get(event_id)
    if evt:
        db.session.delete(evt)
        db.session.commit()
        flash('Événement supprimé', 'warning')
    return redirect(url_for('admin_dashboard'))

def handle_site_config(request, forms, configs):
    """Gère la configuration du site"""
    if forms['site_form'].validate_on_submit():
        site_config = configs['site']
        site_config.site_name = forms['site_form'].site_name.data
        db.session.commit()
        flash('Nom de l\'établissement mis à jour', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/get_updates')
def get_updates():
    try:
        widget_config = WidgetConfig.query.first()
        if not widget_config:
            widget_config = WidgetConfig()
            db.session.add(widget_config)
            db.session.commit()

        config_data = {
            'show_menu_cantine': widget_config.show_menu_cantine,
            'menu_cantine': widget_config.menu_cantine
        }

        absences = [{
            'professeur': a.professeur,
            'lundi': a.lundi,
            'mardi': a.mardi,
            'mercredi': a.mercredi,
            'jeudi': a.jeudi,
            'vendredi': a.vendredi
        } for a in Absence.query.all()]

        events = [{
            'title': e.title,
            'date': e.date.strftime('%d/%m/%Y'),
            'description': e.description
        } for e in Event.get_upcoming_events()]

        return jsonify({
            'absences': absences,
            'events': events,
            'widget_config': config_data
        })
    except Exception as e:
        logger.error(f'Error in get_updates: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/get_weather')
def get_weather():
    """Route pour obtenir les données météo actuelles"""
    try:
        weather_config = WeatherConfig.get_config()
        
        if not weather_config.show_weather:
            return jsonify({'error': 'Météo désactivée'}), 200
            
        url = f"https://api.openweathermap.org/data/2.5/weather?q={weather_config.city}&appid={weather_config.api_key}&units=metric&lang=fr"
        
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            return jsonify({
                'temp': round(data['main']['temp']),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            })
        else:
            return jsonify({'error': 'Données météo non disponibles'}), 500

    except Exception as e:
        logger.error(f'Erreur météo: {e}')
        return jsonify({'error': str(e)}), 500

def get_weather_description(weather_code):
    """Convertit le code météo de Météo France en description"""
    weather_codes = {
        0: "Soleil",
        1: "Peu nuageux",
        2: "Ciel voilé",
        3: "Nuageux",
        4: "Très nuageux",
        5: "Couvert",
        6: "Brouillard",
        7: "Brouillard givrant",
        10: "Pluie faible",
        11: "Pluie modérée",
        12: "Pluie forte",
        13: "Neige faible",
        14: "Neige modérée",
        15: "Neige forte",
    }
    return weather_codes.get(weather_code, "Météo indéterminée")

def get_weather_icon(weather_code):
    """Convertit le code météo en emoji"""
    weather_icons = {
        0: "☀️",
        1: "🌤️",
        2: "⛅",
        3: "☁️",
        4: "☁️",
        5: "☁️",
        6: "🌫️",
        7: "🌫️",
        10: "🌦️",
        11: "🌧️",
        12: "⛈️",
        13: "🌨️",
        14: "🌨️",
        15: "🌨️",
    }
    return weather_icons.get(weather_code, "🌡️")

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True) 