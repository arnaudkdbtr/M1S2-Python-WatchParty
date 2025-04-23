# Interface graphique pour l'application Watch Party

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import socket
import threading
import logging
from utils_config import THEMES, PORT, set_app_icon, setup_ngrok, get_public_ip, logger
from server import Server
from client import Client
from pyngrok import ngrok

class WatchPartyApp:
    """Interface graphique pour l'application Watch Party"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Watch Party")
        self.master.geometry("800x600")
        self.master.minsize(600, 450)
        
        # Définir l'icône pour la fenêtre principale
        set_app_icon(self.master)
        
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
        
        # Ligne 3: Options de synchronisation automatique
        sync_options_frame = ttk.Frame(video_frame)
        sync_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.auto_sync_var = tk.BooleanVar(value=True)
        self.auto_sync_check = ttk.Checkbutton(
            sync_options_frame, 
            text="Correction automatique de désynchronisation", 
            variable=self.auto_sync_var,
            command=self.toggle_auto_sync
        )
        self.auto_sync_check.pack(side=tk.LEFT, padx=5)
        
        # Entrée pour le seuil de synchronisation
        ttk.Label(sync_options_frame, text="Seuil (sec):").pack(side=tk.LEFT, padx=5)
        self.sync_threshold_var = tk.StringVar(value="1.0")
        self.sync_threshold_entry = tk.Entry(sync_options_frame, textvariable=self.sync_threshold_var, width=4)
        self.sync_threshold_entry.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour appliquer le seuil
        self.apply_threshold_button = ttk.Button(
            sync_options_frame, 
            text="Appliquer", 
            command=self.apply_sync_threshold
        )
        self.apply_threshold_button.pack(side=tk.LEFT, padx=5)
        
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

    def toggle_auto_sync(self):
        """Active ou désactive la synchronisation automatique"""
        if self.client:
            enabled = self.auto_sync_var.get()
            
            if enabled:
                # Activer le rapport périodique de position
                if not hasattr(self, 'sync_timer') or not self.sync_timer:
                    self.start_position_reporting()
                self.add_system_message("Correction automatique de désynchronisation activée")
            else:
                # Désactiver le rapport périodique
                if hasattr(self, 'sync_timer') and self.sync_timer:
                    self.master.after_cancel(self.sync_timer)
                    self.sync_timer = None
                self.add_system_message("Correction automatique de désynchronisation désactivée")
    
    def apply_sync_threshold(self):
        """Applique le nouveau seuil de synchronisation"""
        if not self.client or not self.is_host:
            return
            
        try:
            threshold = float(self.sync_threshold_var.get())
            if threshold <= 0:
                raise ValueError("Le seuil doit être positif")
                
            # Envoyer le seuil au serveur
            if self.server:
                self.server.sync_threshold = threshold
                self.add_system_message(f"Seuil de synchronisation défini à {threshold} secondes")
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre positif valide")
    
    def start_position_reporting(self):
        """Démarre le rapport périodique de position"""
        if self.client and self.auto_sync_var.get():
            # Envoyer un rapport de position
            self.client.report_position()
            
            # Planifier le prochain rapport
            self.sync_timer = self.master.after(1000, self.start_position_reporting)

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
        dialog = tk.Toplevel(self.master)
        dialog.title("Nom d'utilisateur")
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Appliquer l'icône à la boîte de dialogue
        set_app_icon(dialog)
        
        # Fermer le dialogue pour continuer
        dialog.destroy()
        
        username = simpledialog.askstring("Nom d'utilisateur", "Entrez votre nom d'utilisateur:", 
                                          initialvalue=self.username.get())
        if not username:
            return  # L'utilisateur a annulé
        
        # Mettre à jour le nom d'utilisateur
        self.username.set(username)
        
        # Demander si l'utilisateur souhaite activer ngrok
        ngrok_dialog = tk.Toplevel(self.master)
        ngrok_dialog.title("Mode en ligne")
        ngrok_dialog.transient(self.master)
        ngrok_dialog.grab_set()
        
        # Appliquer l'icône à la boîte de dialogue
        set_app_icon(ngrok_dialog)
        
        # Fermer le dialogue pour continuer
        ngrok_dialog.destroy()
        
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
        server_dialog = tk.Toplevel(self.master)
        server_dialog.title("Adresse du serveur")
        server_dialog.transient(self.master)
        server_dialog.grab_set()
        
        # Appliquer l'icône à la boîte de dialogue
        set_app_icon(server_dialog)
        
        # Fermer le dialogue pour continuer
        server_dialog.destroy()
        
        server_addr = simpledialog.askstring("Adresse du serveur", "Entrez l'adresse du serveur:",
                                            initialvalue=self.server_addr.get())
        if not server_addr:
            return  # L'utilisateur a annulé
        
        # Demander le port du serveur
        port_dialog = tk.Toplevel(self.master)
        port_dialog.title("Port du serveur")
        port_dialog.transient(self.master)
        port_dialog.grab_set()
        
        # Appliquer l'icône à la boîte de dialogue
        set_app_icon(port_dialog)
        
        # Fermer le dialogue pour continuer
        port_dialog.destroy()
        
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
        user_dialog = tk.Toplevel(self.master)
        user_dialog.title("Nom d'utilisateur")
        user_dialog.transient(self.master)
        user_dialog.grab_set()
        
        # Appliquer l'icône à la boîte de dialogue
        set_app_icon(user_dialog)
        
        # Fermer le dialogue pour continuer
        user_dialog.destroy()
        
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
            
            # Initialiser le seuil de synchronisation
            try:
                threshold = float(self.sync_threshold_var.get())
                if threshold > 0:
                    self.server.sync_threshold = threshold
            except:
                pass
            
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
            
            # Démarrer le rapport de position si la synchronisation auto est activée
            if self.auto_sync_var.get():
                self.start_position_reporting()
            
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
        
        # Appliquer l'icône à la boîte de dialogue
        set_app_icon(token_dialog)
        
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
        
        # Appliquer l'icône à la fenêtre
        set_app_icon(info_window)
        
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
            
    def update_ui_connection_state(self, connected):
        """Met à jour l'état de l'interface en fonction de la connexion"""
        state = tk.NORMAL if connected else tk.DISABLED
        host_only_state = tk.NORMAL if connected and self.is_host else tk.DISABLED
        
        # Boutons de connexion (inversé pour les boutons de connexion)
        self.host_button.config(state=tk.DISABLED if connected else tk.NORMAL)
        self.client_button.config(state=tk.DISABLED if connected else tk.NORMAL)
        
        # Contrôles vidéo
        self.video_url_entry.config(state=host_only_state)  # Restriction: seulement l'hôte peut modifier l'URL
        self.set_video_button.config(state=host_only_state)  # Seulement l'hôte peut définir la vidéo
        self.play_button.config(state=host_only_state)       # Seulement l'hôte peut lancer la lecture
        self.pause_button.config(state=host_only_state)      # Seulement l'hôte peut mettre en pause
        self.seek_entry.config(state=host_only_state)        # Seulement l'hôte peut chercher
        self.seek_button.config(state=host_only_state)       # Seulement l'hôte peut chercher
        self.sync_button.config(state=host_only_state)       # Seulement l'hôte peut synchroniser
        
        # Contrôles de synchronisation
        self.sync_threshold_entry.config(state=host_only_state)
        self.apply_threshold_button.config(state=host_only_state)
        
        # Contrôles chat
        self.chat_input.config(state=state)
        self.send_button.config(state=state)
        
        # Activer le rapport de position si connecté et synchronisation auto activée
        if connected:
            # Activer le rapport de position si la synchronisation auto est activée
            if self.auto_sync_var.get():
                self.start_position_reporting()
        else:
            # Arrêter le rapport de position
            if hasattr(self, 'sync_timer') and self.sync_timer:
                self.master.after_cancel(self.sync_timer)
                self.sync_timer = None
        
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