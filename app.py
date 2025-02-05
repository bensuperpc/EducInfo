import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, abort, g, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from extensions import db, csrf, login_manager, logger
<<<<<<< Updated upstream
from models import User, Absence, WidgetConfig, Event, SiteConfig, WeatherConfig, TransportConfig
from forms import (LoginForm, AbsenceForm, WidgetConfigForm, EventForm, 
                  ChangePasswordForm, SiteConfigForm, WeatherConfigForm, 
                  TransportConfigForm, StopPointForm)  # Ajout de StopPointForm ici
=======
from models import User, Absence, WidgetConfig, Event, SiteConfig, WeatherConfig
from forms import (LoginForm, AbsenceForm, WidgetConfigForm, EventForm, ChangePasswordForm,
                   SiteConfigForm, WeatherConfigForm)
>>>>>>> Stashed changes
import requests
from services.cts_service import CTSService
from services.weather_service import WeatherService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialisation des extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Création des services
    app.cts_service = CTSService(
        base_url=app.config['CTS_BASE_URL'],
        timeout=app.config['CTS_API_TIMEOUT']
    )
    app.weather_service = WeatherService(timeout=10)
    
    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def initialize_database():
    """Initialise la base de données avec les configurations par défaut"""
    try:
        with app.app_context():
            db.create_all()
            if not User.query.filter_by(identifiant='admin').first():
                admin = User(identifiant='admin', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            if not WeatherConfig.query.first():
                db.session.add(WeatherConfig())
            if not SiteConfig.query.first():
                db.session.add(SiteConfig())
            if not WidgetConfig.query.first():
                db.session.add(WidgetConfig())
<<<<<<< Updated upstream
            if not TransportConfig.query.first():  # Ajout de la config transport
                db.session.add(TransportConfig())
                
=======
>>>>>>> Stashed changes
            db.session.commit()
            logger.info('Base de données initialisée avec succès')
    except Exception as e:
        logger.error(f"Erreur d'initialisation: {e}")
        db.session.rollback()
        raise

@app.context_processor
def utility_processor():
    def get_absence_status(absence, jour):
        return getattr(absence, jour, False)
    return {'get_absence_status': get_absence_status}

@app.context_processor
def inject_config():
    return {
        'site_config': SiteConfig.get_config(),
        'weather_city': app.config['WEATHER_CITY'],
        'current_datetime': datetime.now(),
        'transport_config': TransportConfig.get_config()  # Ajout de cette ligne
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
<<<<<<< Updated upstream
        # Récupération des configurations
        config = WidgetConfig.query.first() or WidgetConfig()
        transport_config = TransportConfig.query.first() or TransportConfig()  # Ajout ici
        
        # Récupérer les informations de transport si activé
        transport_stops = []
        if transport_config and transport_config.enabled:
            for stop in transport_config.stop_points:
                info = get_cts_stop_info(stop['code'])
                if info and 'MonitoredStopVisit' in info:
                    passages = []
                    for visit in info['MonitoredStopVisit']:
                        journey = visit.get('MonitoredVehicleJourney', {})
                        passages.append({
                            'line': journey.get('PublishedLineName'),
                            'destination': journey.get('DestinationName'),
                            'time': journey.get('MonitoredCall', {}).get('ExpectedDepartureTime')
                        })
                    transport_stops.append({
                        'name': stop['name'],
                        'passages': passages
                    })
        
        # Récupération des autres données
=======
        config = WidgetConfig.query.first() or WidgetConfig()
>>>>>>> Stashed changes
        absences = Absence.query.all()
        events = Event.get_upcoming_events(days=30)  # Limiter aux 30 prochains jours
        
<<<<<<< Updated upstream
        return render_template('home.html', 
                             config=config,
                             transport_config=transport_config,  # Ajout ici
                             transport_stops=transport_stops,    # Ajout ici
                             absences=absences, 
                             events=events)
                             
=======
        cts_arrivals = []
        if config.show_transports and config.cts_stop_code:
            try:
                api_token = config.cts_api_token or app.config.get('CTS_API_TOKEN')
                if not api_token:
                    flash("Token API CTS non configuré", "warning")
                else:
                    cts_arrivals = app.cts_service.get_stop_monitoring(
                        config.cts_stop_code,
                        api_token,
                        config.cts_vehicle_mode
                    )
                    
                    if not cts_arrivals:
                        flash("Aucun passage prévu dans les 30 prochaines minutes", "info")
                        
            except Exception as e:
                logger.error(f"Erreur CTS dans home: {e}")
                flash("Erreur lors de la récupération des horaires", "error")
                cts_arrivals = []
                
        return render_template('home.html',
                             config=config,
                             absences=absences,
                             events=events,
                             cts_arrivals=cts_arrivals)
>>>>>>> Stashed changes
    except Exception as e:
        logger.error(f'Erreur page d\'accueil: {str(e)}')
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
        'widget_form': WidgetConfigForm(),
        'transport_form': TransportConfigForm(),  # Ajout du formulaire transport
        'stop_form': StopPointForm()
    }
    
    configs = {
        'widget': WidgetConfig.query.first() or WidgetConfig(),
        'site': SiteConfig.get_config(),
        'weather': WeatherConfig.get_config(),
        'transport': TransportConfig.get_config()  # Ajout de la config transport
    }
<<<<<<< Updated upstream

    # Pré-remplir les formulaires
=======
    
    # Pré-remplissage des formulaires
>>>>>>> Stashed changes
    if not forms['widget_form'].is_submitted():
        forms['widget_form'] = WidgetConfigForm(obj=configs['widget'])
    if not forms['site_form'].is_submitted():
        forms['site_form'].site_name.data = configs['site'].site_name
    if not forms['weather_form'].is_submitted():
        forms['weather_form'].api_key.data = configs['weather'].api_key
        forms['weather_form'].city.data = configs['weather'].city
        forms['weather_form'].show_weather.data = configs['weather'].show_weather
    if not forms['transport_form'].is_submitted():
        forms['transport_form'] = TransportConfigForm(obj=configs['transport'])

    # Traitement du POST
    if request.method == 'POST':
        # Traitement du formulaire de configuration des widgets
        if 'submit_widget' in request.form:
            if forms['widget_form'].validate_on_submit():
                widget_config = configs['widget']
                widget_config.show_menu_cantine = forms['widget_form'].show_menu_cantine.data
                widget_config.menu_entree = forms['widget_form'].menu_entree.data
                widget_config.menu_plat = forms['widget_form'].menu_plat.data
                widget_config.menu_dessert = forms['widget_form'].menu_dessert.data
                widget_config.show_transports = forms['widget_form'].show_transports.data
                widget_config.cts_stop_code = forms['widget_form'].cts_stop_code.data.strip()
                widget_config.cts_vehicle_mode = forms['widget_form'].cts_vehicle_mode.data
                widget_config.cts_api_token = forms['widget_form'].cts_api_token.data.strip()
                widget_config.cts_stop_name = forms['widget_form'].cts_stop_name.data
                db.session.commit()
                flash('Configuration widgets mise à jour', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # Traitement des autres formulaires (absences, événements, site, météo, etc.)
        form_handlers = {
            'delete_absence': handle_absence_deletion,
            'submit_absence': handle_absence_update,
            'submit_password': handle_password_change,
            'submit_event': handle_event_creation,
            'delete_event': handle_event_deletion,
            'submit_site': handle_site_config,
            'submit_weather': handle_weather_config,
            'submit_transport': handle_transport_config,  # Ajout du handler transport
            'submit_stop': handle_stop_point_add,
            'delete_stop': handle_stop_point_delete
        }
        for action, handler in form_handlers.items():
            if action in request.form:
                return handler(request, forms, configs)
    
    return render_template(
        'admin_dashboard.html',
        absences=Absence.query.all(),
        widget_config=configs['widget'],
        future_events=Event.get_upcoming_events(),
        **forms
    )

<<<<<<< Updated upstream
    return render_template('admin_dashboard.html',
                         absences=Absence.query.all(),
                         widget_config=configs['widget'],
                         transport_config=configs['transport'],  # Ajout de cette ligne
                         future_events=Event.get_upcoming_events(),
                         **forms)

# Handlers pour les différentes actions
=======
>>>>>>> Stashed changes
def handle_absence_deletion(request, forms, configs):
    absence_id = request.form.get('delete_absence')
    absence = Absence.query.get(absence_id)
    if absence:
        db.session.delete(absence)
        db.session.commit()
        flash('Absence supprimée avec succès', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_absence_update(request, forms, configs):
    if forms['absence_form'].validate_on_submit():
        professeur = forms['absence_form'].professeur.data
        jours = request.form.getlist('jours')
        absence = Absence.query.filter_by(professeur=professeur).first()
        if not absence:
            absence = Absence(professeur=professeur)
            db.session.add(absence)
            flash(f'Nouvelle absence ajoutée pour {professeur}', 'success')
        else:
            flash(f'Absence mise à jour pour {professeur}', 'info')
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
    if forms['event_form'].validate_on_submit():
        try:
            evt = Event(
                title=forms['event_form'].title.data,
                date=forms['event_form'].date.data,
                description=forms['event_form'].description.data.strip() if forms['event_form'].description.data else ""
            )
            db.session.add(evt)
            db.session.commit()
            flash('Événement ajouté avec succès', 'success')
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'événement: {str(e)}")
            db.session.rollback()
            flash('Erreur lors de la création de l\'événement', 'error')
    else:
        for field, errors in forms['event_form'].errors.items():
            for error in errors:
                flash(f'Erreur: {error}', 'error')
    return redirect(url_for('admin_dashboard'))

def handle_event_deletion(request, forms, configs):
    event_id = request.form.get('delete_event')
    evt = Event.query.get(event_id)
    if evt:
        db.session.delete(evt)
        db.session.commit()
        flash('Événement supprimé', 'warning')
    return redirect(url_for('admin_dashboard'))

def handle_site_config(request, forms, configs):
    if forms['site_form'].validate_on_submit():
        site_config = configs['site']
        site_config.site_name = forms['site_form'].site_name.data
        db.session.commit()
        flash('Nom de l\'établissement mis à jour', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_transport_config(request, forms, configs):
    """Gère la configuration des transports"""
    if forms['transport_form'].validate_on_submit():
        transport_config = configs['transport']
        transport_config.enabled = forms['transport_form'].enabled.data
        transport_config.api_token = forms['transport_form'].api_token.data
        transport_config.show_in_banner = forms['transport_form'].show_in_banner.data
        db.session.commit()
        flash('Configuration des transports mise à jour', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_stop_point_add(request, forms, configs):
    """Gère l'ajout d'un arrêt"""
    if forms['stop_form'].validate_on_submit():
        transport_config = configs['transport']
        new_stop = {
            'code': forms['stop_form'].code.data,
            'name': forms['stop_form'].name.data
        }
        if not transport_config.stop_points:
            transport_config.stop_points = []
        transport_config.stop_points.append(new_stop)
        db.session.commit()
        flash('Arrêt ajouté avec succès', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_stop_point_delete(request, forms, configs):
    """Gère la suppression d'un arrêt"""
    index = int(request.form.get('delete_stop'))
    transport_config = configs['transport']
    if 0 <= index < len(transport_config.stop_points):
        transport_config.stop_points.pop(index)
        db.session.commit()
        flash('Arrêt supprimé', 'success')
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
    try:
        weather_config = WeatherConfig.get_config()
        if not weather_config.show_weather:
            return jsonify({'error': 'Météo désactivée'}), 200

        weather_data = app.weather_service.get_current_weather(
            city=weather_config.city,
            api_key=weather_config.api_key
        )

        if weather_data:
            return jsonify(weather_data)
        else:
            return jsonify({'error': 'Données météo non disponibles'}), 500
            
    except Exception as e:
        logger.error(f'Erreur météo: {e}')
        return jsonify({'error': str(e)}), 500

<<<<<<< Updated upstream
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

def get_cts_stop_info(stop_code):
    """Obtient les informations de passage en temps réel pour un arrêt donné"""
    config = TransportConfig.get_config()
    if not config.enabled or not config.api_token:
        return None
        
    headers = {'Authorization': f'Basic {config.api_token}'}
    url = f"https://api.cts-strasbourg.eu/v1/siri/2.0/stop-monitoring"
    
    params = {
        'MonitoringRef': stop_code,
        'MaximumStopVisits': 3,
        'MinimumStopVisitsPerLine': 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('ServiceDelivery', {}).get('StopMonitoringDelivery', [{}])[0]
        return None
    except Exception as e:
        logger.error(f"Erreur CTS: {str(e)}")
        return None

@app.route('/get_transport_updates')
def get_transport_updates():
    """Endpoint API pour obtenir les mises à jour des transports"""
    config = TransportConfig.get_config()
    if not config.enabled:
        return jsonify({'enabled': False})
        
    stops_data = []
    for stop in config.stop_points:
        info = get_cts_stop_info(stop['code'])
        if info and 'MonitoredStopVisit' in info:
            passages = []
            for visit in info['MonitoredStopVisit']:
                journey = visit.get('MonitoredVehicleJourney', {})
                passages.append({
                    'line': journey.get('PublishedLineName'),
                    'destination': journey.get('DestinationName'),
                    'time': journey.get('MonitoredCall', {}).get('ExpectedDepartureTime')
                })
            stops_data.append({
                'name': stop['name'],
                'passages': passages
            })
            
    return jsonify({
        'enabled': True,
        'stops': stops_data
    })

@app.template_filter('formattime')
def formattime_filter(value):
    """Convertit une chaîne ISO en heure locale au format HH:MM"""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except Exception as e:
        logger.error(f"Erreur formatage heure: {e}")
        return value
=======
if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True)
>>>>>>> Stashed changes
