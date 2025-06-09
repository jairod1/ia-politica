from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import os
import time
import random
import re
import subprocess

# Intentar importar undetected-chromedriver
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
    print("✅ undetected-chromedriver disponible")
except ImportError:
    UNDETECTED_AVAILABLE = False
    print("⚠️ undetected-chromedriver NO disponible - usando anti-detección manual")

OUTPUT_DIR = os.path.join("..", "..", "data", "raw", "dirty-csvs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "faro-vigo-sucio.csv")

# CONFIGURACIÓN PRINCIPAL
DATE_THRESHOLD = datetime(2025, 6, 5)  # Fecha umbral - procesar artículos >= esta fecha
MAX_PAGES = 1000  # Máximo número de páginas a revisar
MAX_OLD_ARTICLES = 3  # Máximo artículos consecutivos anteriores al umbral antes de parar

# 🔥 NUEVA CONFIGURACIÓN ROBUSTA
MAX_DRIVER_FAILURES = 5  # Máximo fallos de driver antes de recrear
CURRENT_DRIVER_FAILURES = 0
DISQUS_TIMEOUT = 60  # Timeout más largo para Disqus (60s)
INTER_ARTICLE_DELAY = (15, 30)  # Delay entre artículos (15-30s)

def setup_stealth_driver_undetected():
    """Versión con undetected-chromedriver"""
    print("🥷 Configurando driver UNDETECTED...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")
    # 🔥 NUEVAS OPCIONES PARA ESTABILIDAD
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-ipc-flooding-protection")
    
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(60)  # 🔥 Timeout más largo
    driver.implicitly_wait(10)  # 🔥 Espera implícita más larga
    return driver

def setup_stealth_driver_manual():
    """Versión con anti-detección manual"""
    print("🥷 Configurando driver MANUAL anti-detección...")
    
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-extensions")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 🔥 NUEVAS OPCIONES PARA ESTABILIDAD CON IFRAMES
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    prefs = {
        "profile.default_content_setting_values": {"notifications": 2},
        "profile.managed_default_content_settings": {"images": 1}
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']})")
    
    driver.set_page_load_timeout(60)  # 🔥 Timeout más largo
    driver.implicitly_wait(10)  # 🔥 Espera implícita más larga
    return driver

def setup_stealth_driver():
    """Función principal - elige la mejor opción disponible"""
    if UNDETECTED_AVAILABLE:
        return setup_stealth_driver_undetected()
    else:
        return setup_stealth_driver_manual()

def kill_all_chrome():
    """🔨 Mata TODOS los Chrome zombies de forma brutal"""
    print("    🔨 Matando Chrome zombies...")
    try:
        # Windows: Matar Chrome y ChromeDriver
        subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                      capture_output=True, check=False)
        subprocess.run(['taskkill', '/f', '/im', 'chromedriver.exe'], 
                      capture_output=True, check=False)
        print("    ☠️ Chrome zombies eliminados")
    except Exception as e:
        print(f"    ⚠️ Error matando Chrome: {e}")

def setup_fresh_driver():
    """🆕 Crea un driver completamente fresco sin zombies"""
    kill_all_chrome()  # 🔨 Matar zombies primero
    time.sleep(5)      # 🛌 Esperar más tiempo que mueran completamente
    driver = setup_stealth_driver()  # 🆕 Chrome fresco
    print("    ✅ Driver fresco creado")
    return driver

def is_driver_alive(driver):
    """🔍 Verifica si el driver sigue vivo"""
    try:
        driver.current_url
        return True
    except (WebDriverException, Exception):
        return False

def safe_driver_get(driver, url, max_retries=3):
    """🛡️ Navegación segura con reintentos"""
    for attempt in range(max_retries):
        try:
            if not is_driver_alive(driver):
                print(f"    💀 Driver muerto, recreando...")
                driver = setup_fresh_driver()
            
            print(f"    🌐 Navegando a: {url[-50:]}...")
            driver.get(url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print(f"    ✅ Navegación exitosa")
            return driver, True
            
        except Exception as e:
            print(f"    ⚠️ Error navegación (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("    🔄 Recreando driver...")
                driver = setup_fresh_driver()
                time.sleep(5)
            else:
                print("    ❌ Navegación fallida definitivamente")
                return driver, False
    
    return driver, False

def human_like_scroll(driver):
    """Scroll natural como humano - versión LENTA pero SEGURA"""
    print("    🖱️ Scroll humano súper natural...")
    
    try:
        # Verificar que el driver esté vivo
        if not is_driver_alive(driver):
            print("    💀 Driver muerto durante scroll")
            return False
        
        # Scroll más gradual y lento
        for i in range(4):
            scroll_amount = random.randint(150, 350)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(1.5, 3.0))  # Pausas MÁS largas
        
        # Pausa larga en comentarios
        time.sleep(random.uniform(5, 8))  # Tiempo para "leer"
        
        # Scroll final más lento
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 5))  # Pausa extra
        
        # Múltiples movimientos de ratón
        actions = ActionChains(driver)
        for _ in range(2):
            actions.move_by_offset(
                random.randint(50, 300), 
                random.randint(50, 300)
            )
            time.sleep(random.uniform(1.0, 2.0))
        actions.perform()
        
        return True
        
    except Exception as e:
        print(f"    ⚠️ Error en scroll: {e}")
        return False

