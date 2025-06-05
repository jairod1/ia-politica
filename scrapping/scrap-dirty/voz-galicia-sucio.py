from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time
import re

# Configuración original
OUTPUT_DIR = os.path.join("..", "data", "csvs-sucios")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "voz_galicia_sucio.csv")
DATE_THRESHOLD = datetime(2025, 5, 15)

def setup_driver():
    """Configura Selenium con JavaScript habilitado para comentarios dinámicos"""
    chrome_options = Options()
    
    # Configuración básica - HABILITANDO JavaScript
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Headers realistas
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"--user-agent={user_agent}")
    
    # Anti-detección pero permitiendo JavaScript
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ ChromeDriver iniciado con JavaScript habilitado")
    except Exception as e:
        print(f"❌ Error iniciando ChromeDriver: {e}")
        raise
    
    # Scripts anti-detección
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def wait_for_comments_to_load(driver, max_wait=30):
    """Espera agresivamente a que los comentarios se carguen"""
    print("🔄 Esperando carga dinámica de comentarios...")
    
    # Lista de selectores posibles para comentarios
    comment_selectors = [
        'dd.comment',
        'dd[class*="comment"]',
        '.comment-content',
        '[class*="comment"]',
        'div[id*="comment"]',
        '.comentario',
        '[class*="comentario"]'
    ]
    
    # Intentar multiple veces con diferentes estrategias
    for attempt in range(6):
        print(f"   🔄 Intento {attempt + 1}/6...")
        
        # Hacer scroll hasta abajo
        for i in range(10):
            driver.execute_script(f"window.scrollBy(0, {i * 200});")
            time.sleep(0.3)

        
        # Buscar botones que puedan cargar comentarios
        try:
            load_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "button[class*='comment'], button[class*='cargar'], button[class*='load'], .load-more, .show-comments")
            
            for button in load_buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        print(f"   🖱️  Haciendo clic en botón: {button.get_attribute('class')}")
                        ActionChains(driver).move_to_element(button).click().perform()
                        time.sleep(2)
                except:
                    pass
        except:
            pass
        
        # Verificar si aparecieron comentarios
        for selector in comment_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ Encontrados {len(elements)} elementos con selector: {selector}")
                    time.sleep(2)  # Dar tiempo a que carguen completamente
                    return selector
            except:
                continue
        
        # Scroll intermedio
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
    
    print("   ⚠️  No se pudieron cargar comentarios dinámicamente")
    return None

