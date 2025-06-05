from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import os
import time
import random
import re

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
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "diario-pontevedra-stealth-completo.csv")

# CONFIGURACIÓN PRINCIPAL
DATE_THRESHOLD = datetime(2025, 5, 24)  # Fecha umbral - procesar artículos >= esta fecha
MAX_PAGES = 50  # Máximo número de páginas a revisar
MAX_OLD_ARTICLES = 3  # Máximo artículos consecutivos anteriores al umbral antes de parar

def setup_stealth_driver_undetected():
    """Versión con undetected-chromedriver"""
    print("🥷 Configurando driver UNDETECTED...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")
    
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
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
    
    prefs = {
        "profile.default_content_setting_values": {"notifications": 2},
        "profile.managed_default_content_settings": {"images": 1}
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']})")
    
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
    return driver

def setup_stealth_driver():
    """Función principal - elige la mejor opción disponible"""
    if UNDETECTED_AVAILABLE:
        return setup_stealth_driver_undetected()
    else:
        return setup_stealth_driver_manual()

def human_like_scroll(driver):
    """Scroll natural como humano - versión LENTA"""
    print("    🖱️ Scroll humano súper natural...")
    
    # Scroll más gradual y lento
    for i in range(4):
        scroll_amount = random.randint(150, 350)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.8, 2.5))  # Pausas más largas
    
    # Pausa larga en comentarios
    time.sleep(random.uniform(3, 6))  # Tiempo para "leer"
    
    # Scroll final más lento
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(2, 4))  # Pausa extra
    
    # Múltiples movimientos de ratón
    try:
        actions = ActionChains(driver)
        for _ in range(2):
            actions.move_by_offset(
                random.randint(50, 300), 
                random.randint(50, 300)
            )
            time.sleep(random.uniform(0.5, 1.5))
        actions.perform()
    except:
        pass

def wait_for_comments_to_load(driver, max_wait=40):
    """Espera inteligente para que carguen los comentarios"""
    print("    ⏳ Esperando comentarios (hasta 40s)...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        indicators = [
            "iframe[id*='onmcomments']",
            "iframe[src*='comments']", 
            "#conversation",
            ".post-list"
        ]
        
        for indicator in indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements:
                print(f"    ✅ Comentarios detectados: {indicator}")
                return True
        
        # Scroll adicional cada 5 segundos
        if time.time() - start_time > 5:
            driver.execute_script("window.scrollBy(0, 50);")
        
        time.sleep(1)
    
    print("    ❌ Timeout comentarios")
    return False

