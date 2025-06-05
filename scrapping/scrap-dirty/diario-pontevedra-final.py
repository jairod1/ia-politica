from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import os
import time

OUTPUT_DIR = os.path.join("..", "..", "data", "raw", "dirty-csvs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "diario-pontevedra-mayo17.csv")

# FECHA ESPECÍFICA: Solo artículos del 17 de mayo de 2025
TARGET_DATE = date(2025, 5, 17)

def setup_driver():
    options = Options()
    
    # Configuración básica
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Mejorar compatibilidad con contenido dinámico e iframes
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-iframes-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    
    # User agent actualizado
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Configurar preferencias para mejor manejo de JavaScript e iframes
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,  # Bloquear notificaciones
        },
        "profile.managed_default_content_settings": {
            "images": 2  # Deshabilitar imágenes para mejorar velocidad
        }
    }
    options.add_experimental_option("prefs", prefs)
    
    # Timeouts más generosos
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)  # Aumentar timeout de carga de página
    driver.implicitly_wait(10)  # Espera implícita para elementos
    
    return driver

def extract_comments(driver):
    try:
        # Esperar a que cargue la página
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # PASO 1: Verificar si tiene comentarios habilitados
        widget_headers = driver.find_elements(By.CSS_SELECTOR, ".widget-header")
        comments_enabled = False
        
        for header in widget_headers:
            header_text = header.text.strip().upper()
            if "COMENTARIOS" in header_text:
                comments_enabled = True
                print(f"✅ Comentarios habilitados (encontrado: '{header.text}')")
                break
        
        if not comments_enabled:
            print("🚫 Artículo sin comentarios habilitados")
            return []
        
        # Justo antes de buscar el iframe:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        print("🔍 Esperando iframe con Selenium tras scroll...")
        try:
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='onmcomments-']"))
            )
            iframe_id = iframe.get_attribute("id")
            print(f"✅ Iframe encontrado: {iframe_id}")
        except TimeoutException:
            print("❌ No se encontró iframe con Selenium tras scroll")
            return []
        
        # if not iframe_elements:
        #     print("❌ No se encontró iframe de comentarios")
        #     return []
        
        # iframe = iframe_elements[0]
        # iframe_id = iframe.get_attribute("id")
        # print(f"✅ Iframe encontrado: {iframe_id}")
        
        # PASO 3: Entrar al iframe y extraer comentarios
        driver.switch_to.frame(iframe)
        
        # Esperar contenido del iframe
        try:
            WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "post-list")),
                    EC.presence_of_element_located((By.ID, "no-posts"))
                )
            )
            time.sleep(1)
        except TimeoutException:
            print("⚠️ Timeout esperando contenido del iframe")
            driver.switch_to.default_content()
            return []
        
        # Verificar si hay mensaje de "sin comentarios"
        no_posts_elements = driver.find_elements(By.ID, "no-posts")
        if no_posts_elements:
            no_posts_elem = no_posts_elements[0]
            if no_posts_elem.is_displayed():
                print("📭 Sin comentarios (mensaje no-posts visible)")
                driver.switch_to.default_content()
                return []
        
        # Buscar comentarios
        posts = driver.find_elements(By.CSS_SELECTOR, "#post-list .post")
        
        if not posts:
            print("📭 No se encontraron elementos .post")
            driver.switch_to.default_content()
            return []
        
        print(f"📝 Encontrados {len(posts)} comentarios, procesando...")
        
        # PASO 4: PROCESAR COMENTARIOS
        comments = []
        
        for i, post_elem in enumerate(posts[:15]):
            try:
                # Autor
                author_elems = post_elem.find_elements(By.CSS_SELECTOR, ".comment-author-name")
                author = "Anónimo"
                if author_elems:
                    author = author_elems[0].text.strip()
                    # Limpiar numeración (ej: "1. jairod" -> "jairod")
                    if ". " in author and author[0].isdigit():
                        author = author.split(". ", 1)[1]

                # Fecha + hora
                date_elems = post_elem.find_elements(By.CSS_SELECTOR, ".content-meta-date")
                time_elems = post_elem.find_elements(By.CSS_SELECTOR, ".content-meta-time")
                
                date_text = date_elems[0].text.strip() if date_elems else ""
                time_text = time_elems[0].text.strip() if time_elems else ""
                timestamp = f"{date_text} {time_text}".strip()

                # Texto del comentario
                message_elems = post_elem.find_elements(By.CSS_SELECTOR, ".post-message p")
                if not message_elems:
                    message_elems = post_elem.find_elements(By.CSS_SELECTOR, ".post-message")
                message = message_elems[0].text.strip() if message_elems else ""

                # Likes
                like_elems = post_elem.find_elements(By.CSS_SELECTOR, '[data-role="likes"]')
                likes = 0
                if like_elems:
                    like_text = like_elems[0].text.strip()
                    if like_text and like_text.isdigit():
                        likes = int(like_text)

                # Dislikes
                dislike_elems = post_elem.find_elements(By.CSS_SELECTOR, '[data-role="dislikes"]')
                dislikes = 0
                if dislike_elems:
                    dislike_text = dislike_elems[0].text.strip()
                    if dislike_text and dislike_text.isdigit():
                        dislikes = int(dislike_text)

                # Solo añadir si tiene contenido real
                if author != "Anónimo" or message:
                    comments.append({
                        "author": author,
                        "date": timestamp,
                        "text": message,
                        "location": "",
                        "likes": likes,
                        "dislikes": dislikes
                    })
                    print(f"✅ Comentario {len(comments)}: {author} - '{message[:30]}...' - {likes} likes")
                
            except Exception as e:
                print(f"⚠️ Error procesando comentario {i+1}: {str(e)}")
                continue

        # Volver al contexto principal
        driver.switch_to.default_content()
        
        print(f"🎉 Total extraídos: {len(comments)} comentarios")
        return comments
        
    except Exception as e:
        print(f"⚠️ Error inesperado: {type(e).__name__} - {str(e)}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return []

def scrape_multiple_articles(base_url="https://www.diariodepontevedra.es/tags/marin/",
                             target_date=TARGET_DATE,
                             max_pages=10):
    driver = setup_driver()
    all_rows = []
    seen_links = set()
    articles_found_target_date = 0
    articles_processed = 0

    try:
        print(f"🎯 Buscando artículos específicamente del: {target_date}")
        
        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            print(f"🔄 Página {page}: {url}")
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            container = soup.select_one("div.content-col.col-12.col-lg.stick")
            article_links = []

            if container:
                for a in container.select("div.archive-item h2.title a[href^='/articulo/']"):
                    href = a["href"]
                    full_url = f"https://www.diariodepontevedra.es{href}"
                    if full_url not in article_links:
                        article_links.append(full_url)

            print(f"🔗 Encontrados {len(article_links)} enlaces en el contenedor principal.")

            if not article_links:
                print("❌ No se encontraron artículos. Parando...")
                break

            from dateutil.parser import parse as date_parse

            page_has_target_date = False
            
            for article in container.select("div.archive-item"):
                a = article.select_one("h2.title a[href^='/articulo/']")
                date_span = article.select_one("span.date-container")

                if not a or not date_span:
                    continue

                href = a["href"]
                full_url = f"https://www.diariodepontevedra.es{href}"

                if full_url in seen_links:
                    print(f"⏭️ Artículo ya procesado: {full_url}")
                    continue
                seen_links.add(full_url)

                # 🕒 Extraer y parsear fecha del listado
                raw_date = date_span.get_text(strip=True)

                # ✅ Separar fecha y hora si están pegadas
                import re
                raw_date = re.sub(r'(\d{2}/\w{3}/\d{2})(\d{1,2}:\d{2})', r'\1 \2', raw_date)

                try:
                    parsed_date = date_parse(raw_date, dayfirst=True)
                    article_date = parsed_date.date()
                    print(f"📅 Fecha del artículo: {article_date}")
                except Exception:
                    print(f"⚠️ No se pudo parsear la fecha '{raw_date}' → saltando artículo.")
                    continue

                # 🎯 Verificar si es exactamente la fecha objetivo
                if article_date == target_date:
                    page_has_target_date = True
                    articles_found_target_date += 1
                    print(f"🎯 ¡ARTÍCULO DEL {target_date}! Procesando...")
                    
                    # ✅ Procesar el artículo
                    try:
                        driver.get(full_url)
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        article_soup = BeautifulSoup(driver.page_source, "html.parser")

                        comments = extract_comments(driver)
                        title = article_soup.title.string.strip() if article_soup.title else ""

                        row = {
                            "source": "Diario de Pontevedra",
                            "title": title,
                            "link": full_url,
                            "date": parsed_date.isoformat(),
                            "n_comments": len(comments)
                        }
                        for i in range(15):
                            row[f"comment_{i+1}_author"] = ""
                            row[f"comment_{i+1}_location"] = ""
                            row[f"comment_{i+1}_date"] = ""
                            row[f"comment_{i+1}_text"] = ""
                            row[f"comment_{i+1}_likes"] = 0
                            row[f"comment_{i+1}_dislikes"] = 0

                        for i, comment in enumerate(comments[:15]):
                            row[f"comment_{i+1}_author"] = comment["author"]
                            row[f"comment_{i+1}_location"] = comment["location"]
                            row[f"comment_{i+1}_date"] = comment["date"]
                            row[f"comment_{i+1}_text"] = comment["text"]
                            row[f"comment_{i+1}_likes"] = comment["likes"]
                            row[f"comment_{i+1}_dislikes"] = comment["dislikes"]

                        all_rows.append(row)
                        articles_processed += 1
                        print(f"✅ Artículo #{articles_processed} procesado con {len(comments)} comentarios")
                        
                    except Exception as e:
                        print(f"⚠️ Error procesando artículo: {e}")
                        continue
                        
                elif article_date < target_date:
                    print(f"📍 Artículo anterior a {target_date}: {article_date} - continuando búsqueda")
                    continue
                else:
                    print(f"📍 Artículo posterior a {target_date}: {article_date} - continuando búsqueda")
                    continue
            
            # Si no encontramos artículos de la fecha objetivo en esta página, continuar
            if not page_has_target_date and articles_found_target_date == 0:
                print(f"📄 Página {page}: No se encontraron artículos del {target_date}")
            elif articles_found_target_date > 0 and not page_has_target_date:
                print(f"🔚 Ya no hay más artículos del {target_date}. Finalizando búsqueda.")
                break
                
    finally:
        driver.quit()

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\n🎉 RESUMEN FINAL:")
    print(f"   📊 Artículos del {target_date} encontrados: {articles_found_target_date}")
    print(f"   ✅ Artículos procesados exitosamente: {articles_processed}")
    print(f"   💾 Guardado CSV en: {OUTPUT_PATH}")

if __name__ == "__main__":
    scrape_multiple_articles()