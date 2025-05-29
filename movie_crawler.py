import requests
from bs4 import BeautifulSoup
import json
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

class MotphimCrawler:
    def __init__(self):
        self.base_url = "https://motphimtopp.com/phim-le/"
        self.movies = []
        # Cấu hình session với retry mechanism
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def crawl_movies(self, num_movies=10):
        print("Đang lấy danh sách phim mới nhất từ motphimtopp.com ...")
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Lấy tất cả phim mới cập nhật
            movie_items = soup.select("article.item.movies")
            print(f"Tìm thấy {len(movie_items)} phim")
            
            # Sắp xếp phim theo thời gian cập nhật
            sorted_movies = []
            for item in movie_items:
                try:
                    # Lấy thời gian cập nhật
                    time_tag = item.select_one("div.data span.time")
                    update_time = time_tag.text.strip() if time_tag else ""
                    
                    # Lấy tên phim và link chi tiết
                    a_tag = item.select_one("div.data h3 a")
                    title = a_tag.text.strip() if a_tag else "Unknown"
                    url = a_tag["href"] if a_tag else ""
                    
                    # Lấy poster
                    img_tag = item.select_one("div.poster img")
                    poster_url = img_tag["src"] if img_tag else ""
                    
                    # Lấy năm
                    year_tag = item.select_one("div.data span")
                    year = year_tag.text.strip()[-4:] if year_tag and year_tag.text.strip()[-4:].isdigit() else "Unknown"
                    
                    # Lấy rating
                    rating_tag = item.select_one("div.rating")
                    rating = rating_tag.text.strip() if rating_tag else "N/A"
                    
                    # Lấy mô tả và link xem phim thực sự từ trang chi tiết
                    description, movie_url = self.get_movie_detail(url)
                    
                    movie_data = {
                        "title": title,
                        "year": year,
                        "rating": rating,
                        "description": description,
                        "poster_url": poster_url,
                        "movie_url": movie_url,
                        "url": url,
                        "update_time": update_time
                    }
                    sorted_movies.append(movie_data)
                    print(f"Đã lấy: {title} - Cập nhật: {update_time}")
                    # Thêm delay nhỏ giữa các request để tránh bị block
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Lỗi khi lấy phim: {e}")
                    continue
            
            # Sắp xếp phim theo thời gian cập nhật mới nhất
            sorted_movies.sort(key=lambda x: x.get('update_time', ''), reverse=True)
            
            # Lấy num_movies phim mới nhất
            self.movies = sorted_movies[:num_movies]
                    
            # Lưu file
            if not os.path.exists('data'):
                os.makedirs('data')
            with open("data/movies.json", "w", encoding="utf-8") as f:
                json.dump(self.movies, f, ensure_ascii=False, indent=4)
            print(f"Đã lưu {len(self.movies)} phim mới nhất vào data/movies.json")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối: {e}")
            return False
        except Exception as e:
            print(f"Lỗi không xác định: {e}")
            return False

    def get_movie_detail(self, detail_url):
        try:
            res = self.session.get(detail_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Lấy mô tả
            desc_tag = soup.find('div', class_='description')
            description = desc_tag.text.strip() if desc_tag else ""
            
            # Lấy link xem phim thực sự (iframe player)
            iframe = soup.select_one('div.pframe iframe')
            movie_url = iframe["src"] if iframe and iframe.has_attr("src") else detail_url
            
            return description, movie_url
            
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi lấy chi tiết phim: {e}")
            return "", detail_url
        except Exception as e:
            print(f"Lỗi không xác định khi lấy chi tiết phim: {e}")
            return "", detail_url

if __name__ == "__main__":
    crawler = MotphimCrawler()
    crawler.crawl_movies(10)