def wait_for_disqus_to_load(driver, max_wait=DISQUS_TIMEOUT):
    """Espera específicamente a que Disqus cargue completamente - VERSIÓN ROBUSTA"""
    print(f"    ⏳ Esperando Disqus (hasta {max_wait}s)...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # Verificar que el driver esté vivo
            if not is_driver_alive(driver):
                print("    💀 Driver muerto esperando Disqus")
                return False
            
            # Indicadores específicos de Disqus
            disqus_indicators = [
                "#disqus_thread iframe",
                "iframe[src*='disqus.com']",
                "#disqus_thread [id*='disqus']",
                ".disqus-thread"
            ]
            
            for indicator in disqus_indicators:
                elements = driver.find_elements(By.CSS_SELECTOR, indicator)
                if elements and any(el.is_displayed() for el in elements):
                    print(f"    ✅ Disqus detectado: {indicator}")
                    time.sleep(5)  # 🔥 Espera adicional para que cargue completamente
                    return True
            
            # Scroll adicional cada 10 segundos para ayudar a cargar
            if int(time.time() - start_time) % 10 == 0:
                driver.execute_script("window.scrollBy(0, 200);")
                print(f"    🔄 Scroll de ayuda ({int(time.time() - start_time)}s)")
            
            time.sleep(2)  # 🔥 Esperas más largas
            
        except Exception as e:
            print(f"    ⚠️ Error esperando Disqus: {e}")
            return False
    
    print("    ❌ Timeout Disqus")
    return False

def extract_disqus_comments_robust(driver, article_url):
    """🛡️ Extracción ROBUSTA de comentarios desde Disqus"""
    global CURRENT_DRIVER_FAILURES
    
    print(f"  🥷 Extrayendo Disqus: {article_url[-50:]}...")
    
    try:
        # 🔥 NAVEGACIÓN SEGURA
        driver, nav_success = safe_driver_get(driver, article_url)
        if not nav_success:
            print("    ❌ No se pudo navegar al artículo")
            return driver, []
        
        time.sleep(random.uniform(3, 6))  # 🔥 Pausa más larga inicial
        
        # 🔥 FIX: Eliminar iframes molestos que interceptan clicks
        print("    🗑️ Eliminando iframes molestos...")
        try:
            driver.execute_script("""
                // Eliminar iframes de publicidad que bloquean clicks
                var ads = document.querySelectorAll('iframe[src*="guitar_player"]');
                for(var i = 0; i < ads.length; i++) {
                    ads[i].remove();
                }
                
                // Eliminar otros iframes problemáticos
                var problemFrames = document.querySelectorAll('iframe[style*="position"]');
                for(var i = 0; i < problemFrames.length; i++) {
                    if(problemFrames[i].style.position === 'absolute' || problemFrames[i].style.position === 'fixed') {
                        problemFrames[i].remove();
                    }
                }
            """)
            print("    ✅ Iframes molestos eliminados")
        except Exception as e:
            print(f"    ⚠️ No se pudieron eliminar iframes: {e}")
        
        # Buscar y hacer clic en el botón "Ver comentarios" - MÚLTIPLES ESTRATEGIAS
        comment_clicked = False
        
        # Estrategia 1: Selectores múltiples
        button_selectors = [
            "a[href='javascript:void(0)'][title*='comentarios']",
            "a[href='javascript:void(0)'][title*='Ver comentarios']",
            "#disqus-launcher-button",
            "a[id*='disqus-launcher']",
            "button[id*='disqus']",
            ".ft-btn[title*='comentarios']"
        ]
        
        for selector in button_selectors:
            try:
                comment_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"    🖱️ Botón encontrado con: {selector}")
                
                # 🔥 FIX: Usar JavaScript click en lugar de Selenium click
                print("    ⚡ Usando JavaScript click para evitar interceptación...")
                driver.execute_script("arguments[0].scrollIntoView(true);", comment_button)
                time.sleep(2)
                driver.execute_script("arguments[0].click();", comment_button)
                
                comment_clicked = True
                time.sleep(random.uniform(5, 8))  # 🔥 Pausa más larga
                break
                
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                print(f"    ⚠️ Error con botón {selector}: {e}")
                continue
        
        if not comment_clicked:
            print("    ⚠️ No se encontró botón 'Ver comentarios' - buscando Disqus directamente")
        
        # Scroll humano para ayudar a cargar Disqus
        if not human_like_scroll(driver):
            print("    ❌ Error en scroll humano")
            return driver, []
        
        # Esperar a que Disqus cargue
        if not wait_for_disqus_to_load(driver):
            print("    ❌ Disqus no se cargó")
            return driver, []
        
        # 🔥 MANEJO ROBUSTO DE IFRAMES
        iframe = None
        iframe_selectors = [
            "#disqus_thread iframe",
            "iframe[src*='disqus.com']", 
            "iframe[src*='comments']",
            "iframe[id*='dsq']"
        ]
        
        for selector in iframe_selectors:
            try:
                iframes = driver.find_elements(By.CSS_SELECTOR, selector)
                if iframes:
                    iframe = iframes[0]
                    print(f"    ✅ Iframe Disqus: {selector}")
                    break
            except Exception as e:
                print(f"    ⚠️ Error buscando iframe {selector}: {e}")
                continue
        
        if not iframe:
            print("    ❌ Sin iframe de Disqus")
            return driver, []
        
        # 🔥 CAMBIO SEGURO AL IFRAME
        try:
            driver.switch_to.frame(iframe)
            time.sleep(5)  # 🔥 Pausa más larga después del switch
            print("    ✅ Switch a iframe exitoso")
        except Exception as e:
            print(f"    ❌ Error switch a iframe: {e}")
            return driver, []
        
        # Verificar si hay comentarios
        no_comments_indicators = [
            ".no-posts",
            ".empty",
            "[data-role='no-posts']",
            ".post-list:empty"
        ]
        
        for indicator in no_comments_indicators:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, indicator)
                if elements and any(el.is_displayed() for el in elements):
                    print("    📭 Sin comentarios en Disqus")
                    driver.switch_to.default_content()
                    return driver, []
            except Exception as e:
                print(f"    ⚠️ Error verificando no-comments: {e}")
                continue
        
        # Buscar posts/comentarios de Disqus
        post_selectors = [
            ".post",
            "[data-role='post']",
            ".comment",
            ".post-content"
        ]
        
        posts = []
        for selector in post_selectors:
            try:
                posts = driver.find_elements(By.CSS_SELECTOR, selector)
                if posts:
                    print(f"    📝 Encontrados {len(posts)} posts con: {selector}")
                    break
            except Exception as e:
                print(f"    ⚠️ Error buscando posts {selector}: {e}")
                continue
        
        if not posts:
            print("    📭 Sin posts encontrados")
            driver.switch_to.default_content()
            return driver, []
        
        comments = []
        for i, post in enumerate(posts[:15]):  # Máximo 15 comentarios
            try:
                # Autor (adaptado para Disqus)
                author_selectors = [
                    ".author a",
                    ".publisher-anchor-color",
                    ".username",
                    "[data-role='username']"
                ]
                author = "Anónimo"
                for sel in author_selectors:
                    try:
                        author_elems = post.find_elements(By.CSS_SELECTOR, sel)
                        if author_elems:
                            author = author_elems[0].text.strip()
                            break
                    except:
                        continue

                # Fecha/timestamp (adaptado para Disqus)
                date_selectors = [
                    ".timeago",
                    "[data-role='relative-time']",
                    ".post-meta time",
                    ".timestamp"
                ]
                timestamp = ""
                for sel in date_selectors:
                    try:
                        date_elems = post.find_elements(By.CSS_SELECTOR, sel)
                        if date_elems:
                            timestamp = date_elems[0].text.strip()
                            break
                    except:
                        continue

                # Mensaje/contenido (adaptado para Disqus)
                message_selectors = [
                    ".post-body p",
                    ".post-message",
                    ".comment-content",
                    "[data-role='message']"
                ]
                message = ""
                for sel in message_selectors:
                    try:
                        message_elems = post.find_elements(By.CSS_SELECTOR, sel)
                        if message_elems:
                            message = message_elems[0].text.strip()
                            break
                    except:
                        continue

                if message:
                    comments.append({
                        "author": author,
                        "date": timestamp,
                        "text": message,
                        "location": "",  # Disqus no suele mostrar ubicación
                        "likes": 0,      # Mantenemos estructura pero sin datos
                        "dislikes": 0    # Mantenemos estructura pero sin datos
                    })
                    
            except Exception as e:
                print(f"    ⚠️ Error procesando post {i}: {e}")
                continue
        
        # 🔥 SWITCH SEGURO DE VUELTA
        try:
            driver.switch_to.default_content()
            print("    ✅ Switch de vuelta exitoso")
        except Exception as e:
            print(f"    ⚠️ Error switch de vuelta: {e}")
        
        print(f"    🎉 Extraídos: {len(comments)} comentarios de Disqus")
        
        # 🔥 RESETEAR CONTADOR DE FALLOS SI TODO VA BIEN
        CURRENT_DRIVER_FAILURES = 0
        
        return driver, comments
        
    except Exception as e:
        print(f"    ❌ Error crítico extracción Disqus: {e}")
        
        # 🔥 INCREMENTAR CONTADOR DE FALLOS
        CURRENT_DRIVER_FAILURES += 1
        print(f"    📊 Fallos acumulados: {CURRENT_DRIVER_FAILURES}/{MAX_DRIVER_FAILURES}")
        
        # 🔥 SI HAY MUCHOS FALLOS, RECREAR DRIVER
        if CURRENT_DRIVER_FAILURES >= MAX_DRIVER_FAILURES:
            print(f"    🔄 Demasiados fallos, recreando driver...")
            driver = setup_fresh_driver()
            CURRENT_DRIVER_FAILURES = 0
        
        try:
            driver.switch_to.default_content()
        except:
            pass
        
        return driver, []