def extract_comments_aggressive(driver, max_comments=15):
    """Extracción agresiva probando múltiples estrategias"""
    comments = []
    
    # Obtener HTML completo
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    time.sleep(2)  # Asegura que el DOM esté completamente listo
    
    # Estrategia 1: Selectores específicos de La Voz
    selectors_to_try = [
    'dl.comments > dd'
    ]
 
    comment_elements = []
    working_selector = None
    
    for selector in selectors_to_try:
        elements = soup.select(selector)
        if elements:
            print(f"✅ Selector funcionando: {selector} ({len(elements)} elementos)")
            comment_elements = elements[:max_comments]
            working_selector = selector
            break
    
    if not comment_elements:
        print("❌ Ningún selector específico funcionó")
        # Estrategia 2: Buscar por contenido de texto
        print("🔍 Buscando comentarios por contenido...")
        
        # Buscar elementos que contengan texto típico de comentarios
        all_elements = soup.find_all(['div', 'dd', 'article', 'section'])
        
        for element in all_elements:
            text = element.get_text().strip()
            
            # Patrones que indican comentarios
            comment_patterns = [
                r'hace \d+ días?',
                r'Responder?',
                r'Me gusta',
                r'No me gusta',
                r'desde [A-Z]+',
                r'[a-zA-Z]+[\.\-]\d+'  # Patrones de usuario como jan.-265425840
            ]
            
            pattern_matches = sum(1 for pattern in comment_patterns if re.search(pattern, text, re.IGNORECASE))
            
            # Si tiene al menos 2 patrones de comentario y texto sustancial
            if pattern_matches >= 2 and 20 < len(text) < 1000:
                comment_elements.append(element)
                if len(comment_elements) >= max_comments:
                    break
        
        print(f"🔍 Encontrados {len(comment_elements)} elementos por contenido")
    
    if not comment_elements:
        print("❌ No se encontraron comentarios con ninguna estrategia")
        return []
    
    # Procesar elementos encontrados
    for i, element in enumerate(comment_elements, 1):
        try:
            print(f"🔎 Procesando elemento {i}...")

            # Obtener texto inicial completo (con botones incluidos)
            full_text = element.get_text().strip()

            # Extraer likes/dislikes antes de eliminar botones
            likes = 0
            dislikes = 0

            like_match = re.search(r'Me gusta.*?(\d+)', full_text)
            if like_match:
                likes = int(like_match.group(1))

            dislike_match = re.search(r'No me gusta.*?(\d+)', full_text)
            if dislike_match:
                dislikes = int(dislike_match.group(1))

            # Ahora sí: eliminar botones del DOM (para limpiar el texto del comentario)
            for button in element.find_all("button"):
                button.decompose()

            # Volver a extraer texto limpio sin botones
            cleaned_text = element.get_text().strip()

            # Detectar si es una respuesta ANTES de limpiar el texto
            is_response = False
            response_to = ""
            response_match = re.search(r'(?:Responde\s+)?a\s+([a-zA-Z]+[\.\-_]*\d+)', cleaned_text)
            if response_match:
                is_response = True
                response_to = response_match.group(1)

            # Extraer autor
            author = "Anónimo"

            # Extraer ubicación (ej: MUROS, FENE)
            location = ""
            location_match = re.search(r'desde\s+([A-ZÁÉÍÓÚÑ]{3,})', cleaned_text)
            if location_match:
                location = location_match.group(1)
            
            user_match = re.search(r'([a-zA-Z]+[\.\-]?\d+)', cleaned_text)

            if user_match:
                author = user_match.group(1)

            desde_match = re.search(r'desde ([A-Z][A-Z]+)', cleaned_text)
            if desde_match:
                author = f"{author} desde {desde_match.group(1)}"

            strong_elements = element.find_all('strong')
            for strong in strong_elements:
                strong_text = strong.get_text().strip()
                if len(strong_text) < 30 and strong_text not in ['Me gusta', 'No me gusta', 'Responder']:
                    if not re.search(r'hace \d+ días?', strong_text):
                        author = strong_text
                        break

            print(f"   👤 Autor detectado: {author}")

            # Extraer fecha
            date_text = ""
            date_match = re.search(r'hace \d+ días?\.?', cleaned_text)
            if date_match:
                date_text = date_match.group(0)

            print(f"   📅 Fecha detectada: {date_text}")

            # Texto del comentario limpio
            comment_text = cleaned_text

            cleanup_patterns = [
            r'hace \d+ días?\.?',
            r'Me gusta.*?\d+',
            r'No me gusta.*?\d+',
            r'\bResponder\b',
            r'\bdesde\s+[A-ZÁÉÍÓÚÑ]{3,}(?:\s+y\s+\w+)?[\.,]?',      # desde FENE, etc.
            ]

            # Limpiar patrones básicos
            for pattern in cleanup_patterns:
                comment_text = re.sub(pattern, '', comment_text, flags=re.IGNORECASE)

            # Limpiar usuario al principio (sin "Responde a")
            if not is_response:
                comment_text = re.sub(r'^[a-zA-Z]+[\.\-_]*\d+\s+', '', comment_text, flags=re.IGNORECASE)
            else:
            # Para respuestas: cambiar "a usuario" por "Responde a usuario"
                comment_text = re.sub(r'^a\s+([a-zA-Z]+[\.\-_]*\d+)\.?\s*', r'Responde a \1. ', comment_text, flags=re.IGNORECASE)
            comment_text = ' '.join(comment_text.split()).strip()

            print(f"   💬 Texto limpio: {comment_text[:100]}...")

            if comment_text and len(comment_text) > 10:
                if any(c["text"] == comment_text for c in comments):
                    print(f"   ⚠️ Comentario {i} duplicado (mismo texto), descartado")
                    continue

                comments.append({
                    "author": author,
                    "location": location,
                    "text": comment_text,
                    "date": date_text,
                    "likes": likes,
                    "dislikes": dislikes
                })
                print(f"   ✅ Comentario {i} agregado")
            else:
                print(f"   ⚠️  Comentario {i} descartado (texto insuficiente)")

        except Exception as e:
            print(f"❌ Error procesando elemento {i}: {e}")
            continue
    
    return comments

