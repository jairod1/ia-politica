from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time

OUTPUT_DIR = os.path.join("..", "..", "data", "raw", "dirty-csvs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "diario-pontevedra-sucio.csv")
DATE_THRESHOLD = datetime(2025, 5, 15)

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return driver

def extract_comments(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    comment_section = soup.find("body", class_="comments-page")
    if not comment_section:
        return []
    
    comments = []
    comment_divs = soup.select(".post-content")
    for div in comment_divs[:15]:
        try:
            date_part = div.select_one(".content-meta-date.time-ago")
            time_part = div.select_one(".content-meta-time")
            date = date_part.get_text(strip=True) if date_part else ""
            time_ = time_part.get_text(strip=True) if time_part else ""
            timestamp = f"{date} {time_}".strip()
            
            author_tag = div.select_one(".comment-author-name")
            author = author_tag.get_text(strip=True) if author_tag else "Anónimo"
            
            message_tag = div.select_one(".post-message p")
            message = message_tag.get_text(strip=True) if message_tag else ""
            
            like_tag = div.select_one('[data-role="likes"].count')
            dislike_tag = div.select_one('[data-role="dislikes"].count')

            likes = int(like_tag.get_text(strip=True)) if like_tag and like_tag.get_text(strip=True).isdigit() else 0
            dislikes = int(dislike_tag.get_text(strip=True)) if dislike_tag and dislike_tag.get_text(strip=True).isdigit() else 0

            if message:
                comments.append({
                    "author": author,
                    "date": timestamp,
                    "text": message,
                    "location": "",
                    "likes": likes,
                    "dislikes": dislikes
                })

        except Exception:
            continue
    return comments

def scrape_multiple_articles(base_url="https://www.diariodepontevedra.es/tags/marin/?page=",
                             date_threshold=DATE_THRESHOLD,
                             max_pages=50,
                             max_old_articles=3):
    driver = setup_driver()
    all_rows = []
    old_articles = 0

    try:
        for page in range(1, max_pages + 1):
            print(f"🔄 Página {page}")
            driver.get(f"{base_url}{page}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            article_links = [a["href"] for a in soup.select("a[href*='/articulo/o-morrazo/']") if a["href"].startswith("https://")]

            if not article_links:
                print("❌ No se encontraron artículos. Parando...")
                break

            for url in article_links:
                print(f"📝 Procesando: {url}")
                try:
                    driver.get(url)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    article_soup = BeautifulSoup(driver.page_source, "html.parser")

                    time_tag = article_soup.find("time")
                    if time_tag and time_tag.has_attr("datetime"):
                        date = datetime.fromisoformat(time_tag["datetime"][:10])
                    else:
                        date = datetime.now()
                    
                    if date.date() < date_threshold.date():
                        old_articles += 1
                        if old_articles >= max_old_articles:
                            print("🛑 Límite de artículos antiguos alcanzado")
                            return
                        continue
                    else:
                        old_articles = 0

                    comments = extract_comments(driver)
                    title = article_soup.title.string.strip() if article_soup.title else ""

                    row = {
                        "source": "Diario de Pontevedra",
                        "title": title,
                        "link": url,
                        "date": date.isoformat(),
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
                except Exception as e:
                    print(f"⚠️ Error procesando artículo: {e}")
                    continue
    finally:
        driver.quit()

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"✅ Guardado CSV en: {OUTPUT_PATH} con {len(df)} artículos")

if __name__ == "__main__":
    scrape_multiple_articles()