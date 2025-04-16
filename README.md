# 🎬 Watch Party Synchronisée (100 % Python)

## 📌 Présentation du Projet

Watch Party Synchronisée est une application développée exclusivement en Python permettant d’organiser des soirées de visionnage de vidéos YouTube synchronisées entre plusieurs utilisateurs distants. Chaque participant voit exactement la même chose au même moment, avec des commandes centralisées comme lecture, pause ou repositionnement dans la vidéo.

🧪 Ce projet a été réalisé dans le cadre de l’UE Technique de Programmation, un cours du second semestre du Master 1, dédié exclusivement au développement Python.

## 🚀 Fonctionnalités principales

-📺 Lecture synchronisée de vidéos YouTube
-🎮 Contrôle centralisé par l’hôte (lecture, pause, seek)
-🌐 Communication réseau via socket ou via Ngrok pour le mode en ligne
-🤖 Automatisation du navigateur via Selenium
-💬 Chat texte intégré entre les participants
-🧵 Multi-threading pour gérer commandes et échanges simultanés

## 🖥️ Fonctionnement
### 🎬 Côté hôte : 

1) L’hôte lance watchparty.py et clique sur Utilisation Hôte

2) Il choisit s’il souhaite :
-➕ Utiliser une connexion locale
-🌐 Ou activer Ngrok pour une connexion à distance (serveur en ligne). Une clé Ngrok par défaut est proposée (modifiable si l’utilisateur a la sienne)

3) Une fois la clé saisie, un serveur distant est lancé automatiquement, avec une adresse publique (host + port)

4) L’hôte entre l’URL YouTube à visionner

5) Le serveur est prêt, les clients peuvent rejoindre.

### 🎬 Côté client : 

1) Le client lance également watchparty.py

2) Il choisit le mode client

3) Il entre :
- L’adresse et le port du serveur (fournis par l’hôte)

4) Le navigateur s’ouvre automatiquement avec la vidéo de l’hôte

5) Toutes les commandes de lecture sont reçues et exécutées en temps réel

## 🧩 Fonctionnalités futures envisagées

🗳️ Système de votes pour choisir la vidéo à regarder

📃 Playlists partagées

🎞️ Intégration directe du lecteur vidéo dans l’application (sans ouvrir un navigateur à part)

🌐 Support d’autres plateformes (Netflix, Prime Video…)

🎨 Amélioration graphique via une future interface plus soignée 

🖥️ Déploiement d’un site web permettant d’utiliser l’application sans installer Python

## ⚠️ Contraintes

🔹 Projet 100 % Python

🔹 Aucun HTML/CSS

🔹 Interface actuelle en ligne de commande (future via tkinter)

🔹 Compatible avec Windows, macOS et Linux (avec chromedriver installé)