def extract_comments_selenium(url, max_comments=15):
    """Función principal de extracción con múltiples estrategias"""
    driver = setup_driver()
    comments = []

    driver.get(url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    try:
        print(f"🌐 Cargando URL: {url}")
        try:
            WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "comments_feed"))
        )
            print("✅ Comentarios dinámicos detectados")
        except TimeoutException:
            print("⚠️ Timeout esperando #comments_feed (puede que no haya comentarios visibles)")

        
        print(f"📄 Página cargada: {driver.title}")
        
        # Esperar a que se carguen los comentarios dinámicamente
        working_selector = wait_for_comments_to_load(driver)
        
        # Extracción agresiva
        comments = extract_comments_aggressive(driver, max_comments)
        
        # Si no encuentra comentarios, guardar HTML para debug
        if not comments:
            debug_file = "debug_la_voz_comments.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"💾 HTML guardado en {debug_file} para debugging")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
    finally:
        driver.quit()
    
    return comments

def scrape_and_save():
    """Función principal"""
    url = "https://www.lavozdegalicia.es/noticia/sociedad/2025/05/15/playa-portocelo-leyenda-pueblo-hundido/0003_202505G15P28996.htm"
    
    print("🚀 Iniciando scraping agresivo de La Voz de Galicia...")
    comments = extract_comments_selenium(url)
    
    if comments:
        print(f"🎉 ¡Éxito! Encontrados {len(comments)} comentarios")
    else:
        print("⚠️  No se encontraron comentarios")
    
    # Crear estructura de datos
    # Crear estructura de datos (agrupada por comentario para mejor legibilidad)
    article_data = {
        "source": "La Voz de Galicia",
        "title": "Playa de Portocelo: La leyenda del pueblo hundido",
        "link": url,
        "date": datetime.now().isoformat(),
        "n_comments": len(comments)
    }

    # Crear campos agrupados por comentario
    for i in range(15):
        article_data.update({
            f"comment_{i+1}_author": "",
            f"comment_{i+1}_location": "",
            f"comment_{i+1}_date": "",
            f"comment_{i+1}_text": "",
            f"comment_{i+1}_likes": 0,
            f"comment_{i+1}_dislikes": 0
        })

    # Llenar con comentarios encontrados
    for i, comment in enumerate(comments[:15]):
        article_data[f"comment_{i+1}_author"] = comment["author"]
        article_data[f"comment_{i+1}_location"] = comment["location"]
        article_data[f"comment_{i+1}_date"] = comment["date"]
        article_data[f"comment_{i+1}_text"] = comment["text"]
        article_data[f"comment_{i+1}_likes"] = comment["likes"]
        article_data[f"comment_{i+1}_dislikes"] = comment["dislikes"]
    
    # Guardar CSV
    df = pd.DataFrame([article_data])
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8')
    
    print(f"✅ CSV guardado en: {os.path.abspath(OUTPUT_PATH)}")
    print(f"📊 Total comentarios: {len(comments)}")
    
    if comments:
        print("\n📋 Comentarios extraídos:")
        for i, comment in enumerate(comments[:5], 1):
            print(f"   {i}. [{comment['author']}] {comment['text'][:80]}...")
            if comment['date']:
                print(f"      📅 {comment['date']} | 👍 {comment['likes']} | 👎 {comment['dislikes']}")

if __name__ == "__main__":
    scrape_and_save()