def is_valid_article(article_soup):
    """Filtra artículos según los criterios especificados"""
    
    # Verificar headers prohibidos
    header_elem = article_soup.find("header")
    if header_elem:
        header_link = header_elem.find("a", class_="new__topic")
        if header_link:
            header_text = header_link.get_text(strip=True).upper()
            
            # Headers prohibidos - todo lo demás es permitido
            forbidden_headers = ["GALICIA", "GRAN VIGO", "MORRAZO", "AROUSA",
                                 "OURENSE", "DEZA-TABEIRÓS", "DEPORTES DEZA",
                                 "GALERÍAS HISTÓRICAS"]
            if any(forbidden in header_text for forbidden in forbidden_headers):
                print(f"    🚫 Header prohibido: {header_text}")
                return False
            else:
                print(f"    ✅ Header permitido: {header_text}")
                return True
    
    print("    ✅ Sin header - permitido por defecto")
    return True

def scrape_faro_vigo_marin_robust(base_url="https://www.farodevigo.es/pontevedra/marin/pagina-",
                                  date_threshold=DATE_THRESHOLD,
                                  max_pages=MAX_PAGES,
                                  max_old_articles=MAX_OLD_ARTICLES):
    """
    🛡️ Scraper ROBUSTO para Faro de Vigo - sección Marín
    
    MEJORAS ANTI-CRASH:
    - Manejo robusto de errores de driver
    - Timeouts más largos para Disqus
    - Verificación de estado del driver
    - Recreación automática cuando sea necesario
    - Pausas más largas entre operaciones
    """
    
    print("🛡️ FARO DE VIGO SCRAPER ROBUSTO - MARÍN")
    print(f"📅 Umbral de fecha: {date_threshold.date()}")
    print(f"📄 Máximo páginas: {max_pages}")
    print(f"🚫 Máximo artículos viejos consecutivos: {max_old_articles}")
    print(f"⏰ Delays entre artículos: {INTER_ARTICLE_DELAY[0]}-{INTER_ARTICLE_DELAY[1]}s")
    print(f"🕒 Timeout Disqus: {DISQUS_TIMEOUT}s")
    
    # 🔥 INICIALIZAR DRIVER FRESCO SIN ZOMBIES
    driver = setup_fresh_driver()
    all_rows = []
    seen_links = set()
    old_articles = 0
    total_processed = 0

    try:
        for page in range(1, max_pages + 1):
            url = f"{base_url}{page}/"
            print(f"\n🔄 Página {page}: {url}")
    
            # Renovar sesión periódicamente - MÁS CONSERVADOR
            if page > 1 and page % 3 == 0:  # 🔥 Cada 3 páginas en lugar de 5
                print("🔄 Nueva sesión preventiva...")
                driver = setup_fresh_driver()
                print("    ✅ Sesión renovada")
    
            # 🔥 NAVEGACIÓN ROBUSTA
            driver, nav_success = safe_driver_get(driver, url)
            if not nav_success:
                print(f"❌ Error crítico navegando a página {page} - saltando")
                continue
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Buscar artículos, excluyendo widgets
            articles = soup.find_all("article", class_="lst")
            
            # Filtrar widgets irrelevantes
            valid_articles = []
            for article in articles:
                # Skip weather y drugstore widgets
                if article.find(class_=lambda x: x and ("weather-widget" in x or "drugstore-widget" in x)):
                    print("    🚫 Skipping widget (weather/drugstore)")
                    continue
                
                # Verificar si es artículo válido
                if is_valid_article(article):
                    valid_articles.append(article)
            
            print(f"🔗 Artículos válidos encontrados: {len(valid_articles)}")

            if not valid_articles:
                print("❌ No se encontraron artículos válidos. Continuando...")
                continue

            from dateutil.parser import parse as date_parse

            for article in valid_articles:
                # Extraer enlace - MEJORADO: buscar enlace específico del artículo
                link_elem = None
                
                # Estrategia 1: Buscar enlace en el título
                title_link = article.find("h1 a") or article.find("h2 a") or article.find("h3 a")
                if title_link and title_link.get("href"):
                    link_elem = title_link
                
                # Estrategia 2: Buscar enlace con clase específica de artículo
                if not link_elem:
                    specific_links = article.find_all("a", href=True)
                    for link in specific_links:
                        href = link.get("href", "")
                        # Filtrar enlaces que parecen de artículos (tienen fecha o ID)
                        if any(pattern in href for pattern in ["/2025/", "/2024/", "-118", "pontevedra"]) and not any(bad in href for bad in ["/opinion/", "/deportes/", "/galicia/"]):
                            link_elem = link
                            break
                
                # Estrategia 3: Fallback al primer enlace válido
                if not link_elem:
                    all_links = article.find_all("a", href=True)
                    for link in all_links:
                        href = link.get("href", "")
                        if href.startswith("/") and len(href) > 10:  # Enlaces internos largos
                            link_elem = link
                            break
                
                if not link_elem:
                    print("    ⚠️ No se encontró enlace válido - skipping")
                    continue
                
                href = link_elem["href"]
                # Construir URL completa si es relativa
                if href.startswith("/"):
                    full_url = f"https://www.farodevigo.es{href}"
                else:
                    full_url = href

                # 🔥 VALIDACIÓN: Verificar que es un enlace de artículo válido
                invalid_patterns = [
                    "/opinion/",
                    "/deportes/", 
                    "/galicia/",
                    "/gran-vigo/",
                    "/economia/",
                    "/sociedad/",
                    "/actualidad/",
                    "/o-morrazo/",
                ]
                
                # Si el enlace termina solo con la sección (sin artículo específico)
                if any(full_url.endswith(pattern) for pattern in invalid_patterns):
                    print(f"    🚫 Enlace de sección detectado: {full_url[-30:]}... - skipping")
                    continue
                
                # Verificar que parece un artículo (tiene ID numérico o fecha)
                if not any(pattern in full_url for pattern in ["-118", "/2025/", "/2024/"]):
                    print(f"    ⚠️ Enlace sospechoso (sin ID/fecha): {full_url[-50:]}... - skipping")
                    continue

                if full_url in seen_links:
                    print(f"⏭️ Ya procesado: {full_url[-30:]}...")
                    continue
                seen_links.add(full_url)
                
                print(f"🔗 Procesando: {full_url[-50:]}...")

                # Extraer fecha
                date_elem = article.find("time")
                if date_elem:
                    date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
                else:
                    # Buscar en meta tags
                    meta_date = article.find("meta", attrs={"itemprop": "datePublished"})
                    date_str = meta_date["content"] if meta_date else ""

                try:
                    if date_str:
                        date = date_parse(date_str)
                    else:
                        print(f"⚠️ Sin fecha encontrada → usando fecha actual")
                        date = datetime.now()
                    print(f"📅 Fecha del artículo: {date.date()}")
                except Exception as e:
                    print(f"⚠️ Error parseando fecha '{date_str}': {e} → usando fecha actual")
                    date = datetime.now()

                # Verificar umbral de fecha
                if date.date() < date_threshold.date():
                    print(f"🚫 Artículo anterior al umbral ({date_threshold.date()})")
                    old_articles += 1
                    if old_articles >= max_old_articles:
                        print(f"🏁 Límite de artículos antiguos alcanzado: {max_old_articles}. Finalizando.")
                        
                        # Guardar antes de salir
                        if all_rows:
                            df = pd.DataFrame(all_rows)
                            df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
                            print(f"✅ Guardado CSV final: {OUTPUT_PATH} con {len(df)} artículos")
                        
                        kill_all_chrome()
                        return
                    continue
                else:
                    old_articles = 0

                # Procesar artículo válido
                try:
                    total_processed += 1
                    print(f"\n🎯 PROCESANDO ARTÍCULO #{total_processed}")
                    
                    # 🔥 EXTRACCIÓN ROBUSTA DE COMENTARIOS
                    driver, comments = extract_disqus_comments_robust(driver, full_url)
                    
                    # Extraer título de manera segura
                    try:
                        if is_driver_alive(driver):
                            title = driver.title or "Sin título"
                        else:
                            title = "Sin título"
                    except Exception as e:
                        print(f"    ⚠️ Error obteniendo título: {e}")
                        title = "Sin título"

                    # 🔥 NUEVA ESTRATEGIA: Guardar TODOS los artículos, tengan o no comentarios
                    if len(comments) == 0:
                        print(f"    ⚠️ Artículo sin comentarios - guardando IGUAL para análisis")
                    else:
                        print(f"    ✅ Artículo CON {len(comments)} comentarios - guardando")

                    # Crear fila de datos (misma estructura que Diario Pontevedra)
                    row = {
                        "source": "Faro de Vigo",
                        "title": title,
                        "link": full_url,
                        "date": date.isoformat(),
                        "n_comments": len(comments)
                    }
                    
                    # Inicializar columnas de comentarios (estructura idéntica)
                    for i in range(15):
                        row[f"comment_{i+1}_author"] = ""
                        row[f"comment_{i+1}_location"] = ""
                        row[f"comment_{i+1}_date"] = ""
                        row[f"comment_{i+1}_text"] = ""
                        row[f"comment_{i+1}_likes"] = 0
                        row[f"comment_{i+1}_dislikes"] = 0

                    # Llenar comentarios
                    for i, comment in enumerate(comments[:15]):
                        row[f"comment_{i+1}_author"] = comment["author"]
                        row[f"comment_{i+1}_location"] = comment["location"]
                        row[f"comment_{i+1}_date"] = comment["date"]
                        row[f"comment_{i+1}_text"] = comment["text"]
                        row[f"comment_{i+1}_likes"] = comment["likes"]
                        row[f"comment_{i+1}_dislikes"] = comment["dislikes"]

                    all_rows.append(row)
                    print(f"✅ Artículo #{total_processed} GUARDADO: {len(comments)} comentarios")
                    
                    # 🔥 PAUSAS MÁS LARGAS ANTI-DETECCIÓN
                    pause_time = random.uniform(INTER_ARTICLE_DELAY[0], INTER_ARTICLE_DELAY[1])
                    print(f"😴 Pausa humana LARGA: {pause_time:.1f}s...")
                    time.sleep(pause_time)
                    
                    # Renovar sesión periódicamente - MÁS CONSERVADOR
                    if total_processed % 5 == 0:  # 🔥 Cada 5 artículos en lugar de 8
                        print(f"🔄 RENOVANDO SESIÓN después de {total_processed} artículos...")
                        driver = setup_fresh_driver()
                        print("    ✅ Nueva sesión establecida")
                    
                except Exception as e:
                    print(f"⚠️ Error procesando artículo: {e}")
                    continue
                    
    finally:
        # 🔥 CIERRE BRUTAL: Matar todo Chrome
        print("🔄 Finalizando - matando todos los Chrome...")
        kill_all_chrome()

    # Guardar resultados finales
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
        
        articles_with_comments = len(df[df['n_comments'] > 0])
        articles_without_comments = len(df[df['n_comments'] == 0])
        
        print(f"\n🎉 SCRAPING COMPLETADO:")
        print(f"   📊 Total artículos procesados: {total_processed}")
        print(f"   ✅ Artículos CON comentarios: {articles_with_comments}")
        print(f"   📝 Artículos SIN comentarios: {articles_without_comments}")
        print(f"   💬 Total comentarios extraídos: {sum(row['n_comments'] for row in all_rows)}")
        print(f"   💾 Archivo guardado: {OUTPUT_PATH}")
    else:
        print(f"\n😞 No se encontraron artículos en {total_processed} procesados")

if __name__ == "__main__":
    scrape_faro_vigo_marin_robust()