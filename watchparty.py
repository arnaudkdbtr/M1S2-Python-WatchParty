#Installer dans le terminal au préalable
#pip install pyperclip pillow
#pip install selenium
#pip install pyngrok requests
import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import re
import logging
import os
import sys
from urllib.parse import urlparse, parse_qs
from pyngrok import ngrok, conf
import requests
import io

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
PORT = 5555
BUFFER_SIZE = 4096

# Thèmes pour le mode clair et sombre
THEMES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "frame_bg": "#e0e0e0",
        "button_bg": "#d0d0d0",
        "entry_bg": "#ffffff",
        "chat_bg": "#ffffff",
        "chat_fg": "#000000",
        "chat_system_fg": "#0000AA",
        "chat_highlight_bg": "#e6e6e6",
        "status_bg": "#d9d9d9"
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "frame_bg": "#2d2d2d",
        "button_bg": "#3d3d3d",
        "entry_bg": "#3d3d3d",
        "chat_bg": "#2d2d2d",
        "chat_fg": "#e0e0e0",
        "chat_system_fg": "#8cb4ff",
        "chat_highlight_bg": "#3d3d3d",
        "status_bg": "#333333"
    }
}

class YouTubeController:
    """Classe pour contrôler le navigateur YouTube via Selenium"""
    
    def __init__(self):
        self.driver = None
        self.is_initialized = False
        self.video_id = None
        
    def initialize_browser(self, headless=False):
        """Initialise le navigateur Chrome avec Selenium"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--mute-audio")  # Option pour démarrer sans son
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.is_initialized = True
            logger.info("Navigateur initialisé avec succès")
            return True
        except WebDriverException as e:
            logger.error(f"Erreur lors de l'initialisation du navigateur: {e}")
            return False
            
    def open_video(self, url):
        """Ouvre une vidéo YouTube"""
        if not self.is_initialized:
            logger.error("Le navigateur n'est pas initialisé")
            return False
            
        try:
            # Extraction de l'ID de la vidéo YouTube
            parsed_url = urlparse(url)
            if 'youtube.com' in parsed_url.netloc:
                query_params = parse_qs(parsed_url.query)
                self.video_id = query_params.get('v', [None])[0]
            elif 'youtu.be' in parsed_url.netloc:
                self.video_id = parsed_url.path[1:]
            else:
                self.video_id = None
                
            if not self.video_id:
                logger.error("URL YouTube non valide")
                return False
                
            # Construction de l'URL de partage propre
            clean_url = f"https://www.youtube.com/watch?v={self.video_id}"
            self.driver.get(clean_url)
            
            # Attente que la vidéo soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "movie_player"))
            )
            
            # Accepter le cookie consent si présent
            try:
                consent_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Accepter') or contains(@aria-label, 'Accept')]"))
                )
                consent_button.click()
            except:
                pass  # Ignorer si le bouton de consentement n'est pas présent
            
            # Petite pause pour laisser la vidéo se charger correctement
            time.sleep(2)
            
            # IMPORTANT: Forcer la mise en pause immédiatement après le chargement
            # Cela évite que la vidéo ne démarre automatiquement chez le client
            try:
                self.pause()
                logger.info("Vidéo mise en pause automatiquement après chargement")
            except Exception as e:
                logger.error(f"Erreur lors de la mise en pause initiale: {e}")
                
            logger.info(f"Vidéo YouTube ouverte avec succès: {clean_url}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de la vidéo: {e}")
            return False
            
    def play(self):
        """Lance la lecture de la vidéo"""
        if not self.is_initialized:
            return False
            
        try:
            self.driver.execute_script("document.getElementById('movie_player').playVideo();")
            logger.info("Lecture de la vidéo lancée")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du lancement de la lecture: {e}")
            return False
            
    def pause(self):
        """Met en pause la vidéo"""
        if not self.is_initialized:
            return False
            
        try:
            self.driver.execute_script("document.getElementById('movie_player').pauseVideo();")
            logger.info("Vidéo mise en pause")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise en pause: {e}")
            return False
            
    def seek(self, time_seconds):
        """Déplace la lecture à un moment précis (en secondes)"""
        if not self.is_initialized:
            return False
            
        try:
            self.driver.execute_script(f"document.getElementById('movie_player').seekTo({time_seconds}, true);")
            logger.info(f"Lecture déplacée à {time_seconds} secondes")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du déplacement de la lecture: {e}")
            return False
            
    def get_current_time(self):
        """Récupère le temps actuel de la vidéo en secondes"""
        if not self.is_initialized:
            return 0
            
        try:
            current_time = self.driver.execute_script("return document.getElementById('movie_player').getCurrentTime();")
            return float(current_time)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du temps actuel: {e}")
            return 0
            
    def is_playing(self):
        """Vérifie si la vidéo est en cours de lecture"""
        if not self.is_initialized:
            return False
            
        try:
            state = self.driver.execute_script("return document.getElementById('movie_player').getPlayerState();")
            # État 1 = en lecture, 2 = en pause
            return state == 1
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'état de lecture: {e}")
            return False
            
    def close(self):
        """Ferme le navigateur"""
        if self.is_initialized and self.driver:
            try:
                self.driver.quit()
                self.is_initialized = False
                logger.info("Navigateur fermé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du navigateur: {e}")

class Server:
    """Classe représentant le serveur de synchronisation des vidéos"""
    
    def __init__(self, host='0.0.0.0', port=PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.current_video_url = None
        self.current_video_state = {"playing": False, "time": 0.0}
        self.lock = threading.Lock()
        
    def start(self):
        """Démarre le serveur"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"Serveur démarré sur {self.host}:{self.port}")
            
            # Démarrer le thread d'acceptation des clients
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du serveur: {e}")
            return False
            
    def accept_connections(self):
        """Accept de nouvelles connexions clients en continu"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Nouvelle connexion de {addr[0]}:{addr[1]}")
                
                with self.lock:
                    self.clients.append(client_socket)
                
                # Si une vidéo est déjà en cours, envoyer les infos au nouveau client
                if self.current_video_url:
                    self.send_to_client(client_socket, {
                        "type": "video_info",
                        "url": self.current_video_url,
                        "state": self.current_video_state
                    })
                
                # Démarrer un thread pour gérer ce client
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:  # Ignorer les erreurs lors de l'arrêt du serveur
                    logger.error(f"Erreur lors de l'acceptation d'une connexion: {e}")
                    
    def handle_client(self, client_socket, addr):
        """Gère les messages d'un client spécifique"""
        while self.running:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                    
                message = json.loads(data.decode('utf-8'))
                logger.info(f"Message reçu de {addr[0]}:{addr[1]}: {message}")
                
                self.process_message(message, client_socket)
                
            except json.JSONDecodeError:
                logger.error(f"Message mal formaté reçu de {addr[0]}:{addr[1]}")
            except Exception as e:
                logger.error(f"Erreur lors du traitement d'un message client: {e}")
                break
                
        # Client déconnecté
        with self.lock:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
        try:
            client_socket.close()
        except:
            pass
        logger.info(f"Client {addr[0]}:{addr[1]} déconnecté")
        
    def process_message(self, message, sender_socket=None):
        """Traite un message reçu d'un client"""
        msg_type = message.get("type")
        
        if msg_type == "set_video":
            self.current_video_url = message.get("url")
            self.current_video_state = {"playing": False, "time": 0.0}
            
            # Diffuser à tous les clients
            self.broadcast({
                "type": "video_info",
                "url": self.current_video_url,
                "state": self.current_video_state
            })
            
        elif msg_type == "play":
            self.current_video_state["playing"] = True
            self.broadcast({"type": "play"})
            
        elif msg_type == "pause":
            self.current_video_state["playing"] = False
            self.broadcast({"type": "pause"})
            
        elif msg_type == "seek":
            time_pos = message.get("time", 0)
            self.current_video_state["time"] = time_pos
            self.broadcast({
                "type": "seek",
                "time": time_pos
            })
            
        elif msg_type == "sync_request":
            # Un client demande une synchronisation
            if sender_socket and self.current_video_url:
                # Avant d'envoyer l'état, on demande à l'hôte son état actuel
                # Pour cela, on diffuse une demande spéciale à l'hôte
                try:
                    requester_addr = sender_socket.getpeername()
                    self.broadcast({
                        "type": "host_time_request",
                        "requester": requester_addr  # Identifie le client qui a fait la demande
                    })
                    
                    # On envoie quand même l'état actuel (qui pourrait être un peu décalé)
                    # mais c'est mieux que rien en attendant la réponse de l'hôte
                    self.send_to_client(sender_socket, {
                        "type": "video_info",
                        "url": self.current_video_url,
                        "state": self.current_video_state
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la synchronisation: {e}")
                
        elif msg_type == "host_time_response":
            # L'hôte répond avec son temps actuel
            current_time = message.get("time", 0)
            playing = message.get("playing", False)
            requester_addr = message.get("requester", None)
            
            # Mettre à jour l'état stocké
            self.current_video_state["time"] = current_time
            self.current_video_state["playing"] = playing
            
            # Si un client spécifique a fait la demande, on lui envoie la mise à jour
            if requester_addr:
                for client in self.clients:
                    try:
                        if client.getpeername() == tuple(requester_addr):
                            self.send_to_client(client, {
                                "type": "seek",
                                "time": current_time
                            })
                            if playing:
                                self.send_to_client(client, {"type": "play"})
                            else:
                                self.send_to_client(client, {"type": "pause"})
                            break
                    except:
                        continue
                
        elif msg_type == "force_sync":
            # L'hôte demande une synchronisation forcée pour tous les clients
            current_time = message.get("time", 0)
            playing = message.get("playing", False)
            
            # Mettre à jour l'état actuel de la vidéo
            self.current_video_state["time"] = current_time
            self.current_video_state["playing"] = playing
            
            # Diffuser à tous les clients
            self.broadcast({
                "type": "seek",
                "time": current_time
            })
            
            # Diffuser l'état de lecture (play/pause)
            if playing:
                self.broadcast({"type": "play"})
            else:
                self.broadcast({"type": "pause"})
                
        elif msg_type == "chat":
            # Message de chat à diffuser
            username = message.get("username", "Anonyme")
            content = message.get("content", "")
            if content.strip():
                self.broadcast({
                    "type": "chat",
                    "username": username,
                    "content": content
                })
    
    def broadcast(self, message):
        """Envoie un message à tous les clients connectés"""
        with self.lock:
            disconnected_clients = []
            for client in self.clients:
                try:
                    self.send_to_client(client, message)
                except:
                    disconnected_clients.append(client)
                    
            # Nettoyer les clients déconnectés
            for client in disconnected_clients:
                if client in self.clients:
                    self.clients.remove(client)
                    
    def send_to_client(self, client_socket, message):
        """Envoie un message à un client spécifique"""
        try:
            data = json.dumps(message).encode('utf-8')
            client_socket.sendall(data)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'un message à un client: {e}")
            raise
            
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        
        # Fermer toutes les connexions client
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients = []
            
        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            
        logger.info("Serveur arrêté")

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

class WatchPartyApp:
    """Interface graphique pour l'application Watch Party"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Watch Party Synchronisée")
        self.master.geometry("800x600")
        self.master.minsize(600, 450)
        
        # Variables
        self.is_host = False
        self.server = None
        self.client = None
        self.server_addr = tk.StringVar(value="localhost")
        self.server_port = tk.IntVar(value=PORT)
        self.username = tk.StringVar(value="User" + str(int(time.time()) % 1000))
        self.video_url = tk.StringVar(value="https://www.youtube.com/watch?v=jNQXAC9IVRw")  # Vidéo test par défaut
        
        # Thème actuel (par défaut: clair)
        self.current_theme = "light"
        
        # Configuration de l'interface
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Configurer le thème initial
        self.apply_theme()
        
        # Style
        self.style = ttk.Style()
        self.update_style()
        
        # Cadre principal
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Section configuration
        config_frame = ttk.LabelFrame(main_frame, text="Configuration")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ligne 1: Mode (Hôte/Client) et thème
        mode_frame = ttk.Frame(config_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        
        self.host_button = ttk.Button(mode_frame, text="Démarrer comme Hôte", command=self.show_host_dialog)
        self.host_button.pack(side=tk.LEFT, padx=5)
        
        self.client_button = ttk.Button(mode_frame, text="Rejoindre comme Client", command=self.show_client_dialog)
        self.client_button.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour changer de thème
        self.theme_button = ttk.Button(mode_frame, text="Mode Sombre", command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=5)
        
        # Ligne 2: Configuration réseau
        network_frame = ttk.Frame(config_frame)
        network_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(network_frame, text="Adresse serveur:").pack(side=tk.LEFT, padx=5)
        self.server_addr_entry = tk.Entry(network_frame, textvariable=self.server_addr, width=15)
        self.server_addr_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(network_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.server_port_entry = tk.Entry(network_frame, textvariable=self.server_port, width=6)
        self.server_port_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(network_frame, text="Nom d'utilisateur:").pack(side=tk.LEFT, padx=5)
        self.username_entry = tk.Entry(network_frame, textvariable=self.username, width=15)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        
# Section vidéo
        video_frame = ttk.LabelFrame(main_frame, text="Contrôle vidéo")
        video_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ligne 1: URL vidéo
        url_frame = ttk.Frame(video_frame)
        url_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(url_frame, text="URL YouTube:").pack(side=tk.LEFT, padx=5)
        self.video_url_entry = tk.Entry(url_frame, textvariable=self.video_url, width=50)
        self.video_url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.set_video_button = ttk.Button(url_frame, text="Définir Vidéo", command=self.set_video, state=tk.DISABLED)
        self.set_video_button.pack(side=tk.LEFT, padx=5)
        
        # Ligne 2: Contrôles vidéo
        control_frame = ttk.Frame(video_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.play_button = ttk.Button(control_frame, text="► Lecture", command=self.play_video, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="❚❚ Pause", command=self.pause_video, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Aller à (sec):").pack(side=tk.LEFT, padx=5)
        
        self.seek_var = tk.StringVar()
        self.seek_entry = tk.Entry(control_frame, textvariable=self.seek_var, width=6, state=tk.DISABLED)
        self.seek_entry.pack(side=tk.LEFT, padx=5)
        
        self.seek_button = ttk.Button(control_frame, text="Aller", command=self.seek_video, state=tk.DISABLED)
        self.seek_button.pack(side=tk.LEFT, padx=5)
        
        self.sync_button = ttk.Button(control_frame, text="⟳ Synchroniser", command=self.sync_video, state=tk.DISABLED)
        self.sync_button.pack(side=tk.LEFT, padx=5)
        
        # Section chat
        chat_frame = ttk.LabelFrame(main_frame, text="Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Zone des messages
        self.chat_text = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        chat_scroll = ttk.Scrollbar(chat_frame, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=chat_scroll.set)
        
        self.chat_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Zone d'envoi de message
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = tk.Entry(input_frame, width=50, state=tk.DISABLED)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.chat_input.bind("<Return>", self.send_chat_message)
        
        self.send_button = ttk.Button(input_frame, text="Envoyer", command=self.send_chat_message, state=tk.DISABLED)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        # Barre d'état en bas
        self.status_var = tk.StringVar(value="En attente de connexion...")
        self.status_bar = ttk.Label(self.master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Gestion de la fermeture de l'application
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def apply_theme(self):
        """Applique le thème actuel à la fenêtre principale"""
        theme = THEMES[self.current_theme]
        self.master.configure(bg=theme["bg"])
        
    def update_style(self):
        """Met à jour le style des widgets ttk selon le thème actuel"""
        theme = THEMES[self.current_theme]
        
        # Configuration du style ttk
        self.style.configure("TFrame", background=theme["frame_bg"])
        self.style.configure("TLabel", background=theme["frame_bg"], foreground=theme["fg"])
        self.style.configure("TButton", background=theme["button_bg"])
        self.style.configure("TEntry", fieldbackground=theme["entry_bg"], foreground=theme["fg"])
        self.style.configure("TLabelframe", background=theme["frame_bg"], foreground=theme["fg"])
        self.style.configure("TLabelframe.Label", background=theme["frame_bg"], foreground=theme["fg"])
        
        # Configurer les widgets existants
        if hasattr(self, 'chat_text'):
            self.chat_text.configure(bg=theme["chat_bg"], fg=theme["chat_fg"], insertbackground=theme["fg"])
            
        if hasattr(self, 'status_bar'):
            self.status_bar.configure(background=theme["status_bg"], foreground=theme["fg"])
            
    def toggle_theme(self):
        """Bascule entre le thème clair et sombre"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        
        # Mettre à jour le texte du bouton
        self.theme_button.configure(text="Mode Clair" if self.current_theme == "dark" else "Mode Sombre")
        
        # Appliquer le nouveau thème
        self.apply_theme()
        self.update_style()
        
        # Forcer la mise à jour de tous les widgets
        self.master.update_idletasks()
        
    def show_host_dialog(self):
        """Affiche la boîte de dialogue pour le mode hôte"""
        # Demander le nom d'utilisateur
        username = simpledialog.askstring("Nom d'utilisateur", "Entrez votre nom d'utilisateur:", 
                                          initialvalue=self.username.get())
        if not username:
            return  # L'utilisateur a annulé
        
        # Mettre à jour le nom d'utilisateur
        self.username.set(username)
        
        # Demander si l'utilisateur souhaite activer ngrok
        use_ngrok = messagebox.askyesno("Mode en ligne", 
                                        "Souhaitez-vous activer le mode en ligne via Ngrok?\n\n"
                                        "(Cela permettra à d'autres personnes de rejoindre depuis Internet)")
        
        # Désactiver les champs de configuration
        self.server_addr_entry.config(state=tk.DISABLED)
        self.server_port_entry.config(state=tk.DISABLED)
        self.username_entry.config(state=tk.DISABLED)
        
        # Démarrer le serveur avec les options choisies
        self.start_as_host(use_ngrok)
    
    def show_client_dialog(self):
        """Affiche les boîtes de dialogue pour le mode client"""
        # Demander l'adresse du serveur
        server_addr = simpledialog.askstring("Adresse du serveur", "Entrez l'adresse du serveur:",
                                            initialvalue=self.server_addr.get())
        if not server_addr:
            return  # L'utilisateur a annulé
        
        # Demander le port du serveur
        server_port_str = simpledialog.askstring("Port du serveur", "Entrez le port du serveur:",
                                                initialvalue=str(self.server_port.get()))
        if not server_port_str:
            return  # L'utilisateur a annulé
        
        try:
            server_port = int(server_port_str)
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être un nombre entier")
            return
        
        # Demander le nom d'utilisateur
        username = simpledialog.askstring("Nom d'utilisateur", "Entrez votre nom d'utilisateur:",
                                         initialvalue=self.username.get())
        if not username:
            return  # L'utilisateur a annulé
        
        # Mettre à jour les valeurs dans l'interface
        self.server_addr.set(server_addr)
        self.server_port.set(server_port)
        self.username.set(username)
        
        # Désactiver les champs de configuration
        self.server_addr_entry.config(state=tk.DISABLED)
        self.server_port_entry.config(state=tk.DISABLED)
        self.username_entry.config(state=tk.DISABLED)
        
        # Démarrer le client avec les paramètres
        self.start_as_client()
    
    def start_as_host(self, use_ngrok=False):
        """Démarre l'application en mode hôte"""
        if self.client or self.server:
            self.disconnect()
            
        # Vérifier le nom d'utilisateur
        if not self.username.get().strip():
            messagebox.showerror("Erreur", "Veuillez entrer un nom d'utilisateur")
            return
            
        try:
            port = self.server_port.get()
            
            # Créer et démarrer le serveur
            self.server = Server(port=port)
            if not self.server.start():
                messagebox.showerror("Erreur", "Impossible de démarrer le serveur")
                self.server = None
                return
                
            # Se connecter en tant que client au serveur local
            self.client = Client(host='localhost', port=port)
            self.client.username = self.username.get()
            self.client.is_host = True  # Marquer ce client comme étant l'hôte
            
            if not self.client.connect():
                messagebox.showerror("Erreur", "Impossible de se connecter au serveur local")
                self.server.stop()
                self.server = None
                self.client = None
                return
                
            # Enregistrer le gestionnaire de chat
            self.client.register_handler("chat", self.handle_chat_message)
            
            # Mettre à jour l'interface
            self.is_host = True
            self.update_ui_connection_state(True)
            self.status_var.set(f"Serveur démarré sur le port {port} - Connecté en tant qu'hôte")
            
            # Ajouter un message dans le chat
            self.add_system_message(f"Serveur démarré sur le port {port}")
            self.add_system_message(f"Connecté en tant qu'hôte : {self.client.username}")
            
            # Configurer ngrok si demandé
            if use_ngrok:
                self.configure_ngrok()
            else:
                self.configure_local_mode()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du démarrage du serveur: {e}")
            self.disconnect()
            
    def configure_ngrok(self):
        """Configure ngrok pour l'accès distant"""
        # Votre token prédéfini
        default_token = "2voI412xuqcxgr4AmOZFCQUGe3U_2VWwF2shALE626FYKbwhP"
        
        # Créer une boîte de dialogue personnalisée pour le token
        token_dialog = tk.Toplevel(self.master)
        token_dialog.title("Configuration ngrok")
        token_dialog.geometry("500x200")
        token_dialog.resizable(False, False)
        token_dialog.transient(self.master)
        token_dialog.grab_set()
        
        # Appliquer le thème actuel
        theme = THEMES[self.current_theme]
        token_dialog.configure(bg=theme["bg"])
        
        # Centrer la fenêtre
        token_dialog.update_idletasks()
        x = (token_dialog.winfo_screenwidth() - token_dialog.winfo_width()) // 2
        y = (token_dialog.winfo_screenheight() - token_dialog.winfo_height()) // 2
        token_dialog.geometry(f"+{x}+{y}")
        
        # Variable pour stocker le token
        token_var = tk.StringVar(value=default_token)
        
        # Créer les widgets
        frame = ttk.Frame(token_dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Token d'authentification ngrok:", font=("Arial", 11)).pack(pady=5)
        ttk.Label(frame, text="Un token par défaut est fourni, mais vous pouvez en utiliser un autre.", 
                 font=("Arial", 10)).pack(pady=2)
        
        token_entry = tk.Entry(frame, textvariable=token_var, width=50)
        token_entry.pack(pady=10, fill=tk.X)
        
        # Variable pour stocker le résultat
        result = {"token": None, "cancelled": True}
        
        # Fonctions pour les boutons
        def on_confirm():
            result["token"] = token_var.get()
            result["cancelled"] = False
            token_dialog.destroy()
            
        def on_cancel():
            token_dialog.destroy()
        
        # Boutons de confirmation et annulation
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10, fill=tk.X)
        
        ttk.Button(button_frame, text="Confirmer", command=on_confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        
        # Attendre que l'utilisateur ferme la boîte de dialogue
        self.master.wait_window(token_dialog)
        
        # Si l'utilisateur a confirmé, continuer avec ngrok
        if not result["cancelled"] and result["token"]:
            # Configurer ngrok avec le token fourni
            ngrok_host, ngrok_port = setup_ngrok(result["token"])
            
            if ngrok_host and ngrok_port:
                # Afficher les informations dans le chat
                self.add_system_message("=== INFORMATIONS DE CONNEXION ===")
                self.add_system_message(f"Tunnel ngrok créé avec succès!")
                self.add_system_message(f"Les participants peuvent se connecter avec:")
                self.add_system_message(f"Adresse: {ngrok_host}")
                self.add_system_message(f"Port: {ngrok_port}")
                
                # Afficher une fenêtre avec les informations de connexion
                self.show_connection_info_window(ngrok_host, ngrok_port)
            else:
                messagebox.showerror(
                    "Erreur ngrok", 
                    "Impossible de créer le tunnel ngrok. Vérifiez votre connexion Internet et votre token."
                )
                # Revenir au mode local en cas d'échec
                self.configure_local_mode()
        else:
            # L'utilisateur a annulé, revenir au mode local
            self.configure_local_mode()
            
    def configure_local_mode(self):
        """Configure l'application pour fonctionner en mode local uniquement"""
        # Obtenir l'IP locale
        local_ip = socket.gethostbyname(socket.gethostname())
        
        # Afficher les informations de connexion locale dans le chat
        self.add_system_message("=== MODE LOCAL UNIQUEMENT ===")
        self.add_system_message("Fonctionnement en mode réseau local uniquement.")
        self.add_system_message(f"Les participants sur votre réseau peuvent se connecter avec:")
        self.add_system_message(f"Adresse: {local_ip}")
        self.add_system_message(f"Port: {PORT}")
        
        # Afficher une fenêtre avec les informations locales
        self.show_connection_info_window(local_ip, PORT)
            
    def show_connection_info_window(self, host, port):
        """Affiche une fenêtre avec les informations de connexion"""
        info_window = tk.Toplevel(self.master)
        info_window.title("Informations de connexion")
        info_window.geometry("400x300")
        info_window.resizable(False, False)
        
        # Appliquer le thème actuel
        theme = THEMES[self.current_theme]
        info_window.configure(bg=theme["bg"])
        
        # Frame contenant les informations
        frame = ttk.Frame(info_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Informations textuelles
        ttk.Label(frame, text="Pour rejoindre cette session:", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(frame, text=f"Adresse: {host}", font=("Arial", 11)).pack(pady=2)
        ttk.Label(frame, text=f"Port: {port}", font=("Arial", 11)).pack(pady=2)
        
        # Instructions supplémentaires
        if "ngrok" in host:
            ttk.Label(frame, text="Note: Le tunnel ngrok sera actif pendant 2 heures maximum.", 
                     font=("Arial", 10), foreground=theme["chat_system_fg"]).pack(pady=5)
        else:
            ttk.Label(frame, text="IMPORTANT:", font=("Arial", 11, "bold")).pack(pady=10)
            ttk.Label(frame, text="Seuls les participants connectés à votre réseau local\npourront rejoindre cette session.", 
                     font=("Arial", 10)).pack(pady=2)
            ttk.Label(frame, text="Pour permettre l'accès depuis Internet, redémarrez\nl'application et activez l'accès distant avec ngrok.", 
                     font=("Arial", 10)).pack(pady=5)
        
        # Bouton pour copier les informations dans le presse-papier
        def copy_to_clipboard():
            info_window.clipboard_clear()
            info_window.clipboard_append(f"Adresse: {host}\nPort: {port}")
            messagebox.showinfo("Information", "Informations de connexion copiées dans le presse-papier")
        
        ttk.Button(frame, text="Copier les infos", command=copy_to_clipboard).pack(pady=10)
        
        # Centrer la fenêtre
        info_window.update_idletasks()
        width = info_window.winfo_width()
        height = info_window.winfo_height()
        x = (info_window.winfo_screenwidth() // 2) - (width // 2)
        y = (info_window.winfo_screenheight() // 2) - (height // 2)
        info_window.geometry(f"{width}x{height}+{x}+{y}")
        
    def start_as_client(self):
        """Démarre l'application en mode client"""
        if self.client or self.server:
            self.disconnect()
            
        # Vérifier le nom d'utilisateur
        if not self.username.get().strip():
            messagebox.showerror("Erreur", "Veuillez entrer un nom d'utilisateur")
            return
            
        try:
            host = self.server_addr.get()
            port = self.server_port.get()
            
            # Se connecter au serveur
            self.client = Client(host=host, port=port)
            self.client.username = self.username.get()
            self.client.is_host = False  # Marquer ce client comme n'étant pas l'hôte
            
            if not self.client.connect():
                messagebox.showerror("Erreur", "Impossible de se connecter au serveur")
                self.client = None
                return
                
            # Enregistrer le gestionnaire de chat
            self.client.register_handler("chat", self.handle_chat_message)
            
            # Mettre à jour l'interface
            self.is_host = False
            self.update_ui_connection_state(True)
            self.status_var.set(f"Connecté au serveur {host}:{port} en tant que client")
            
            # Ajouter un message dans le chat
            self.add_system_message(f"Connecté au serveur {host}:{port}")
            self.add_system_message(f"Connecté en tant que client : {self.client.username}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la connexion au serveur: {e}")
            self.disconnect()
            
    def disconnect(self):
        """Déconnecte du serveur et arrête le serveur si en mode hôte"""
        if self.client:
            self.client.disconnect()
            self.client = None
            
        if self.server:
            self.server.stop()
            self.server = None
            
        # Arrêter ngrok si actif
        try:
            ngrok.kill()
        except:
            pass
            
        self.is_host = False
        self.update_ui_connection_state(False)
        self.status_var.set("Déconnecté")
        self.add_system_message("Déconnecté du serveur")
        
        # Réactiver les champs de configuration
        self.server_addr_entry.config(state=tk.NORMAL)
        self.server_port_entry.config(state=tk.NORMAL)
        self.username_entry.config(state=tk.NORMAL)
        
    def update_ui_connection_state(self, connected):
        """Met à jour l'état de l'interface en fonction de la connexion"""
        state = tk.NORMAL if connected else tk.DISABLED
        host_only_state = tk.NORMAL if connected and self.is_host else tk.DISABLED
        
        # Boutons de connexion (inversé pour les boutons de connexion)
        self.host_button.config(state=tk.DISABLED if connected else tk.NORMAL)
        self.client_button.config(state=tk.DISABLED if connected else tk.NORMAL)
        
        # Contrôles vidéo
        self.set_video_button.config(state=host_only_state)  # Seulement l'hôte peut définir la vidéo
        self.play_button.config(state=host_only_state)       # Seulement l'hôte peut lancer la lecture
        self.pause_button.config(state=host_only_state)      # Seulement l'hôte peut mettre en pause
        self.seek_entry.config(state=host_only_state)        # Seulement l'hôte peut chercher
        self.seek_button.config(state=host_only_state)       # Seulement l'hôte peut chercher
        self.sync_button.config(state=host_only_state)       # Seulement l'hôte peut synchroniser
        
        # Contrôles chat
        self.chat_input.config(state=state)
        self.send_button.config(state=state)
        
    def set_video(self):
        """Définit la vidéo à regarder"""
        if not self.client or not self.is_host:
            return
            
        url = self.video_url.get().strip()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return
            
        # Vérifier que l'URL est une URL YouTube
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return
            
        if self.client.set_video(url):
            self.add_system_message(f"Vidéo définie: {url}")
        else:
            messagebox.showerror("Erreur", "Impossible de définir la vidéo")
            
    def play_video(self):
        """Lance la lecture de la vidéo"""
        if not self.client or not self.is_host:
            return
            
        if self.client.play():
            self.add_system_message("Lecture de la vidéo lancée")
        else:
            messagebox.showerror("Erreur", "Impossible de lancer la lecture")
            
    def pause_video(self):
        """Met en pause la vidéo"""
        if not self.client or not self.is_host:
            return
            
        if self.client.pause():
            self.add_system_message("Vidéo mise en pause")
        else:
            messagebox.showerror("Erreur", "Impossible de mettre en pause")
            
    def seek_video(self):
        """Déplace la lecture à un moment précis"""
        if not self.client or not self.is_host:
            return
            
        try:
            time_pos = float(self.seek_var.get())
            if time_pos < 0:
                raise ValueError("Le temps doit être positif")
                
            if self.client.seek(time_pos):
                self.add_system_message(f"Lecture déplacée à {time_pos} secondes")
            else:
                messagebox.showerror("Erreur", "Impossible de déplacer la lecture")
                
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide")
            
    def sync_video(self):
        """Demande une synchronisation"""
        if not self.client:
            return
            
        if self.is_host:
            # L'hôte force la synchronisation de tous les clients
            if self.client.force_sync():
                self.add_system_message("Synchronisation forcée envoyée à tous les clients")
            else:
                messagebox.showerror("Erreur", "Impossible de synchroniser les clients")
        else:
            # Un client demande une synchronisation avec le serveur
            if self.client.sync_with_server():
                self.add_system_message("Demande de synchronisation envoyée")
            else:
                messagebox.showerror("Erreur", "Impossible de synchroniser")
            
    def send_chat_message(self, event=None):
        """Envoie un message dans le chat"""
        if not self.client:
            return
            
        message = self.chat_input.get().strip()
        if not message:
            return
            
        if self.client.send_chat(message):
            # Le message sera affiché quand il reviendra du serveur
            self.chat_input.delete(0, tk.END)
        else:
            messagebox.showerror("Erreur", "Impossible d'envoyer le message")
            
    def handle_chat_message(self, username, content):
        """Gère un message de chat reçu"""
        theme = THEMES[self.current_theme]
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.tag_configure("username", foreground=theme["chat_fg"], font=("Arial", 10, "bold"))
        self.chat_text.tag_configure("content", foreground=theme["chat_fg"])
        
        self.chat_text.insert(tk.END, f"{username}: ", "username")
        self.chat_text.insert(tk.END, f"{content}\n", "content")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
    def add_system_message(self, message):
        """Ajoute un message système dans le chat"""
        theme = THEMES[self.current_theme]
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.tag_configure("system", foreground=theme["chat_system_fg"], font=("Arial", 9, "italic"))
        
        self.chat_text.insert(tk.END, f"[Système] {message}\n", "system")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
    def on_closing(self):
        """Gère la fermeture de l'application"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter ?"):
            self.disconnect()
            self.master.destroy()

# Fonctions utilitaires pour ngrok
def setup_ngrok(auth_token):
    """Configure et démarre un tunnel ngrok pour le serveur"""
    try:
        # Configurer ngrok avec le token fourni
        conf.get_default().auth_token = auth_token
        
        # Créer un tunnel TCP vers le port du serveur
        tunnel = ngrok.connect(PORT, "tcp")
        
        # Extraire l'adresse et le port du tunnel
        # L'URL ressemble à "tcp://0.tcp.ngrok.io:12345"
        tunnel_url = tunnel.public_url
        ngrok_host = tunnel_url.split("//")[1].split(":")[0]
        ngrok_port = int(tunnel_url.split("//")[1].split(":")[1])
        
        logger.info(f"Tunnel ngrok créé: {tunnel_url}")
        return ngrok_host, ngrok_port
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de ngrok: {e}")
        return None, None

def get_public_ip():
    """Obtient l'adresse IP publique de l'utilisateur"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return "Impossible de détecter l'IP publique"

def main():
    """Point d'entrée principal de l'application"""
    # Vérifier les arguments de ligne de commande
    if "--test" in sys.argv:
        run_integration_test()
    else:
        root = tk.Tk()
        app = WatchPartyApp(root)
        root.mainloop()

def run_integration_test():
    """Fonction de test automatisé avec une instance serveur et client"""
    import threading
    import time
    
    # Démarrer une instance serveur dans un thread séparé
    def start_server():
        server_root = tk.Tk()
        server_root.title("HOST - Watch Party")
        server_app = WatchPartyApp(server_root)
        
        # Simuler le démarrage du serveur après 1 seconde
        server_root.after(1000, lambda: server_app.show_host_dialog())
        
        # Simuler le réglage d'une vidéo test après 3 secondes
        server_root.after(3000, lambda: server_app.video_url.set("https://www.youtube.com/watch?v=jNQXAC9IVRw"))
        server_root.after(3500, lambda: server_app.set_video())
        
        # Simuler la lecture après 5 secondes
        server_root.after(5000, lambda: server_app.play_video())
        
        # Synchroniser tous les clients toutes les 10 secondes
        def periodic_sync():
            if server_app.client and server_app.is_host:
                server_app.sync_video()
            server_root.after(10000, periodic_sync)
            
        server_root.after(10000, periodic_sync)
        
        server_root.mainloop()
    
    # Démarrer une instance client dans un thread séparé
    def start_client():
        # Attendre que le serveur démarre
        time.sleep(2)
        
        client_root = tk.Tk()
        client_root.title("CLIENT - Watch Party")
        client_app = WatchPartyApp(client_root)
        
        # Simuler la connexion au serveur après 1 seconde
        client_root.after(1000, lambda: client_app.show_client_dialog())
        
        client_root.mainloop()
    
    # Démarrer le serveur dans un thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Démarrer le client dans le thread principal
    start_client()

if __name__ == "__main__":
    main()
