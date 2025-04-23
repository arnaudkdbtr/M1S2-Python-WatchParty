# Utilitaires et configuration

import io
import base64
from PIL import Image, ImageTk
import requests
import logging
from pyngrok import ngrok, conf

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

# Fonction pour définir l'icône de l'application
def set_app_icon(window):
    """Définit l'icône de l'application à partir d'une chaîne base64"""
    try:
        # Chaîne base64 de l'icône 
        icon_base64 = "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"
        
        # Décoder la chaîne base64
        icon_data = base64.b64decode(icon_base64)
        
        # Créer une image à partir des données
        icon_image = Image.open(io.BytesIO(icon_data))
        
        # Convertir l'image en format PhotoImage pour Tkinter
        icon_photo = ImageTk.PhotoImage(icon_image)
        
        # Définir l'icône de la fenêtre
        window.iconphoto(True, icon_photo)
        
        # Stocker l'image pour éviter qu'elle ne soit supprimée par le garbage collector
        window.icon_image = icon_photo
        
    except Exception as e:
        logger.error(f"Erreur lors de la définition de l'icône: {e}")

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