def extract_comments_stealth(driver, article_url):
    """Extracción stealth de comentarios"""
    print(f"  🥷 Extrayendo: {article_url[-50:]}...")
    
    try:
        # Navegar con comportamiento humano
        driver.get(article_url)
        time.sleep(random.uniform(1, 3))
        
        # Verificar widget de comentarios
        widget_headers = driver.find_elements(By.CSS_SELECTOR, ".widget-header")
        has_comments = False
        for header in widget_headers:
            if "COMENTARIOS" in header.text.upper():
                has_comments = True
                print(f"    ✅ Widget: '{header.text}'")
                break
        
        if not has_comments:
            print("    🚫 Sin widget comentarios")
            return []
        
        # Scroll humano
        human_like_scroll(driver)
        
        # Esperar comentarios
        if not wait_for_comments_to_load(driver):
            print("    ❌ No se cargaron comentarios")
            return []
        
        # Buscar iframe
        iframe_selectors = [
            "iframe[id^='onmcomments-']",
            "iframe[src*='/comments/get/']",
            "iframe[src*='comment']"
        ]
        
        iframe = None
        for selector in iframe_selectors:
            iframes = driver.find_elements(By.CSS_SELECTOR, selector)
            if iframes:
                iframe = iframes[0]
                print(f"    ✅ Iframe: {selector}")
                break
        
        if not iframe:
            print("    ❌ Sin iframe")
            return []
        
        # Extraer del iframe
        driver.switch_to.frame(iframe)
        time.sleep(1)
        
        # Verificar no-posts
        no_posts = driver.find_elements(By.ID, "no-posts")
        if no_posts and no_posts[0].is_displayed():
            print("    📭 Sin comentarios (no-posts)")
            driver.switch_to.default_content()
            return []
        
        # Extraer posts
        posts = driver.find_elements(By.CSS_SELECTOR, "#post-list .post")
        if not posts:
            print("    📭 Sin posts")
            driver.switch_to.default_content()
            return []
        
        print(f"    📝 Extrayendo {len(posts)} comentarios...")
        
        comments = []
        for i, post in enumerate(posts[:15]):
            try:
                # Autor
                author_elems = post.find_elements(By.CSS_SELECTOR, ".comment-author-name")
                author = "Anónimo"
                if author_elems:
                    author = author_elems[0].text.strip()
                    if ". " in author and author[0].isdigit():
                        author = author.split(". ", 1)[1]

                # Fecha
                date_elems = post.find_elements(By.CSS_SELECTOR, ".content-meta-date")
                time_elems = post.find_elements(By.CSS_SELECTOR, ".content-meta-time")
                date_text = date_elems[0].text.strip() if date_elems else ""
                time_text = time_elems[0].text.strip() if time_elems else ""
                timestamp = f"{date_text} {time_text}".strip()

                # Mensaje
                message_elems = post.find_elements(By.CSS_SELECTOR, ".post-message p")
                if not message_elems:
                    message_elems = post.find_elements(By.CSS_SELECTOR, ".post-message")
                message = message_elems[0].text.strip() if message_elems else ""

                # Likes
                like_elems = post.find_elements(By.CSS_SELECTOR, '[data-role="likes"]')
                likes = 0
                if like_elems:
                    like_text = like_elems[0].text.strip()
                    if like_text and like_text.isdigit():
                        likes = int(like_text)
                
                # Dislikes
                dislike_elems = post.find_elements(By.CSS_SELECTOR, '[data-role="dislikes"]')
                dislikes = 0
                if dislike_elems:
                    dislike_text = dislike_elems[0].text.strip()
                    if dislike_text and dislike_text.isdigit():
                        dislikes = int(dislike_text)

                if message:
                    comments.append({
                        "author": author,
                        "date": timestamp,
                        "text": message,
                        "location": "",
                        "likes": likes,
                        "dislikes": dislikes
                    })
                    
            except Exception as e:
                print(f"    ⚠️ Error post {i}: {e}")
                continue
        
        driver.switch_to.default_content()
        print(f"    🎉 Extraídos: {len(comments)} comentarios")
        return comments
        
    except Exception as e:
        print(f"    ❌ Error extracción: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return []

def scrape_multiple_articles_stealth(base_url="https://www.diariodepontevedra.es/tags/marin/",
                                    date_threshold=DATE_THRESHOLD,
                                    max_pages=MAX_PAGES,
                                    max_old_articles=MAX_OLD_ARTICLES):
    """
    Scraper principal con técnicas ANTI-DETECCIÓN AVANZADAS:
    
    🥷 ESTRATEGIAS IMPLEMENTADAS:
    - Pausas largas (5-15s) entre artículos
    - Renovación de sesión cada 8 artículos
    - Timeout extendido (40s) para comentarios  
    - Actividad humana simulada cada 5 artículos
    - Scroll súper lento y natural
    - Movimientos de ratón múltiples
    
    ¡A ver si logran detectar esto! 😈
    """
    
    print("🥷 SCRAPER STEALTH ANTI-DETECCIÓN NIVEL DIOS")
    print(f"📅 Umbral de fecha: {date_threshold.date()}")
    print(f"📄 Máximo páginas: {max_pages}")
    print(f"🚫 Máximo artículos viejos consecutivos: {max_old_articles}")
    print("🕰️ MODO ULTRA-LENTO ACTIVADO (pausas 5-15s)")
    
    driver = setup_stealth_driver()
    all_rows = []
    seen_links = set()
    old_articles = 0
    total_processed = 0

    try:
        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            print(f"\n🔄 Página {page}: {url}")
            
            # Pausa antes de cargar nueva página (comportamiento humano)
            if page > 1:
                page_pause = random.uniform(3, 8)
                print(f"    📖 Leyendo página anterior... ({page_pause:.1f}s)")
                time.sleep(page_pause)
            
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            container = soup.select_one("div.content-col.col-12.col-lg.stick")
            
            if not container:
                print("❌ No se encontró contenedor. Parando...")
                break

            # Obtener enlaces de artículos
            article_links = []
            for a in container.select("div.archive-item h2.title a[href^='/articulo/']"):
                href = a["href"]
                full_url = f"https://www.diariodepontevedra.es{href}"
                if full_url not in article_links:
                    article_links.append(full_url)

            print(f"🔗 Encontrados {len(article_links)} enlaces")

            if not article_links:
                print("❌ No se encontraron artículos. Parando...")
                break

            from dateutil.parser import parse as date_parse

            for article in container.select("div.archive-item"):
                a = article.select_one("h2.title a[href^='/articulo/']")
                date_span = article.select_one("span.date-container")

                if not a or not date_span:
                    continue

                href = a["href"]
                full_url = f"https://www.diariodepontevedra.es{href}"

                if full_url in seen_links:
                    print(f"⏭️ Ya procesado: {full_url[-50:]}...")
                    continue
                seen_links.add(full_url)

                # Parsear fecha
                raw_date = date_span.get_text(strip=True)
                raw_date = re.sub(r'(\d{2}/\w{3}/\d{2})(\d{1,2}:\d{2})', r'\1 \2', raw_date)

                try:
                    date = date_parse(raw_date, dayfirst=True)
                    print(f"📅 Fecha del artículo: {date.date()}")
                except Exception:
                    print(f"⚠️ No se pudo parsear fecha '{raw_date}' → usando fecha actual")
                    date = datetime.now()

                # Verificar si es anterior al umbral
                if date.date() < date_threshold.date():
                    print(f"🚫 Artículo anterior al umbral ({date_threshold.date()})")
                    old_articles += 1
                    if old_articles >= max_old_articles:
                        print(f"🏁 Límite de artículos antiguos consecutivos alcanzado: {max_old_articles}. Finalizando.")
                        
                        # Guardar antes de salir
                        if all_rows:
                            df = pd.DataFrame(all_rows)
                            df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
                            print(f"✅ Guardado CSV final: {OUTPUT_PATH} con {len(df)} artículos")
                        
                        driver.quit()
                        return
                    continue
                else:
                    old_articles = 0

                # Procesar artículo válido
                try:
                    total_processed += 1
                    print(f"\n🎯 PROCESANDO ARTÍCULO #{total_processed}")
                    
                    # Extraer comentarios con stealth
                    comments = extract_comments_stealth(driver, full_url)
                    
                    # Obtener título
                    article_soup = BeautifulSoup(driver.page_source, "html.parser")
                    title = article_soup.title.string.strip() if article_soup.title else ""

                    # Crear fila de datos
                    row = {
                        "source": "Diario de Pontevedra",
                        "title": title,
                        "link": full_url,
                        "date": date.isoformat(),
                        "n_comments": len(comments)
                    }
                    
                    # Inicializar columnas de comentarios
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
                    print(f"✅ Artículo #{total_processed} procesado: {len(comments)} comentarios")
                    
                    # OPCIÓN 1: Pausas más largas entre artículos (5-15 segundos)
                    pause_time = random.uniform(5, 15)
                    print(f"😴 Pausa humana: {pause_time:.1f}s...")
                    time.sleep(pause_time)
                    
                    # OPCIÓN 2: Renovar sesión cada 8 artículos para evitar detección
                    if total_processed % 5 == 0:
                        print(f"🔄 RENOVANDO SESIÓN después de {total_processed} artículos...")
                        driver.quit()
                        print("    🛌 Pausa larga entre sesiones...")
                        time.sleep(random.uniform(10, 20))  # Pausa extra entre sesiones
                        driver = setup_stealth_driver()
                        print("    ✅ Nueva sesión establecida")
                    
                    # BONUS: Actividad humana ocasional (cada 5 artículos)
                    elif total_processed % 5 == 0:
                        print("🤖 Simulando actividad humana...")
                        # Visitar página principal brevemente
                        driver.get("https://www.diariodepontevedra.es/")
                        time.sleep(random.uniform(2, 5))
                        # Scroll aleatorio en página principal
                        driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)});")
                        time.sleep(random.uniform(1, 3))
                        print("    ✅ Actividad humana completada")
                    
                except Exception as e:
                    print(f"⚠️ Error procesando artículo: {e}")
                    continue
                    
    finally:
        driver.quit()

    # Guardar resultados finales
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
        
        print(f"\n🎉 SCRAPING COMPLETADO:")
        print(f"   📊 Total artículos procesados: {total_processed}")
        print(f"   ✅ Artículos con datos: {len(df)}")
        print(f"   💬 Total comentarios extraídos: {sum(row['n_comments'] for row in all_rows)}")
        print(f"   💾 Archivo guardado: {OUTPUT_PATH}")
    else:
        print("\n😞 No se extrajeron datos")

if __name__ == "__main__":
    scrape_multiple_articles_stealth()