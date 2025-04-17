# 🎬 Watch Party Synchronisée (100 % Python)

🔧 Ce projet est encore en cours de développement.

## 📌 Présentation du Projet

Watch Party Synchronisée est une application développée exclusivement en Python permettant d'organiser des soirées de visionnage de vidéos YouTube synchronisées entre plusieurs utilisateurs distants. Chaque participant voit exactement la même chose au même moment, avec des commandes centralisées comme lecture, pause ou repositionnement dans la vidéo.

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
- chromedriver est installé sur votre système et est compatible avec votre version de Google Chrome. (La version utilisé par les auteurs du programme est disponible dans le dépot [ici](chromedriver.exe))

## 🚀 Fonctionnalités principales

- 📺 **Synchronisation vidéo avancée**
  - Lecture/pause synchronisée entre tous les participants
  - Navigation temporelle (seek) instantanément partagée
  - Prise en charge des formats d'URL YouTube standard

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
- 
- 
-
