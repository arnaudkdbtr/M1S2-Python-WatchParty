# Logique du client

import socket
import threading
import json
import time
import logging
from utils_config import PORT, BUFFER_SIZE, logger
from youtube_controller import YouTubeController

class Client:
    """Classe représentant un client qui se connecte au serveur de synchronisation"""
    
    def __init__(self, host='localhost', port=PORT):
        self.host = host
        self.port = port
        self.client_socket = None
        self.connected = False
        self.running = False
        self.youtube_controller = YouTubeController()
        self.username = "User" + str(int(time.time()) % 1000)  # Nom par défaut
        self.message_handlers = {}
        self.last_sync_time = 0
        self.is_host = False  # Indique si ce client est l'hôte
        # Attributs pour la correction automatique de désynchronisation
        self.position_report_interval = 5  # Intervalle de rapport en secondes
        self.last_position_report = 0
        
    def connect(self):
        """Se connecte au serveur"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # Démarrer le thread de réception des messages
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            logger.info(f"Connecté au serveur {self.host}:{self.port}")
            
            # Demander une synchronisation initiale
            self.send_message({"type": "sync_request"})
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la connexion au serveur: {e}")
            self.connected = False
            return False
            
    def receive_messages(self):
        """Reçoit et traite les messages du serveur"""
        while self.running:
            try:
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                    
                message = json.loads(data.decode('utf-8'))
                logger.info(f"Message reçu du serveur: {message}")
                
                self.process_message(message)
                
            except json.JSONDecodeError:
                logger.error("Message mal formaté reçu du serveur")
            except Exception as e:
                if self.running:  # Ignorer les erreurs lors de la déconnexion
                    logger.error(f"Erreur lors de la réception d'un message: {e}")
                break
                
        self.connected = False
        logger.info("Déconnecté du serveur")
        
    def process_message(self, message):
        """Traite un message reçu du serveur"""
        msg_type = message.get("type")
        
        if msg_type == "video_info":
            url = message.get("url")
            state = message.get("state", {})
            
            # Ouvrir la vidéo si elle n'est pas déjà ouverte
            if not self.youtube_controller.is_initialized:
                self.youtube_controller.initialize_browser()
                
            # Ouvrir la vidéo (sera mise en pause automatiquement par la méthode open_video)
            self.youtube_controller.open_video(url)
            
            # Appliquer l'état (position et lecture/pause)
            time_pos = state.get("time", 0)
            playing = state.get("playing", False)
            
            # D'abord chercher la position
            self.youtube_controller.seek(time_pos)
            
            # Ensuite appliquer l'état de lecture (par défaut: pause)
            if playing:
                # Seulement si explicitement en lecture
                self.youtube_controller.play()
            else:
                # Pour s'assurer que la vidéo est bien en pause
                self.youtube_controller.pause()
                
        elif msg_type == "play":
            if self.youtube_controller.is_initialized:
                self.youtube_controller.play()
                
        elif msg_type == "pause":
            if self.youtube_controller.is_initialized:
                self.youtube_controller.pause()
                
        elif msg_type == "seek":
            if self.youtube_controller.is_initialized:
                time_pos = message.get("time", 0)
                self.youtube_controller.seek(time_pos)
                
        elif msg_type == "host_time_request":
            # L'hôte doit répondre avec sa position actuelle
            # (cette partie ne sera exécutée que sur l'hôte)
            if self.is_host and self.youtube_controller.is_initialized:
                requester = message.get("requester", None)
                current_time = self.youtube_controller.get_current_time()
                is_playing = self.youtube_controller.is_playing()
                
                # Envoyer notre position actuelle au serveur
                self.send_message({
                    "type": "host_time_response",
                    "time": current_time,
                    "playing": is_playing,
                    "requester": requester
                })
                
        elif msg_type == "chat":
            # Traiter un message de chat
            username = message.get("username", "Anonyme")
            content = message.get("content", "")
            
            # Si un gestionnaire de chat est enregistré, l'appeler
            handler = self.message_handlers.get("chat")
            if handler:
                handler(username, content)
                
        elif msg_type == "auto_sync":
            # Commande de synchronisation automatique
            if self.youtube_controller.is_initialized and not self.is_host:
                time_pos = message.get("time", 0)
                logger.info(f"Correction automatique reçue: alignement à {time_pos} secondes")
                self.youtube_controller.seek(time_pos)
        
        # Appeler le gestionnaire générique si enregistré
        handler = self.message_handlers.get("message")
        if handler:
            handler(message)
            
    def send_message(self, message):
        """Envoie un message au serveur"""
        if not self.connected:
            logger.error("Non connecté au serveur")
            return False
            
        try:
            data = json.dumps(message).encode('utf-8')
            self.client_socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'un message au serveur: {e}")
            self.connected = False
            return False
            
    def set_video(self, url):
        """Définit la vidéo à regarder"""
        return self.send_message({
            "type": "set_video",
            "url": url
        })
        
    def play(self):
        """Lance la lecture de la vidéo"""
        return self.send_message({"type": "play"})
        
    def pause(self):
        """Met en pause la vidéo"""
        return self.send_message({"type": "pause"})
        
    def seek(self, time_pos):
        """Déplace la lecture à un moment précis"""
        return self.send_message({
            "type": "seek",
            "time": float(time_pos)
        })
        
    def send_chat(self, content):
        """Envoie un message de chat"""
        return self.send_message({
            "type": "chat",
            "username": self.username,
            "content": content
        })
        
    def register_handler(self, event_type, handler):
        """Enregistre un gestionnaire pour un type d'événement"""
        self.message_handlers[event_type] = handler
        
    def sync_with_server(self):
        """Demande une synchronisation avec le serveur"""
        current_time = time.time()
        if current_time - self.last_sync_time > 2:  # Limiter les requêtes de sync
            self.last_sync_time = current_time
            return self.send_message({"type": "sync_request"})
        return False
        
    def force_sync(self):
        """Force la synchronisation de tous les clients avec l'état actuel de l'hôte"""
        if not self.connected or not self.youtube_controller.is_initialized:
            return False
            
        try:
            # Obtenir l'état actuel de la vidéo locale
            current_time = self.youtube_controller.get_current_time()
            is_playing = self.youtube_controller.is_playing()
            
            # Envoyer l'état pour synchroniser tous les clients
            return self.send_message({
                "type": "force_sync",
                "time": current_time,
                "playing": is_playing
            })
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation forcée: {e}")
            return False
            
    def report_position(self):
        """Envoie la position actuelle au serveur pour la détection de désynchronisation"""
        if not self.connected or not self.youtube_controller.is_initialized:
            return False
            
        current_time = time.time()
        # Limiter la fréquence des rapports
        if current_time - self.last_position_report < self.position_report_interval:
            return False
            
        try:
            # Obtenir la position actuelle
            position = self.youtube_controller.get_current_time()
            is_playing = self.youtube_controller.is_playing()
            
            # Envoyer la position au serveur
            self.last_position_report = current_time
            return self.send_message({
                "type": "report_position",
                "time": position,
                "playing": is_playing,
                "is_host": self.is_host  # Indiquer si ce client est l'hôte
            })
        except Exception as e:
            logger.error(f"Erreur lors du rapport de position: {e}")
            return False
        
    def disconnect(self):
        """Se déconnecte du serveur"""
        self.running = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
                
        if self.youtube_controller:
            self.youtube_controller.close()
            
        self.connected = False
        logger.info("Déconnecté du serveur")