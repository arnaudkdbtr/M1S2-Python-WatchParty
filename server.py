# Logique du serveur

import socket
import threading
import json
import time
import logging
from utils_config import PORT, BUFFER_SIZE, logger

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
        # Nouveau: pour suivre le temps de lecture de chaque client
        self.client_positions = {}  # {client_addr: {"time": seconds, "timestamp": server_time}}
        self.host_client = None  # Référence au socket du client hôte
        self.sync_threshold = 1.0  # Seuil de désynchronisation en secondes
        
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
    
    def check_sync_status(self, client_addr, position):
        """Vérifie si un client est désynchronisé et envoie une correction si nécessaire"""
        with self.lock:
            # Stocker la position du client avec un horodatage
            self.client_positions[client_addr] = {
                "time": position,
                "timestamp": time.time()
            }
            
            # Si c'est l'hôte, mettre à jour l'état courant
            if self.host_client and tuple(client_addr) == self.host_client.getpeername():
                self.current_video_state["time"] = position
                
                # Vérifier la synchronisation de tous les clients
                current_host_position = position
                clients_to_sync = []
                
                for client_socket in self.clients:
                    try:
                        client_addr_tuple = client_socket.getpeername()
                        # Ne pas vérifier l'hôte lui-même
                        if client_socket == self.host_client:
                            continue
                            
                        # Récupérer la position du client s'il existe
                        client_data = self.client_positions.get(client_addr_tuple)
                        if client_data:
                            client_position = client_data["time"]
                            time_diff = abs(current_host_position - client_position)
                            
                            # Si le décalage est supérieur au seuil, ajouter à la liste à synchroniser
                            if time_diff > self.sync_threshold:
                                clients_to_sync.append(client_socket)
                    except:
                        continue
                
                # Envoyer des commandes de synchronisation aux clients désynchronisés
                for client_socket in clients_to_sync:
                    try:
                        self.send_to_client(client_socket, {
                            "type": "auto_sync",
                            "time": current_host_position
                        })
                        logger.info(f"Correction automatique envoyée au client {client_socket.getpeername()}")
                    except:
                        pass
        
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
                
        elif msg_type == "report_position":
            # Un client envoie sa position actuelle
            position = message.get("time", 0)
            is_playing = message.get("playing", False)
            
            try:
                if sender_socket:
                    client_addr = sender_socket.getpeername()
                    # Enregistrer la position du client et vérifier la synchronisation
                    self.check_sync_status(client_addr, position)
                    
                    # Si c'est l'hôte qui envoie sa position, identifier ce socket comme l'hôte
                    if message.get("is_host", False):
                        self.host_client = sender_socket
                        # Mettre à jour l'état de lecture
                        self.current_video_state["playing"] = is_playing
            except Exception as e:
                logger.error(f"Erreur lors du traitement d'un rapport de position: {e}")
    
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