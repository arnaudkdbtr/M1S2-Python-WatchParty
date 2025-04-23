# Contrôle de YouTube via Selenium

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urlparse, parse_qs
import time
import logging

logger = logging.getLogger(__name__)

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

            # Options pour éviter la détection comme bot
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            if headless:
                chrome_options.add_argument("--headless")
            #chrome_options.add_argument("--mute-audio")  # Option pour démarrer sans son
            
            # Ajouter un user-agent standard
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
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