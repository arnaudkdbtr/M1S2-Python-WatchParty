![Python Version](https://img.shields.io/badge/Python-3.6%2B-blue)
![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-green)
![Chromedriver](https://img.shields.io/badge/Chromedriver-Required-orange)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-lightgrey)
![Network](https://img.shields.io/badge/Network-Local%20%7C%20Internet-blueviolet)

<h1 style="display: flex; align-items: center; gap: 10px;">
  <img src="Annexes/Logo%2064x64.png" alt="Logo" width="40" />
  Watch Party
</h1>

## 📌 Présentation du Projet

Watch Party est une application développée en Python permettant d'organiser des soirées de visionnage de vidéos YouTube synchronisées entre plusieurs utilisateurs distants. Chaque participant voit exactement la même chose au même moment, avec des commandes centralisées comme lecture, pause ou repositionnement dans la vidéo.

🧪 Ce projet a été réalisé dans le cadre de l'UE Technique de Programmation, un cours du second semestre du Master 1, dédié exclusivement au développement Python.

## ✅ Prérequis

```
pip install selenium
```
```
pip install pyngrok requests
```
```
pip install pyperclip pillow
```

⚠️ Important : L'application utilise Selenium, qui nécessite Chromedriver. Assurez-vous que :
- chromedriver est installé sur votre système et est compatible avec votre version de Google Chrome. (La version utilisé par les auteurs du programme est disponible dans le dépot [ici](Annexes/chromedriver.exe))

## 🏗️ Architecture du projet

Le code a été organisé en différents modules pour améliorer la maintenabilité et la lisibilité. Voici le découpage des fichiers :

### 📂 Structure des fichiers

- main.py : Point d'entrée de l'application qui initialise l'interface graphique
- utils_config.py : Constantes, thèmes, et fonctions utilitaires (comme la gestion de l'icône et ngrok)
- youtube_controller.py : Contrôle du navigateur YouTube via Selenium
- server.py : Logique du serveur pour synchroniser les clients
- client.py : Gestion de la connexion au serveur et traitement des messages
- gui.py : Interface utilisateur complète de l'application

### 💾 Version complète

Pour des raisons pédagogiques et de référence, la version originale non découpée du code est conservée dans le dossier [Annexes/watchparty_full.py](Annexes/watchparty_full.py). Cette version contient toutes les fonctionnalités dans un seul fichier et peut être utilisée comme point de départ pour comprendre l'ensemble du projet.

## 🚀 Fonctionnalités principales

- 📺 **Synchronisation vidéo avancée**
  - Lecture/pause synchronisée entre tous les participants
  - Navigation temporelle (seek) instantanément partagée
  - Prise en charge des formats d'URL YouTube standard
  - Correction automatique de désynchronisation (écarts > 1s)

- 🎮 **Interface utilisateur intuitive**
  - Mode clair / Mode sombre personnalisable
  - Boutons de contrôle vidéo (lecture, pause, recherche temporelle)
  - Zone de chat intégrée avec identification des utilisateurs
  - Affichage des messages système (connexions, synchronisations)

- 🌐 **Connectivité réseau complète**
  - Mode hôte pour créer une session
  - Mode client pour rejoindre une session
  - Fonctionnement en réseau local ou via Internet (ngrok)
  - Affichage des informations de connexion partageables

- 💬 **Communication intégrée**
  - Chat texte en temps réel entre participants
  - Messages système pour événements importants

- 🔄 **Robustesse et fiabilité**
  - Détection automatique des déconnexions
  - Gestion des erreurs de synchronisation
  - Nettoyage des ressources à la fermeture
  - Architecture multithread pour une réactivité optimale

## 🖥️ Fonctionnement

### 🎬 Côté hôte : 
1. L'hôte lance watchparty.py et clique sur "Démarrer comme Hôte"
2. Il entre son nom d'utilisateur
3. Il choisit s'il souhaite :
   - ➕ Utiliser une connexion locale
   - 🌐 Ou activer Ngrok pour une connexion à distance (serveur en ligne). Une clé Ngrok par défaut est proposée (modifiable si l'utilisateur a la sienne)
4. Une fois la clé saisie, un serveur distant est lancé automatiquement, avec une adresse publique (host + port)
5. L'hôte entre l'URL YouTube à visionner
6. Le serveur est prêt, les clients peuvent rejoindre.
7. Lorsque les clients sont dans la room, l'hôte clique sur "Définir vidéo" pour ouvrir le navigateur synchronisé pour tout le monde

### 👥 Côté client : 
1. Le client lance également watchparty.py
2. Il clique sur "Rejoindre comme Client"
3. Il entre :
   - L'adresse du serveur (fournie par l'hôte)
   - Le port du serveur (fourni par l'hôte)
   - Son nom d'utilisateur
4. Le navigateur s'ouvre automatiquement avec la vidéo lorsque l'hôte définit une vidéo
5. Toutes les commandes de lecture sont reçues et exécutées en temps réel

## 🧩 Fonctionnalités actuelles et en développement

### ✅ Fonctionnalités implémentées
- 🎞️ Synchronisation de vidéos YouTube
- 🌑 Mode sombre / Mode clair
- 💬 Chat texte intégré
- 🔄 Synchronisation automatique des clients
- 🌐 Accès internet via Ngrok
- 🔑 Support de token Ngrok personnalisé

### 🚧 Fonctionnalités futures envisagées
- 🗳️ Système de votes pour choisir la vidéo à regarder
- 📃 Playlists partagées
- 🎞️ Intégration directe du lecteur vidéo dans l'application (sans ouvrir un navigateur à part)
- 🌐 Support d'autres plateformes (Netflix, Prime Video…)
- 🎨 Amélioration graphique via une future interface plus soignée 
- 🖥️ Déploiement d'un site web permettant d'utiliser l'application sans installer Python

## ⚠️ Contraintes
🔹 Projet 100 % Python

🔹 Aucun HTML/CSS car hors du programme du cours

## Auteurs
- Arnaud KINDBEITER
- Maé SENECHAL
- Valentin LAGARDE
