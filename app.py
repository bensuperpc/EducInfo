from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from config import Config
from extensions import db, csrf, login_manager, logger
from models import User, Absence, WidgetConfig, Event, SiteConfig, WeatherConfig, MenuItem
from forms import (LoginForm, AbsenceForm, WidgetConfigForm, EventForm, 
                  ChangePasswordForm, SiteConfigForm, WeatherConfigForm, CTSForm, MenuItemForm)
import requests

app = Flask(__name__)
app.config.from_object(Config)

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
            # Vérifie si les tables existent déjà
            db.create_all()
            
            # Initialisation de l'utilisateur admin
            admin = User.query.filter_by(identifiant='admin').first()
            if not admin:
                admin = User(identifiant='admin', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
            
            # Initialisation des configurations
            configs = {
                'weather': WeatherConfig,
                'site': SiteConfig,
                'widget': WidgetConfig
            }
            
            for config_name, config_class in configs.items():
                if not config_class.query.first():
                    db.session.add(config_class())
            
            try:
                db.session.commit()
                logger.info('Base de données initialisée avec succès')
            except Exception as commit_error:
                logger.error(f"Erreur lors du commit: {commit_error}")
                db.session.rollback()
                raise
                
    except Exception as e:
        logger.error(f"Erreur fatale d'initialisation de la base de données: {e}")
        raise SystemExit(1)

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
        'current_datetime': datetime.now()
    }

@app.context_processor
def inject_models():
    """Injecte les modèles nécessaires dans les templates"""
    return {
        'MenuItem': MenuItem
    }

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f'Page non trouvée: {request.url}')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Erreur serveur: {error}')
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    logger.warning(f'Accès interdit: {request.url} par {current_user.identifiant if not current_user.is_anonymous else "anonyme"}')
    return render_template('errors/403.html'), 403

@app.errorhandler(401)
def unauthorized_error(error):
    logger.warning(f'Accès non autorisé: {request.url}')
    return render_template('errors/401.html'), 401

@app.errorhandler(405)
def method_not_allowed_error(error):
    logger.warning(f'Méthode non autorisée: {request.method} {request.url}')
    return render_template('errors/405.html'), 405

@app.errorhandler(Exception)
def handle_unhandled_error(error):
    logger.error(f'Erreur non gérée: {error}', exc_info=True)
    return render_template('errors/500.html'), 500

@app.route('/')
def home():
    try:
        config = WidgetConfig.query.first() or WidgetConfig()
        context = {
            'config': config,
            'absences': Absence.query.all(),
            'events': Event.get_upcoming_events(),
            'menu_items': MenuItem.get_todays_menu() if config.show_menu_cantine else [],
            'cts_arrivals': get_cts_arrivals(config) if config.has_valid_transport_config() else [],
            'active_widgets': config.get_all_active_widgets()
        }
        return render_template('home.html', **context)
    except Exception as e:
        logger.error(f'Erreur page d\'accueil: {str(e)}')
        return f"Erreur : {str(e)}", 500

