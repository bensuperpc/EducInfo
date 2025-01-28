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
        config = WidgetConfig.query.first() or WidgetConfig()
        absences = Absence.query.all()
        events = Event.get_upcoming_events()
        
        return render_template('home.html', 
                             config=config, 
                             absences=absences, 
                             events=events)
    except Exception as e:
        logger.error(f'Error in home route: {e}')
        abort(500)

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
    }
    
    widget_config = WidgetConfig.query.first() or WidgetConfig()
    forms['widget_form'] = WidgetConfigForm(obj=widget_config)
    
    site_config = SiteConfig.get_config()
    weather_config = WeatherConfig.get_config()
    absences = Absence.query.all()

    # Pré-remplir les formulaires avec les valeurs actuelles
    if not forms['site_form'].is_submitted():
        forms['site_form'].site_name.data = site_config.site_name
    if not forms['weather_form'].is_submitted():
        forms['weather_form'].api_key.data = weather_config.api_key
        forms['weather_form'].city.data = weather_config.city
        forms['weather_form'].show_weather.data = weather_config.show_weather

    # Gestion des formulaires POST
    if request.method == 'POST':
        # Gestion de la suppression d'absence
        if 'delete_absence' in request.form:
            absence_id = request.form.get('delete_absence')
            absence = Absence.query.get(absence_id)
            if absence:
                db.session.delete(absence)
                db.session.commit()
                flash('Absence supprimée avec succès', 'success')
                return redirect(url_for('admin_dashboard'))

        # Gestion des widgets
        if 'submit_widget' in request.form and forms['widget_form'].validate_on_submit():
            if not widget_config:
                widget_config = WidgetConfig()
                db.session.add(widget_config)
            
            # widget_config.show_weather = widget_form.show_weather.data
            widget_config.show_menu_cantine = forms['widget_form'].show_menu_cantine.data
            widget_config.menu_cantine = forms['widget_form'].menu_cantine.data
            db.session.commit()
            flash('Configuration widgets mise à jour', 'success')
            return redirect(url_for('admin_dashboard'))

        # Gestion de l'ajout/modification d'absence
        if 'submit_absence' in request.form and forms['absence_form'].validate_on_submit():
            professeur = forms['absence_form'].professeur.data
            jours = request.form.getlist('jours')  # Obtenir tous les jours sélectionnés

            # Vérifier si le professeur existe déjà
            absence = Absence.query.filter_by(professeur=professeur).first()
            if not absence:
                absence = Absence(professeur=professeur)
                db.session.add(absence)
                flash(f'Nouvelle absence ajoutée pour {professeur}', 'success')
            else:
                flash(f'Absence mise à jour pour {professeur}', 'info')

            # Mettre à jour les jours
            absence.lundi = 'lundi' in jours
            absence.mardi = 'mardi' in jours
            absence.mercredi = 'mercredi' in jours
            absence.jeudi = 'jeudi' in jours
            absence.vendredi = 'vendredi' in jours

            db.session.commit()
            return redirect(url_for('admin_dashboard'))

        # Gestion du changement de mot de passe
        if 'submit_password' in request.form and forms['password_form'].validate_on_submit():
            user = User.query.filter_by(identifiant=current_user.identifiant).first()
            if user and user.check_password(forms['password_form'].current_password.data):
                user.set_password(forms['password_form'].new_password.data)
                db.session.commit()
                flash('Mot de passe modifié avec succès', 'success')
                return redirect(url_for('logout'))
            else:
                flash('Mot de passe actuel incorrect', 'error')

        # Gestion Widgets
        if 'submit_widget' in request.form:
            if forms['widget_form'].validate_on_submit():
                widget_config.show_weather = forms['widget_form'].show_weather.data
                widget_config.show_menu_cantine = forms['widget_form'].show_menu_cantine.data
                widget_config.menu_cantine = forms['widget_form'].menu_cantine.data
                db.session.commit()
                flash('Configuration widgets mise à jour', 'success')
                return redirect(url_for('admin_dashboard'))

        # Gestion Événements
        if 'submit_event' in request.form:
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

        if 'delete_event' in request.form:
            event_id = request.form.get('delete_event')
            evt = Event.query.get(event_id)
            if evt:
                db.session.delete(evt)
                db.session.commit()
                flash('Événement supprimé', 'warning')
            return redirect(url_for('admin_dashboard'))

        # Gestion de la configuration du site
        if 'submit_site' in request.form and forms['site_form'].validate_on_submit():
            site_config.site_name = forms['site_form'].site_name.data
            db.session.commit()
            flash('Nom de l\'établissement mis à jour', 'success')
            return redirect(url_for('admin_dashboard'))

        # Gestion de la configuration météo
        if 'submit_weather' in request.form and forms['weather_form'].validate_on_submit():
            weather_config.api_key = forms['weather_form'].api_key.data
            weather_config.city = forms['weather_form'].city.data
            weather_config.show_weather = forms['weather_form'].show_weather.data
            db.session.commit()
            
            # Mettre à jour la configuration de l'application
            app.config['WEATHER_API_KEY'] = weather_config.api_key
            app.config['WEATHER_CITY'] = weather_config.city
            
            flash('Configuration météo mise à jour avec succès', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('admin_dashboard.html',
                           absences=absences,
                           widget_config=widget_config,
                           future_events=Event.get_upcoming_events(),
                           **forms) 

@app.route('/get_updates')
def get_updates():
    """Route pour obtenir les mises à jour en temps réel"""
    try:
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

        widget_config = WidgetConfig.query.first()
        config_data = {
            'show_weather': widget_config.show_weather,
            'show_menu_cantine': widget_config.show_menu_cantine,
            'menu_cantine': widget_config.menu_cantine
        } if widget_config else {}

        return jsonify({
            'absences': absences,
            'events': events,
            'widget_config': config_data
        })
    except Exception as e:
        logger.error(f'Error in get_updates: {e}')
        return jsonify({'error': 'Une erreur est survenue'}), 500

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
        # Ajoutez d'autres codes selon besoin
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
        # Ajoutez d'autres codes selon besoin
    }
    return weather_icons.get(weather_code, "🌡️")

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True)
    app.run(debug=True)