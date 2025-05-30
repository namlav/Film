import requests
from bs4 import BeautifulSoup
import json
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import re

class MotphimCrawler:
    def __init__(self):
        self.base_url = ""
        self.movies = []
        self.current_genre_slug = ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        }
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def save_poster_image(self, title, url, genre_slug, retries=3):
        if not url:
            return

        folder = os.path.join("images", genre_slug)
        os.makedirs(folder, exist_ok=True)

        # 👉 Thay mọi ký tự không phải chữ/số bằng "_", bao gồm cả dấu :
        clean_name = re.sub(r'[^\w]', '_', title)
        filename = os.path.join(folder, f"{clean_name}.jpg")

        for attempt in range(1, retries + 1):
            try:
                print(f"→ Tải ảnh ({attempt}/{retries}): {filename}")
                img = self.session.get(url, headers=self.headers, timeout=10)
                img.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(img.content)
                print(f"🖼️ Lưu thành công: {filename}")
                return
            except Exception as e:
                print(f"❌ Lỗi lần {attempt}: {e}")
                time.sleep(1)

        print(f"⚠️ Bỏ qua ảnh: {filename} sau {retries} lần thử.")


    def crawl_movies(self, num_movies=50):
        sorted_movies = []
        existing_urls = set()
        page = 1
        try:
            while len(sorted_movies) < num_movies:
                url = self.base_url if page == 1 else f"{self.base_url}page/{page}/"
                print(f"→ Đang lấy trang {page}: {url}")
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                movie_items = soup.select("article.item.movies")
                if not movie_items:
                    break

                for item in movie_items:
                    if len(sorted_movies) >= num_movies:
                        break
                    try:
                        a_tag = item.select_one("div.data h3 a")
                        title = a_tag.text.strip() if a_tag else "Unknown"
                        url = a_tag["href"] if a_tag else ""
                        if url in existing_urls:
                            continue
                        existing_urls.add(url)

                        img_tag = item.select_one("div.poster img")
                        poster_url = img_tag.get("data-src") or img_tag.get("src") or "" if img_tag else ""

                        year = "Unknown"
                        year_tag = item.select_one("div.data span")
                        if year_tag:
                            match = re.search(r"\b(19|20)\d{2}\b", year_tag.text)
                            if match:
                                year = match.group(0)

                        rating_tag = item.select_one("div.rating")
                        rating = rating_tag.text.strip() if rating_tag else "N/A"

                        description, movie_url = self.get_movie_detail(url)

                        self.save_poster_image(title, poster_url, self.current_genre_slug)

                        movie_data = {
                            "title": title,
                            "year": year,
                            "rating": rating,
                            "description": description,
                            "poster_url": poster_url,
                            "movie_url": movie_url,
                            "url": url,
                            "genre": ""  # sẽ thêm sau
                        }

                        sorted_movies.append(movie_data)
                        print(f"✔ Đã lấy: {title}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"Lỗi khi lấy phim: {e}")
                        continue

                page += 1

            self.movies = sorted_movies[:num_movies]
            return True

        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối: {e}")
            return False
        except Exception as e:
            print(f"Lỗi không xác định: {e}")
            return False

    def get_movie_detail(self, detail_url):
        try:
            res = self.session.get(detail_url, headers=self.headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            desc_tag = soup.find('div', class_='description')
            description = desc_tag.text.strip() if desc_tag else ""

            iframe = soup.select_one('div.pframe iframe')
            movie_url = iframe["src"] if iframe and iframe.has_attr("src") else detail_url

            return description, movie_url

        except Exception:
            return "", detail_url

    def crawl_genres(self, num_per_genre=10):
        genres = {
            "Kinh dị": "https://motphimtopp.com/the-loai/kinh-di/",
            "Bí ẩn": "https://motphimtopp.com/the-loai/bi-an/",
            "Viễn tưởng": "https://motphimtopp.com/the-loai/vien-tuong/",
            "Chính kịch": "https://motphimtopp.com/the-loai/chinh-kich/",
            "Hành động": "https://motphimtopp.com/the-loai/hanh-dong/",
            "Hài hước": "https://motphimtopp.com/the-loai/hai-huoc/",
            "Hình sự": "https://motphimtopp.com/the-loai/hinh-su/",
            "Tâm lý": "https://motphimtopp.com/the-loai/tam-ly/"
        }

        all_movies = []

        for name, url in genres.items():
            print(f"\n🎬 Đang crawl thể loại: {name}")
            self.base_url = url
            self.current_genre_slug = url.rstrip("/").split("/")[-1]
            if self.crawl_movies(num_per_genre):
                for movie in self.movies:
                    movie["genre"] = name
                all_movies.extend(self.movies)
            time.sleep(2)

        self.movies = all_movies
        if not os.path.exists('data'):
            os.makedirs('data')
        with open("data/movies.json", "w", encoding="utf-8") as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Đã lưu {len(self.movies)} phim vào data/movies.json")


if __name__ == "__main__":
    crawler = MotphimCrawler()
    crawler.crawl_genres(num_per_genre=10)
