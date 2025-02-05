from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, DateField, SubmitField, SelectField
from wtforms.fields import SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp, EqualTo
from datetime import date

class LoginForm(FlaskForm):
    identifiant = StringField('Identifiant', validators=[
        DataRequired(),
        Length(max=120)
    ])
    password = PasswordField('Mot de Passe', validators=[
        DataRequired(),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', 
               message="Le mot de passe doit contenir au moins une lettre et un chiffre")
    ])
    submit = SubmitField('Connexion')

class AbsenceForm(FlaskForm):
    professeur = StringField('Professeur', validators=[DataRequired()])
    jours = SelectMultipleField('Jours d\'absence', choices=[
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
    ])
    submit_absence = SubmitField('Ajouter / Modifier')
    
    def validate_professeur(self, field):
        if len(field.data.strip()) < 2:
            raise ValidationError('Le nom du professeur doit contenir au moins 2 caractères')

class WidgetConfigForm(FlaskForm):
    show_menu_cantine = BooleanField('Afficher le menu de la cantine')
    menu_entree = StringField('Entrée du jour', 
                            render_kw={"placeholder": "Ex: Salade César"})
    menu_plat = StringField('Plat principal',
                          render_kw={"placeholder": "Ex: Poulet rôti et pommes de terre"})
    menu_dessert = StringField('Dessert',
                             render_kw={"placeholder": "Ex: Tarte aux pommes"})
    menu_cantine = TextAreaField('Menu de la cantine')
    show_transports = BooleanField('Afficher le widget de transports')
    cts_api_token = StringField('Clé API CTS', validators=[Length(min=32, max=64)])
    cts_stop_code = StringField("Code d'arrêt CTS")
    cts_vehicle_mode = SelectField("Mode de transport",
                                 choices=[("bus", "Bus"), ("tram", "Tram"), ("undefined", "Tous")],
                                 default="undefined")
    cts_stop_name = StringField("Nom d'affichage de l'arrêt", render_kw={"placeholder": "Ex: Arrêt Lycée"})
    submit_widget = SubmitField('Enregistrer la configuration')

class EventForm(FlaskForm):
    title = StringField('Titre', validators=[
        DataRequired(message="Le titre est requis"),
        Length(min=3, max=200, message="Le titre doit contenir entre 3 et 200 caractères")
    ])
    date = DateField('Date', validators=[DataRequired(message="La date est requise")])
    description = TextAreaField('Description')
    submit_event = SubmitField('Ajouter l\'événement')
    
    def validate_date(self, field):
        try:
            if field.data < date.today():
                raise ValidationError('La date doit être dans le futur')
        except (TypeError, ValueError):
            raise ValidationError('Format de date invalide')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', 
               message="Le mot de passe doit contenir au moins une lettre et un chiffre")
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('new_password', message='Les mots de passe doivent correspondre')
    ])
    submit_password = SubmitField('Changer le mot de passe')

class SiteConfigForm(FlaskForm):
    site_name = StringField('Nom de l\'établissement', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    submit_site = SubmitField('Enregistrer')

class WeatherConfigForm(FlaskForm):
    api_key = StringField('Clé API OpenWeather', validators=[
        DataRequired(),
        Length(min=32, max=32, message="La clé API doit faire exactement 32 caractères")
    ])
    city = StringField('Ville', validators=[
        DataRequired(),
        Length(min=2, max=100, message="Le nom de la ville doit faire entre 2 et 100 caractères")
    ])
    show_weather = BooleanField('Afficher la météo')
<<<<<<< Updated upstream
    submit_weather = SubmitField('Mettre à jour la configuration météo')

class TransportConfigForm(FlaskForm):
    enabled = BooleanField('Activer l\'intégration CTS')
    api_token = StringField('Token API CTS', validators=[Length(max=100)])
    show_in_banner = BooleanField('Afficher les prochains passages dans la bannière')
    submit_transport = SubmitField('Mettre à jour la configuration transport')

class StopPointForm(FlaskForm):
    code = StringField('Code arrêt', validators=[DataRequired()])
    name = StringField('Nom de l\'arrêt', validators=[DataRequired()])
    submit_stop = SubmitField('Ajouter un arrêt')
=======
    submit_weather = SubmitField('Mettre à jour la configuration météo')
>>>>>>> Stashed changes
