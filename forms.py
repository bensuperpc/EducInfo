from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, DateField, SubmitField, SelectField
from wtforms.fields import SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp, EqualTo
from datetime import date
from models import ThemeConfig

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
    # show_weather = BooleanField('Afficher la météo (barre du bas)')
    show_menu_cantine = BooleanField('Afficher le menu de la cantine')
    menu_cantine = TextAreaField('Menu de la cantine')
    submit_widget = SubmitField('Enregistrer')

class EventForm(FlaskForm):
    title = StringField('Titre', validators=[
        DataRequired(),
        Length(min=3, max=200)
    ])
    date = DateField('Date', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit_event = SubmitField('Ajouter l\'Événement')
    
    def validate_date(self, field):
        if field.data < date.today():
            raise ValidationError('La date doit être future')

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

class ThemeConfigForm(FlaskForm):
    primary_color = SelectField('Couleur principale', 
                              choices=ThemeConfig.get_color_choices(),
                              validators=[DataRequired()])
    submit_theme = SubmitField('Enregistrer')

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
    submit_weather = SubmitField('Mettre à jour la configuration météo')
