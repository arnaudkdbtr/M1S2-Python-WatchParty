#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Watch Party - Application pour regarder des vidéos YouTube de façon synchronisée
Point d'entrée principal de l'application
"""

import tkinter as tk
import sys
import logging
from gui import WatchPartyApp
from utils_config import set_app_icon

def run_integration_test():
    """Fonction de test automatisé avec une instance serveur et client"""
    import threading
    import time
    
    # Démarrer une instance serveur dans un thread séparé
    def start_server():
        server_root = tk.Tk()
        server_root.title("HOST - Watch Party")
        
        # Appliquer l'icône
        set_app_icon(server_root)
        
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
        
        # Appliquer l'icône
        set_app_icon(client_root)
        
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

def main():
    """Point d'entrée principal de l'application"""
    # Vérifier les arguments de ligne de commande
    if "--test" in sys.argv:
        run_integration_test()
    else:
        root = tk.Tk()
        root.title("Watch Party")
        
        # Appliquer l'icône
        set_app_icon(root)
        
        app = WatchPartyApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()