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

def scrape_diario_marin_all():
    base_url = "https://diariomarin.com"
    page = 1
    data = []
    MAX_PAGES = 1000  # Límite de seguridad para evitar bucles infinitos
    seen_links = set()  # Para evitar duplicados
    consecutive_empty_pages = 0  # Contador de páginas vacías consecutivas
    old_article_count = 0  # Contador de artículos antiguos consecutivos
    MAX_OLD_ARTICLES = 3  # Número de artículos antiguos consecutivos para detener

    while page <= MAX_PAGES:
        page_url = f"{base_url}/page/{page}/" if page > 1 else base_url
        print(f"\n🌀 Cargando Página {page}: {page_url}")
        
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"❌ Fin de páginas o error HTTP: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Error al cargar página: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        
        # MEJOR IDENTIFICACIÓN DE ARTÍCULOS - ENFOQUE MÁS AMPLIO
        articles = []
        
        # Probar con varios selectores para mayor robustez
        # 1. Método directo para artículos
        articles = soup.find_all("article")
        
        # 2. Buscar en contenedores conocidos si método 1 falla
        if not articles:
            possible_containers = [
                soup.find('div', class_='td-ss-main-content'),
                soup.find('div', class_=['tdb_loop', 'td_block_wrap tdb_loop']),
                soup.find('div', id='tdi_52'),
                # Añadir más contenedores potenciales aquí
                soup.find('div', class_=lambda c: c and ('content' in c.lower() if c else False)),
                soup.find('div', class_=lambda c: c and ('loop' in c.lower() if c else False)),
                soup.find('main'),  # A veces los artículos están en el <main>
            ]
            
            for container in possible_containers:
                if container:
                    container_articles = container.find_all('article')
                    if container_articles:
                        articles = container_articles
                        break
                    
                    # Si no encuentra <article> directamente, buscar divs que contengan títulos
                    potential_article_divs = container.find_all('div', class_=lambda c: c and ('item' in c.lower() if c else False))
                    if potential_article_divs:
                        articles = potential_article_divs
                        break
        
        if not articles:
            print(f"⚠️ No se encontraron artículos en la página {page}.")
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= 2:  # Si 2 páginas consecutivas no tienen artículos, terminar
                print("❌ Múltiples páginas vacías consecutivas. Finalizando.")
                break
            page += 1
            continue
        else:
            consecutive_empty_pages = 0  # Reiniciar contador si encontramos artículos
        
        print(f"📄 Artículos encontrados: {len(articles)}")
        valid_articles_this_page = 0
        new_articles_this_page = 0
           # Proceso completo de artículos
        for article in articles:
            try:
                # EXTRACCIÓN MÁS ROBUSTA DEL TÍTULO Y ENLACE
                # Intenta varios métodos para encontrar título y enlace
                title_tag = None
                link = None
                
                # Método 1: Buscar en encabezados con clases específicas
                for header_tag in ['h2', 'h3', 'h4']:
                    if title_tag:
                        break
                    potential_tags = article.find_all(header_tag, class_=lambda c: c and 
                                                     any(cls in (c or '') for cls in ['entry-title', 'title', 'tdb-entry-title']))
                    if potential_tags:
                        title_tag = potential_tags[0]
                
                # Método 2: Cualquier encabezado si no encontramos con clases específicas
                if not title_tag:
                    for header_tag in ['h2', 'h3', 'h4', 'h1']:
                        potential_tags = article.find_all(header_tag)
                        if potential_tags:
                            title_tag = potential_tags[0]
                            break
                
                # Método 3: Buscar cualquier etiqueta con la clase que contiene "title"
                if not title_tag:
                    title_elements = article.find_all(class_=lambda c: c and 'title' in c.lower() if c else False)
                    if title_elements:
                        title_tag = title_elements[0]
                
                # Extraer título y enlace
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    
                    # Intentar obtener enlace del título
                    link_tag = title_tag.find('a')
                    if link_tag and 'href' in link_tag.attrs:
                        link = link_tag['href']
                    else:
                        # Buscar cualquier enlace en el artículo
                        any_link = article.find('a')
                        if any_link and 'href' in any_link.attrs:
                            link = any_link['href']
                
                # Asegurar que tenemos título y enlace
                if not title_tag or not link:
                    print("⚠️ No se pudo extraer título o enlace. Saltando artículo.")
                    continue
                
                # Normalizar URL (añadir dominio si es relativa)
                if link and not link.startswith(('http://', 'https://')):
                    link = base_url + ('' if link.startswith('/') else '/') + link
                
                # Verificar duplicados
                if link in seen_links:
                    print(f"👀 Artículo duplicado: {title}. Saltando.")
                    continue
                
                seen_links.add(link)
                new_articles_this_page += 1

                # Cargar post completo
                try:
                    post_response = requests.get(link, headers=HEADERS, timeout=15)
                    post_page = BeautifulSoup(post_response.text, "html.parser")
                except Exception as e:
                    print(f"⚠️ Error al cargar artículo '{title}': {str(e)[:100]}")
                    continue

                # EXTRACCIÓN MEJORADA DE FECHA - MÚLTIPLES MÉTODOS
                date = None
                
                # Método 1: Meta tags (más confiable)
                meta_tags = [
                    post_page.find("meta", {"property": "article:published_time"}),
                    post_page.find("meta", {"name": "article:published_time"}),
                    post_page.find("meta", {"property": "og:published_time"}),
                    post_page.find("meta", {"name": "publication_date"})
                ]
                
                for tag in meta_tags:
                    if tag and tag.get("content"):
                        try:
                            date = date_parse(tag["content"]).replace(tzinfo=None)
                            break
                        except:
                            continue
                
                # Método 2: Etiquetas time
                if not date:
                    time_tags = post_page.find_all("time")
                    for t in time_tags:
                        if "datetime" in t.attrs:
                            try:
                                date = date_parse(t["datetime"]).replace(tzinfo=None)
                                break
                            except:
                                continue
                
                # Método 3: Buscar en clases que contengan "date"
                if not date:
                    date_elements = post_page.find_all(class_=lambda c: c and 'date' in c.lower() if c else False)
                    for element in date_elements:
                        try:
                            date_text = element.get_text(strip=True)
                            date = date_parse(date_text).replace(tzinfo=None)
                            break
                        except:
                            continue
                
                if not date:
                    print(f"⚠️ No se pudo obtener fecha para '{title}'. Se ignora.")
                    continue

                # COMPROBACIÓN DE FECHA UMBRAL - MODIFICADO
                if date < DATE_THRESHOLD:
                    print(f"🚫 Artículo con fecha {date.isoformat()} anterior al umbral {DATE_THRESHOLD.isoformat()}. Descartando.")
                    old_article_count += 1  # Incrementar contador de artículos antiguos
                    
                    # Si encontramos suficientes artículos antiguos consecutivos, terminamos
                    if old_article_count >= MAX_OLD_ARTICLES:
                        print(f"🏁 Se encontraron {MAX_OLD_ARTICLES} artículos consecutivos anteriores al umbral. Finalizando.")
                        break
                    
                    continue  # Saltamos este artículo
                else:
                    # Resetear contador si encontramos un artículo reciente
                    old_article_count = 0

                # ✅ Si llegamos aquí, el post es válido
                valid_articles_this_page += 1
                print(f"✅ [Diario Marín] {title} | {date.isoformat()} -> VÁLIDO")

                # Extracción mejorada de comentarios
                comment_texts = []
                processed_comments = set()  # Conjunto para evitar duplicados
                
                # Método 1: Buscar por clase comment-list
                comment_blocks = post_page.find_all(["ol", "ul", "div"], class_=lambda c: c and 'comment' in c.lower() if c else False)
                
                for block in comment_blocks:
                    comments = block.find_all(["li", "div"], class_=lambda c: c and ('comment' in c.lower() if c else False) and ('form' not in c.lower() if c else True))
                    for comment in comments:
                        # Intentar extraer solo el texto del comentario, no metadatos
                        comment_body = comment.find(class_=lambda c: c and ('text' in c.lower() or 'body' in c.lower() or 'content' in c.lower() if c else False))
                        
                        if comment_body:
                            c = comment_body.get_text(separator=" ", strip=True)
                        else:
                            c = comment.get_text(separator=" ", strip=True)
                            
                        # Ignorar texto que no es un comentario real
                        if c and len(c) > 10:  # Filtrar textos muy cortos que probablemente sean metadata
                            # Ignorar textos específicos que no son comentarios reales
                            if not any(texto in c for texto in ["Deja un comentario", "Cancelar respuesta", "Responder"]):
                                # Solo añadir si no es un duplicado
                                if c not in processed_comments:
                                    processed_comments.add(c)
                                    comment_texts.append(c)

                # Filtrar aún más para mantener solo comentarios en formato preferido
                # Reemplaza TODO el bloque de extracción de comentarios por esto
                final_comments = []
                comment_elements = post_page.select("ol.commentlist li.comment")

                for comment in comment_elements[:15]:
                    try:
                    # Autor (opcional, no se usará ahora)
                        author_tag = comment.select_one(".comment-author .fn")
                        author = author_tag.get_text(strip=True) if author_tag else "Anónimo"

                        # Fecha
                        date_tag = comment.select_one("footer .comment-metadata")
                        date_text = date_tag.get_text(strip=True) if date_tag else ""
                        date_text = re.sub(r"\s+", " ", date_text)

                        # Contenido
                        content_tag = comment.select_one(".comment-content")
                        content = content_tag.get_text(separator=" ", strip=True) if content_tag else ""
                        content = re.sub(r"\s+", " ", content)

                        # Validación mínima
                        if len(content) > 5:
                            final_comments.append({
                                "author": author,
                                "date": date_text,
                                "text": content
                            })
                    except Exception as e:
                        print(f"⚠️ Error al procesar comentario: {str(e)[:100]}")
                        continue

                # Calcular número real de comentarios (excluyendo textos no deseados)
                # Estructura con comentarios separados hasta 15
                row = {
                "source": "Diario Marín",
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


            except Exception as e:
                print(f"⚠️ Error procesando artículo: {str(e)[:100]}...")
                continue

        # VERIFICACIÓN SI SE ALCANZÓ EL LÍMITE DE ARTÍCULOS ANTIGUOS
        if old_article_count >= MAX_OLD_ARTICLES:
            print(f"🏁 Se alcanzó el límite de artículos antiguos consecutivos ({MAX_OLD_ARTICLES}). Finalizando.")
            break
                
        # MEJOR CONTROL DE PAGINACIÓN
        print(f"📊 Página {page}: {valid_articles_this_page} artículos válidos, {new_articles_this_page} nuevos")
        
        # Criterios de finalización mejorados
        if new_articles_this_page == 0:
            print(f"⚠️ No se encontraron nuevos artículos en la página {page}. Verificando una página más...")
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= 2:
                print("❌ Fin de paginación detectado (sin nuevos artículos). Finalizando.")
                break
            
        # Restablecer el contador de artículos antiguos entre páginas
        old_article_count = 0  # Resetear entre páginas para evitar falsos positivos
                
        # Pausa para no sobrecargar el servidor
        page += 1
        time.sleep(2)  # Pausa más larga para evitar problemas

    print(f"✅ Diario Marín: {len(data)} artículos válidos recopilados de {page-1} páginas")
    print(f"📅 Rango de fechas: {data[0]['date'] if data else 'N/A'} a {data[-1]['date'] if data else 'N/A'}")
    return data

# Ejecutar - Corrigiendo el error: debe ser scrape_diario_marin_all()
data = scrape_diario_marin_all()

# Ruta a nivel superior (subir un nivel desde ialimpia)
output_dir = os.path.join("..", "..", "data", "raw", "clean-csvs")
os.makedirs(output_dir, exist_ok=True)  # Crea la estructura si no existe

# Ruta completa del archivo CSV
csv_path = os.path.join(output_dir, "diario-marin-limpio.csv")

# Guardar CSV en la carpeta correcta
df = pd.DataFrame(data)
df.to_csv(csv_path, index=False)

# Mostrar resumen
print(f"\n📦 CSV generado en '{csv_path}' con {len(df)} artículos.")
print(df[["source", "title", "date", "n_comments"]])