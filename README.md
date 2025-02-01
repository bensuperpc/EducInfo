# EducInfo

Ancinnement : Espace d'information pour le Lycée Couffignal à Strasbourg

**Ce projet est en cours de reprise. Il peut avoir des dysfonctionnements dans ses premières versions**

## Quel est le but de ce projet ?

Proposer une solution pour afficher des informations comme les absences, le menu de cantine, etc ... aux élèves facilement

## Fonctionnalités

- **Absences** : Affichage hebdomadaire des absences, géré via un tableau de bord admin.
- **Widgets dynamiques** :
  - Météo
  - Menu Cantine
  - Événements à venir
- **Interface Admin Sécurisée** :
  - Authentification via Flask-Login (sessions)
  - Formulaires WTForms pour gérer absences, config widgets, et événements
- **Design Moderne** : Intégration de Tailwind via un CDN pour un style épuré.

## Installation

Vous aurez besoin de Python 3.12 et pip pour installer les dépendances.

1. **Cloner le dépôt** :

```bash
  git clone https://github.com/Doalou/EducInfo.git
  cd EducInfo
```

2. **Installer les dépendances** :

```bash
pip install -r requirements.txt
```

3. **Initialiser la base de données** :

Lors du premier lancement, l’appli créera le fichier educinfo.db et un utilisateur admin par défaut (admin@educinfo.com / admin123).
Vous pouvez modifier ce comportement dans app.py (fonction create_tables).

4. **Lancer l'application** :

```bash
python app.py
```


## Docker

Vous pouvez également utiliser Docker pour lancer l'application.

1. **Construire l'image** :

```bash
make docker
```

ou

```bash
make docker.build
```

2. **Lancer le conteneur** :

```bash
make docker.run
```

Vous pouvez maintenant accéder à l'application sur **http://127.0.0.1:5000/**

### Tests

Pour lancer les tests, vous pouvez utiliser la commande suivante :

```bash
make docker.test
```