def get_cts_arrivals(config):
    if not config.show_transports:
        logger.info("Widget transport désactivé")
        return []
    
    if not config.cts_stop_code:
        logger.warning("Code d'arrêt CTS non configuré")
        return []
    
    try:
        endpoint = f"{app.config['CTS_BASE_URL']}/v1/siri/2.0/stop-monitoring"
        api_token = config.cts_api_token or app.config['CTS_API_TOKEN']
        
        if not api_token:
            logger.error("Token API CTS manquant")
            return []

        params = {
            "MonitoringRef": config.cts_stop_code,
            "VehicleMode": config.cts_vehicle_mode or "undefined",
            "PreviewInterval": "PT2H",
            "MaximumStopVisits": 10
        }

        logger.info(f"Requête CTS: {endpoint} avec arrêt {config.cts_stop_code}")
        response = requests.get(
            endpoint, 
            params=params,
            auth=(api_token, ""),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            visits = data["ServiceDelivery"]["StopMonitoringDelivery"][0].get("MonitoredStopVisit", [])
            visits = visits[:10]
            logger.info(f"Nombre de passages trouvés après limitation : {len(visits)}")
            return visits
        
        logger.error(f"Erreur CTS: statut {response.status_code}, réponse: {response.text}")
        return []
    except Exception as e:
        logger.error(f"Erreur CTS: {str(e)}")
        return []

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
        'cts_form': CTSForm(),
        'menu_form': MenuItemForm()
    }
    
    configs = {
        'widget': WidgetConfig.query.first() or WidgetConfig(),
        'site': SiteConfig.get_config(),
        'weather': WeatherConfig.get_config()
    }
    
    # Pré-remplissage des formulaires
    if not forms['widget_form'].is_submitted():
        widget_config = configs['widget']
        forms['widget_form'].show_menu_cantine.data = widget_config.show_menu_cantine
        forms['widget_form'].show_transports.data = widget_config.show_transports
        forms['widget_form'].cts_stop_code.data = widget_config.cts_stop_code
        forms['widget_form'].cts_vehicle_mode.data = widget_config.cts_vehicle_mode
        forms['widget_form'].cts_api_token.data = widget_config.cts_api_token

    # Pré-remplissage des formulaires
    if not forms['widget_form'].is_submitted():
        forms['widget_form'] = WidgetConfigForm(obj=configs['widget'])
    if not forms['site_form'].is_submitted():
        forms['site_form'].site_name.data = configs['site'].site_name
    if not forms['weather_form'].is_submitted():
        forms['weather_form'].api_key.data = configs['weather'].api_key
        forms['weather_form'].city.data = configs['weather'].city
        forms['weather_form'].show_weather.data = configs['weather'].show_weather

    # Traitement du POST
    if request.method == 'POST':
        # Traitement du formulaire de configuration des widgets
        if 'submit_widget' in request.form:
            if forms['widget_form'].validate_on_submit():
                widget_config = configs['widget']

                if 'show_menu_cantine' in request.form:
                    widget_config.show_menu_cantine = forms['widget_form'].show_menu_cantine.data

                if 'show_transports' in request.form:
                    widget_config.show_transports = forms['widget_form'].show_transports.data
                    if widget_config.show_transports:
                        widget_config.cts_stop_code = forms['widget_form'].cts_stop_code.data
                        widget_config.cts_vehicle_mode = forms['widget_form'].cts_vehicle_mode.data
                        widget_config.cts_api_token = forms['widget_form'].cts_api_token.data
                widget_config.cts_stop_display = forms['widget_form'].cts_stop_display.data

                db.session.commit()
                flash('Configuration widgets mise à jour', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # Traitement du formulaire de recherche CTS pour prévisualisation
        if 'submit_cts' in request.form or 'submit_cts_save' in request.form:
            cts_stop_code = (forms['cts_form'].stop_code.data or "").strip()
            cts_vehicle_mode = forms['cts_form'].vehicle_mode.data or "undefined"
            endpoint = f"{app.config['CTS_BASE_URL']}/v1/siri/2.0/stop-monitoring"
            params = {
                "MonitoringRef": cts_stop_code,
                "VehicleMode": cts_vehicle_mode,
                "PreviewInterval": "PT30M",
                "MaximumStopVisits": 5
            }
            try:
                response = requests.get(endpoint, params=params,
                                        auth=(configs['widget'].cts_api_token or app.config['CTS_API_TOKEN'], ""))
                if response.status_code == 200:
                    data = response.json()
                    try:
                        cts_results = data["ServiceDelivery"]["StopMonitoringDelivery"][0]["MonitoredStopVisit"]
                    except (KeyError, IndexError):
                        cts_results = []
                        flash("Aucune donnée trouvée pour cet arrêt", "info")
                else:
                    cts_results = []
                    flash("Erreur lors de la récupération des données CTS", "danger")
            except Exception as e:
                cts_results = []
                flash("Erreur lors de l'appel à l'API CTS", "danger")
            
            # Si l'admin clique sur "Utiliser ce stop pour l'affichage", on enregistre les infos dans le widget
            if 'submit_cts_save' in request.form:
                widget_config = configs['widget']
                widget_config.cts_stop_code = cts_stop_code
                widget_config.cts_vehicle_mode = cts_vehicle_mode
                db.session.commit()
                flash("Le code d'arrêt CTS a été enregistré pour l'affichage sur la page d'accueil", 'success')
                return redirect(url_for('admin_dashboard'))
            
            return render_template(
                'admin_dashboard.html',
                absences=Absence.query.all(),
                widget_config=configs['widget'],
                future_events=Event.get_upcoming_events(),
                **forms,
                cts_results=cts_results,
                searched_cts_stop=cts_stop_code,
                searched_vehicle_mode=cts_vehicle_mode
            )
        
        # Traitement des autres formulaires (absences, événements, site, météo, etc.)
        form_handlers = {
            'delete_absence': handle_absence_deletion,
            'submit_absence': handle_absence_update,
            'submit_password': handle_password_change,
            'submit_event': handle_event_creation,
            'delete_event': handle_event_deletion,
            'submit_site': handle_site_config,
            'submit_weather': handle_weather_config,
            'submit_menu_item': handle_menu_item_creation,
            'delete_menu_item': handle_menu_item_deletion
        }
        for action, handler in form_handlers.items():
            if action in request.form:
                return handler(request, forms, configs)
    
    return render_template(
        'admin_dashboard.html',
        absences=Absence.query.all(),
        widget_config=configs['widget'],
        future_events=Event.get_upcoming_events(),
        menu_items=MenuItem.get_todays_menu(),
        **forms
    )

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

def handle_menu_item_creation(request, forms, configs):
    if forms['menu_form'].validate_on_submit():
        menu_item = MenuItem(
            category=forms['menu_form'].category.data,
            name=forms['menu_form'].name.data,
            description=forms['menu_form'].description.data,
            icons=''.join(forms['menu_form'].icons.data),
            date=forms['menu_form'].date.data
        )
        db.session.add(menu_item)
        db.session.commit()
        flash('Plat ajouté au menu', 'success')
    return redirect(url_for('admin_dashboard'))

def handle_menu_item_deletion(request, forms, configs):
    item_id = request.form.get('delete_menu_item')
    menu_item = MenuItem.query.get(item_id)
    if menu_item:
        db.session.delete(menu_item)
        db.session.commit()
        flash('Plat supprimé du menu', 'success')
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
            'show_menu_cantine': widget_config.show_menu_cantine
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

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": weather_config.city,
                "appid": weather_config.api_key,
                "units": "metric",
                "lang": "fr"
            }
        )

        if response.status_code == 200:
            data = response.json()
            description = data['weather'][0]['description']
            description = description[:1].upper() + description[1:]

            return jsonify({
                'temp': round(data['main']['temp']),
                'description': description,
                'icon': data['weather'][0]['icon']
            })
        
        return jsonify({'error': 'Données météo non disponibles'}), 500
    except Exception as e:
        logger.error(f'Erreur météo: {e}')
        return jsonify({'error': str(e)}), 500

def get_weather_description(weather_code):
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
    try:
        with app.app_context():
            initialize_database()
            
        try:
            app.run(debug=False, use_reloader=False)
        except OSError as socket_error:
            if socket_error.winerror == 10038:
                logger.error("Erreur de socket Windows. Tentative de redémarrage du serveur...")
                import time
                time.sleep(1)
                app.run(debug=True, use_reloader=False)
            else:
                logger.error(f"Erreur de socket non gérée: {socket_error}")
                raise
    except SystemExit as e:
        logger.critical("Arrêt du programme suite à une erreur d'initialisation")
        raise
    except Exception as e:
        logger.critical(f"Erreur inattendue: {e}")
        raise SystemExit(1)