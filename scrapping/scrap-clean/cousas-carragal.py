import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
from dateutil.parser import parse as date_parse
import time
import os

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
DATE_THRESHOLD = datetime(2023, 5, 28)

def scrape_cousas_carragal_all():
    base_url = "https://cousasdecarragal.blogspot.com/"
    current_url = base_url
    data = []
    stop_scraping = False
    seen_links = set()  # Conjunto para llevar registro de links ya procesados
    
    while current_url and not stop_scraping:
        print(f"🌀 Cargando URL: {current_url}")
        
        try:
            response = requests.get(current_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"❌ Error HTTP: {response.status_code}")
                break
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"❌ Error al cargar página: {e}")
            break
            
        posts = soup.select(".post h3 a")
        print(f"📄 Posts encontrados en página: {len(posts)}")
        
        new_posts_count = 0
        old_posts_count = 0

        for p in posts:
            title = p.get_text(strip=True)
            link = p["href"]
            
            # Verificar si ya hemos procesado este post
            if link in seen_links:
                print(f"👀 Post duplicado: {title}. Saltando.")
                continue
              
            # Registrar este link como ya visto
            seen_links.add(link)
            
            try:
                print(f"🔍 Procesando post: {title}")
                post_response = requests.get(link, headers=HEADERS, timeout=15)
                post_soup = BeautifulSoup(post_response.text, "html.parser")
            except Exception as e:
                print(f"⚠️ Error al cargar post '{title}': {str(e)[:100]}")
                continue
                
            # Extraer fecha
            date_tag = post_soup.select_one("abbr.published") or post_soup.select_one("span.published")
            try:
                date = date_parse(date_tag["title"]).replace(tzinfo=None) if date_tag and "title" in date_tag.attrs else None
            except Exception as e:
                print(f"⚠️ Error al procesar fecha para '{title}': {str(e)[:100]}")
                date = None

            # Verificar si el post es válido según la fecha
            if not date:
                print(f"⚠️ No se pudo obtener fecha para '{title}'. Se ignora.")
                continue
                
            if date < DATE_THRESHOLD:
                print(f"🚫 Post con fecha {date.isoformat()} anterior al umbral {DATE_THRESHOLD.isoformat()}. Finalizando.")
                old_posts_count += 1
               
                # Si encontramos 2 o más posts antiguos consecutivos, detenemos el scraping
                if old_posts_count >= 2:
                    stop_scraping = True
                    break
                continue
            else:
                # Reiniciamos el contador de posts antiguos
                old_posts_count = 0
                new_posts_count += 1

            print(f"✅ [Cousas de Carragal] {title} | {date.isoformat()} -> VÁLIDO")

            # Extraer comentarios
            # Extraer comentarios con autor y fecha
            comment_blocks = post_soup.select(".comments .comment-content")
            comment_wrappers = post_soup.select(".comments .comment")

            final_comments = []

            for wrapper in comment_wrappers[:15]:  # limitar a 15 comentarios
                try:
                    author_tag = wrapper.select_one(".user .fn") or wrapper.select_one(".comment-author")
                    author = author_tag.get_text(strip=True) if author_tag else "Anónimo"

                    date_tag = wrapper.select_one(".datetime a") or wrapper.select_one(".datetime")
                    date_text = date_tag.get_text(strip=True) if date_tag else ""

                    content_tag = wrapper.select_one(".comment-content")
                    content = content_tag.get_text(strip=True) if content_tag else ""

                    if len(content) > 10:
                        final_comments.append({
                        "author": author,
                        "date": date_text,
                        "text": content
                        })

                except Exception as e:
                    print(f"⚠️ Error en comentario: {str(e)[:100]}")
                    continue

            row = {
            "source": "Cousas de Carragal",
            "title": title,
            "link": link,
            "date": date.isoformat(),
            "n_comments": len(final_comments)
            }

            for i in range(15):
                row[f"comment_{i+1}_author"] = ""
                row[f"comment_{i+1}_date"] = ""
                row[f"comment_{i+1}_text"] = ""

            for i, comment in enumerate(final_comments[:15]):
                row[f"comment_{i+1}_author"] = comment["author"]
                row[f"comment_{i+1}_date"] = comment["date"]
                row[f"comment_{i+1}_text"] = comment["text"]

            data.append(row)

        print(f"📊 Página actual: {new_posts_count} posts nuevos añadidos")
        
        # Verificar si debemos detener el scraping
        if old_posts_count >= 2:
            print("🏁 Se encontraron suficientes posts antiguos consecutivos. Finalizando.")
            break
            
        # Buscar botón de "Entradas antiguas"
        older_link_tag = soup.find("a", string=lambda s: s and "entradas antiguas" in s.lower())
        next_url = older_link_tag["href"] if older_link_tag else None
      
        if not next_url:
            print("🏁 No se encontró enlace a entradas antiguas. Finalizando.")
            break
            
        # Verificar si el enlace ya ha sido visitado (para evitar bucles)
        if next_url in seen_links:
            print("🔄 El enlace a la siguiente página ya ha sido visitado. Posible bucle detectado. Finalizando.")
            break
            
        current_url = next_url
        
        # Pausa para no sobrecargar el servidor
        time.sleep(2)

    print(f"✅ Cousas de Carragal: {len(data)} artículos válidos procesados\n")
    print(f"📅 Rango de fechas: {data[0]['date'] if data else 'N/A'} a {data[-1]['date'] if data else 'N/A'}")
    return data

# Ejecutar
data = scrape_cousas_carragal_all()

# Ruta a nivel superior (subir un nivel desde ialimpia)
# Usando '..' subimos un nivel en la jerarquía de directorios
output_dir = os.path.join("..", "..", "data", "raw", "clean-csvs")
os.makedirs(output_dir, exist_ok=True)  # Crea la estructura si no existe

# Ruta completa del archivo CSV
csv_path = os.path.join(output_dir, "cousas-carragal-limpio.csv")

# Guardar CSV en la carpeta correcta
df = pd.DataFrame(data)
df.to_csv(csv_path, index=False)

# Mostrar resumen
print(f"\n📦 CSV generado en '{csv_path}' con {len(df)} artículos.")
print(df[["source", "title", "date", "n_comments"]])