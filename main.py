#account admin: admin,admin123
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from PIL import Image, ImageTk, UnidentifiedImageError
import requests
from bs4 import BeautifulSoup
from tkinterweb import HtmlFrame
import webbrowser
from movie_crawler import MotphimCrawler
import threading
import re
from utils import slugify_title



class MovieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Streaming Application")
        self.root.geometry("800x500")
        self.root.resizable(True, True)  # Cho phép thay đổi kích thước cửa sổ

        # Thêm menu fullscreen
        self.is_fullscreen = False
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        window_width = 800
        window_height = 500
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        root.configure(bg="white")
        root.title("Movie Streaming App")
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white")
        style.configure("TCheckbutton", background="white")
        # Khởi tạo dữ liệu
        self.movies = []
        self.users = []
        self.current_user = None
        
        # Tạo các thư mục cần thiết
        self.create_directories()
        
        # Load dữ liệu
        self.load_data()
        
        # Tạo giao diện đăng nhập
        self.show_login_screen()

    def create_directories(self):
        """Tạo các thư mục cần thiết cho ứng dụng"""
        directories = ['data', 'images', 'movies']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def load_data(self):
        """Load dữ liệu từ file JSON"""
        try:
            with open('data/movies.json', 'r', encoding='utf-8') as f:
                self.movies = json.load(f)
        except FileNotFoundError:
            self.movies = []
            
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = []
        print("Số lượng phim được tải: ", len(self.movies))
    
    def save_data(self):
        """Lưu dữ liệu vào file JSON"""
        with open('data/movies.json', 'w', encoding='utf-8') as f:
            json.dump(self.movies, f, indent=4, ensure_ascii=False)
            
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=4, ensure_ascii=False)

    def create_left_panel(self, parent):
        frame = tk.Frame(parent, width=400, height=400, bg="white")
        frame.pack(side=tk.LEFT, padx=(50, 10), pady=30)
        frame.pack_propagate(False)

        tk.Label(frame, text="🎬 Movie Manager", font=("Segoe UI", 24, "bold"), fg="#007BFF", bg="white").pack(pady=(10, 30))

        try:
            img = Image.open("images/login.png")
            img = img.resize((320, 240), Image.Resampling.LANCZOS)
            self.img_tk = ImageTk.PhotoImage(img)
            tk.Label(frame, image=self.img_tk, bg="white").pack()
        except:
            tk.Label(frame, text="[Image not found]", fg="red", bg="white").pack()

        return frame

    def show_login_screen(self):
        # Xóa widget cũ
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Movie Manager - Sign In")
        self.root.geometry("900x500")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        bg_frame = tk.Frame(self.root, bg="white")
        bg_frame.pack(fill=tk.BOTH, expand=True)

        # ==== TRÁI ====
        self.create_left_panel(bg_frame)

        # ==== PHẢI ====
        right_frame = tk.Frame(bg_frame, width=400, height=400, bg="white")
        right_frame.pack(side=tk.RIGHT, padx=(10, 50), pady=30)
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="Sign in", font=("Segoe UI", 20, "bold"), fg="#007BFF", bg="white").pack(pady=(10, 25))

        form = tk.Frame(right_frame, bg="white")
        form.pack()

        tk.Label(form, text="Username", font=("Segoe UI", 10), bg="white").grid(row=0, column=0, sticky="w")
        self.username_entry = ttk.Entry(form, width=32, font=("Segoe UI", 10))
        self.username_entry.grid(row=1, column=0, pady=(5, 15), ipady=4)

        tk.Label(form, text="Password", font=("Segoe UI", 10), bg="white").grid(row=2, column=0, sticky="w")
        self.password_entry = ttk.Entry(form, width=32, font=("Segoe UI", 10), show="*")
        self.password_entry.grid(row=3, column=0, pady=(5, 15), ipady=4)

        self.is_admin = tk.BooleanVar()
        tk.Checkbutton(
            form,
            text="Log in as administrator",
            variable=self.is_admin,
            font=("Segoe UI", 9),
            bg="white"
        ).grid(row=4, column=0, sticky="w", pady=(5, 15))

        ttk.Button(form, text="Sign in", command=self.login).grid(row=5, column=0, pady=(10, 20), ipadx=10)

        bottom_frame = tk.Frame(right_frame, bg="white")
        bottom_frame.pack()
        tk.Label(bottom_frame, text="Don't have an account?", bg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        register_link = tk.Label(
            bottom_frame, text=" Sign up", fg="#007BFF", bg="white", cursor="hand2", font=("Segoe UI", 9, "underline")
        )
        register_link.pack(side=tk.LEFT)
        register_link.bind("<Button-1>", lambda e: self.show_register_screen())

    def login(self):
        """Xử lý đăng nhập"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        is_admin = self.is_admin.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        # Kiểm tra đăng nhập quản trị
        if is_admin:
            for user in self.users:
                if user['username'] == username and user['password'] == password:
                    if user.get('role') == 'admin':
                        self.current_user = user
                        messagebox.showinfo("Success", "Admin login successful!")
                        self.create_admin_gui()
                        return
                    else:
                        messagebox.showerror("Error", "You are not an administrator.")
                        return
            messagebox.showerror("Error", "Invalid admin credentials")
            return
        
        # Kiểm tra đăng nhập người dùng thường
        for user in self.users:
            if user['username'] == username and user['password'] == password:
                if user.get('is_locked', False):
                    messagebox.showerror("Error", "This account has been locked. Please contact administrator.")
                    return
                self.current_user = user
                if 'favorites' not in self.current_user:
                    self.current_user['favorites'] = []
                messagebox.showinfo("Success", "Login successful!")
                self.create_main_gui()
                return
        
        messagebox.showerror("Error", "Invalid username or password")

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
    
    def create_main_gui(self):
        # Xóa các widget cũ
        for widget in self.root.winfo_children():
            widget.destroy()

        # Tạo menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Menu File
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Menu", menu=file_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Menu User
        user_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="User", menu=user_menu)
        user_menu.add_command(label="Profile", command=self.show_profile)
        user_menu.add_command(label="Yêu thích", command=self.show_favorites)
        # Tạo frame chính
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Thanh tìm kiếm
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_criteria = tk.StringVar(value="Tên phim")
        self.criteria_combobox = ttk.Combobox(
            search_frame,
            textvariable=self.search_criteria,
            values=["Tên phim", "Năm", "Thể loại"],
            state="readonly",
            width=12
        )
        self.criteria_combobox.pack(side=tk.LEFT, padx=5)  # HIỆN combobox

        ttk.Button(search_frame, text="Tìm kiếm", command=self.search_movies).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Hiện tất cả", command=self.show_all_movies).pack(side=tk.LEFT, padx=5)

        # Không hiển thị các label và entry lọc nâng cao
        self.rating_filter = tk.StringVar()
        self.year_filter = tk.StringVar()

        # Frame danh sách phim
        self.movie_frame = ttk.Frame(self.main_frame)
        self.movie_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas + Scroll
        self.canvas = tk.Canvas(self.movie_frame, bg="white")
        self.scrollbar = ttk.Scrollbar(self.movie_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.movies_per_page = 10  # Hiển thị 10 phim mỗi trang
        self.current_page = 0
        self.display_movies()

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)

    def show_all_movies(self):
        self.display_movies()

    def search_movies(self):
        keyword = self.search_var.get().strip().lower()
        criteria = self.search_criteria.get()
        rating_min = self.rating_filter.get()
        year_filter = self.year_filter.get()

        try:
            rating_min = float(rating_min) if rating_min else None
        except:
            rating_min = None

        filtered = []
        for movie in self.movies:
            match = True

            # Tìm kiếm chính
            if keyword:
                if criteria == "Tên phim" and keyword not in movie.get('title', '').lower():
                    match = False
                if criteria == "Năm" and keyword not in str(movie.get('year', '')).lower():
                    match = False
                if criteria == "Thể loại" and keyword not in movie.get('genre', '').lower():
                    match = False

            # Lọc nâng cao
            if rating_min is not None:
                try:
                    if float(movie.get('rating', 0)) < rating_min:
                        match = False
                except:
                    match = False
            if year_filter and str(movie.get('year', '')) != year_filter:
                match = False

            if match:
                filtered.append(movie)

        self.current_page = 0
        self.display_movies(filtered)

    def filter_by_genre(self, genre):
        """Lọc phim theo thể loại"""
        filtered = [m for m in self.movies if genre.lower() in m.get('genre', '').lower()]
        self.search_var.set("")
        self.rating_filter.set("")
        self.year_filter.set("")
        self.current_page = 0
        self.display_movies(filtered)

    def display_movies(self, movies=None):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # ✅ Hiện lại scrollbar và bind cuộn
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        movie_list = movies if movies is not None else self.movies
        print("Số lượng phim để hiển thị:", len(movie_list))

        if not movie_list:
            ttk.Label(self.scrollable_frame, text="No movies available.", font=('Arial', 12)).pack(pady=20)
            return

        total_pages = (len(movie_list) - 1) // self.movies_per_page + 1
        start = self.current_page * self.movies_per_page
        end = start + self.movies_per_page
        page_movies = movie_list[start:end]

        for movie in page_movies:
            self.create_movie_widget(movie)

        # Phân trang
        pagination_frame = ttk.Frame(self.scrollable_frame)
        pagination_frame.pack(pady=10)

        if self.current_page > 0:
            ttk.Button(pagination_frame, text="Về trang đầu", command=lambda: self.go_to_first_page(movie_list)).pack(side=tk.LEFT, padx=5)

        ttk.Button(pagination_frame, text="Trang trước", command=lambda: self.change_page(-1, movie_list)).pack(side=tk.LEFT, padx=5)
        ttk.Label(pagination_frame, text=f"Trang {self.current_page + 1} / {total_pages}").pack(side=tk.LEFT, padx=5)
        ttk.Button(pagination_frame, text="Trang sau", command=lambda: self.change_page(1, movie_list)).pack(side=tk.LEFT, padx=5)

        if self.current_page < total_pages - 1:
            ttk.Button(pagination_frame, text="Về trang cuối", command=lambda: self.go_to_last_page(movie_list)).pack(side=tk.LEFT, padx=5)

    def go_to_first_page(self, movie_list):
        self.current_page = 0
        self.display_movies(movie_list)

    def go_to_last_page(self, movie_list):
        total_pages = (len(movie_list) - 1) // self.movies_per_page + 1
        self.current_page = total_pages - 1
        self.display_movies(movie_list)

    def change_page(self, delta, movie_list):
        total_pages = (len(movie_list) - 1) // self.movies_per_page + 1
        self.current_page = max(0, min(self.current_page + delta, total_pages - 1))
        self.display_movies(movie_list)

    def create_movie_widget(self, movie):
        movie_frame = ttk.Frame(self.scrollable_frame, padding=10, style="Movie.TFrame")
        movie_frame.pack(fill=tk.X, pady=8)

        # === POSTER ===
        poster_displayed = False
        genre_slug = movie.get('genre', '').lower().replace(' ', '-')
        poster_filename = movie.get("poster_filename") or f"{slugify_title(movie['title'])}.jpg"
        poster_path = f"images/{genre_slug}/{poster_filename}"

        print(f"🧩 Đang tìm ảnh: {poster_path}")

        try:
            if os.path.exists(poster_path):
                image = Image.open(poster_path)
                image = image.resize((100, 150), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                poster_label = ttk.Label(movie_frame, image=photo)
                poster_label.image = photo
                poster_label.pack(side=tk.LEFT, padx=(10, 15))
                poster_displayed = True
            else:
                print(f"❓ Không tìm thấy file poster: {poster_path}")
        except UnidentifiedImageError:
            print(f"⚠️ Ảnh bị lỗi: {poster_path}")
        except Exception as e:
            print(f"❌ Lỗi poster: {e}")

        if not poster_displayed:
            ttk.Label(movie_frame, text="[No Poster]", width=15).pack(side=tk.LEFT, padx=(10, 15))

        # === INFO ===
        info_frame = ttk.Frame(movie_frame, style="Movie.TFrame")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(info_frame, text=movie.get('title', 'No title'), font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(0, 2))
        ttk.Label(info_frame, text=f"Thể loại: {movie.get('genre', 'Unknown')}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Năm: {movie.get('year', 'Unknown')}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Rating: {movie.get('rating', 'N/A')}").pack(anchor='w')
        ttk.Label(info_frame, text=movie.get('description', ''), wraplength=550, justify=tk.LEFT).pack(anchor='w', pady=5)

        button_frame = ttk.Frame(info_frame)
        button_frame.pack(anchor='w', pady=(0, 5))

        ttk.Button(button_frame, text="▶ Xem phim", command=lambda m=movie: self.watch_movie(m)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❤ Yêu thích", command=lambda m=movie: self.add_to_favorites(m)).pack(side=tk.LEFT)

    def watch_movie(self, movie):
        webbrowser.open(movie['movie_url'])
    
    def add_to_favorites(self, movie):
        favorites = self.current_user.setdefault('favorites', [])
        if movie['url'] not in [f['url'] for f in favorites]:
            favorites.append(movie)
            self.save_data()
            messagebox.showinfo("Thành công", f"Đã thêm {movie['title']} vào danh sách yêu thích!")
        else:
            messagebox.showinfo("Thông báo", f"{movie['title']} đã có trong danh sách yêu thích.")
    
    def remove_from_favorites(self, movie):
        favorites = self.current_user.get('favorites', [])
        self.current_user['favorites'] = [f for f in favorites if f['url'] != movie['url']]
        self.save_data()
        messagebox.showinfo("Đã xóa", f"Đã xóa '{movie['title']}' khỏi danh sách yêu thích.")
        self.show_favorites()  # Cập nhật lại giao diện

    def show_favorites(self):
        # Xóa toàn bộ nội dung hiện tại
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Cho phép cuộn lại và gán scrollbar
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        fav_movies = self.current_user.get('favorites', [])

        ttk.Label(self.scrollable_frame, text="Danh sách yêu thích", font=('Segoe UI', 16, 'bold')).pack(pady=15)

        if not fav_movies:
            ttk.Label(self.scrollable_frame, text="(Chưa có phim yêu thích)").pack(pady=20)
            return

        for movie in fav_movies:
            movie_frame = ttk.Frame(self.scrollable_frame, padding=10)
            movie_frame.pack(fill=tk.X, pady=5, padx=20)

            # === POSTER ===
            poster_displayed = False
            genre_slug = movie.get('genre', '').lower().replace(' ', '-')
            poster_filename = movie.get("poster_filename") or f"{slugify_title(movie['title'])}.jpg"
            poster_path = f"images/{genre_slug}/{poster_filename}"

            try:
                if os.path.exists(poster_path):
                    image = Image.open(poster_path)
                    image = image.resize((80, 120), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    poster_label = ttk.Label(movie_frame, image=photo)
                    poster_label.image = photo
                    poster_label.pack(side=tk.LEFT, padx=(0, 10))
                    poster_displayed = True
                else:
                    print(f"❓ Không tìm thấy file poster: {poster_path}")
            except:
                print(f"❌ Lỗi khi mở poster: {poster_path}")

            if not poster_displayed:
                ttk.Label(movie_frame, text="[No Poster]", width=15).pack(side=tk.LEFT, padx=(0, 10))

            # === INFO & BUTTONS ===
            info_frame = ttk.Frame(movie_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            ttk.Label(info_frame, text=movie.get('title', 'No title'), font=('Segoe UI', 13, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"Thể loại: {movie.get('genre', 'Unknown')}").pack(anchor='w')
            btn_frame = ttk.Frame(info_frame)
            btn_frame.pack(anchor='w', pady=5)

            ttk.Button(btn_frame, text="▶ Xem phim", command=lambda m=movie: self.watch_movie(m)).pack(side=tk.LEFT, padx=(0, 10))

            ttk.Button(btn_frame, text="🗑️Xóa khỏi yêu thích", command=lambda m=movie: self.remove_from_favorites(m)).pack(side=tk.LEFT)

        # ✅ Cuộn về đầu sau khi hiển thị
        self.canvas.yview_moveto(0)

    def show_register_screen(self):
    # Xóa widget cũ
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Movie Manager - Register")
        self.root.geometry("900x500")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        bg_frame = tk.Frame(self.root, bg="white")
        bg_frame.pack(fill=tk.BOTH, expand=True)

        # ==== TRÁI ====
        self.create_left_panel(bg_frame)

        # ==== PHẢI ====
        right_frame = tk.Frame(bg_frame, width=400, height=400, bg="white")
        right_frame.pack(side=tk.RIGHT, padx=(10, 50), pady=30)
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="Create Account", font=("Segoe UI", 20, "bold"), fg="#007BFF", bg="white").pack(pady=(10, 25))

        form = tk.Frame(right_frame, bg="white")
        form.pack()

        # Username
        tk.Label(form, text="Username", font=("Segoe UI", 10), bg="white").grid(row=0, column=0, sticky="w")
        username_entry = ttk.Entry(form, width=32, font=("Segoe UI", 10))
        username_entry.grid(row=1, column=0, pady=(5, 15), ipady=4)

        # Password
        tk.Label(form, text="Password", font=("Segoe UI", 10), bg="white").grid(row=2, column=0, sticky="w")
        password_entry = ttk.Entry(form, width=32, font=("Segoe UI", 10), show="*")
        password_entry.grid(row=3, column=0, pady=(5, 15), ipady=4)

        # Confirm Password
        tk.Label(form, text="Confirm Password", font=("Segoe UI", 10), bg="white").grid(row=4, column=0, sticky="w")
        confirm_password_entry = ttk.Entry(form, width=32, font=("Segoe UI", 10), show="*")
        confirm_password_entry.grid(row=5, column=0, pady=(5, 15), ipady=4)

        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm_password = confirm_password_entry.get()

            if not username or not password or not confirm_password:
                messagebox.showerror("Error", "Please fill in all fields")
                return

            if password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match")
                return

            for user in self.users:
                if user['username'] == username:
                    messagebox.showerror("Error", "Username already exists")
                    return

            self.users.append({
                'username': username,
                'password': password,
                'role': 'user',
                'favorites': []
            })

            self.save_data()
            messagebox.showinfo("Success", "Registration successful!")
            self.show_login_screen()

        ttk.Button(form, text="Register", command=register).grid(row=6, column=0, pady=(10, 20), ipadx=10)

        # Link quay lại login
        back_link = tk.Label(
            right_frame,
            text="← Back to Sign in",
            fg="#007BFF",
            bg="white",
            cursor="hand2",
            font=("Segoe UI", 9, "underline")
        )
        back_link.pack()
        back_link.bind("<Button-1>", lambda e: self.show_login_screen())

    def logout(self):
        """Đăng xuất"""
        self.current_user = None
        self.show_login_screen()
    
    def show_profile(self):
        # 1. Xóa toàn bộ widget trong cửa sổ chính
        for widget in self.root.winfo_children():
            widget.destroy()

        # 2. Tạo lại thanh menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Menu", menu=file_menu)
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Exit", command=self.root.quit)

        user_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="User", menu=user_menu)
        user_menu.add_command(label="Profile", command=self.show_profile)
        user_menu.add_command(label="Yêu thích", command=self.show_favorites)

        # 3. Tạo main frame chứa giao diện
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        main_content = ttk.Frame(self.main_frame)
        main_content.pack(fill=tk.BOTH, expand=True, pady=40, padx=40)

        # ==== TRÁI: ẢNH ====
        left_frame = tk.Frame(main_content, width=300, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)

        try:
            img = Image.open("images/Profile.jpg")
            img = img.resize((200, 200), Image.LANCZOS)
            self.profile_img = ImageTk.PhotoImage(img)
            tk.Label(left_frame, image=self.profile_img, bg="white").pack(pady=5)
        except:
            tk.Label(left_frame, text="[Không thể tải ảnh]", fg="red", bg="white").pack()

        # ==== PHẢI: THÔNG TIN ====
        right_frame = tk.Frame(main_content, bg="white")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        ttk.Label(right_frame, text="Thông tin tài khoản", font=("Segoe UI", 16, "bold")).pack(pady=(10, 20))
        ttk.Label(right_frame, text=f"👤 Username: {self.current_user['username']}", font=("Segoe UI", 12)).pack(anchor='w', pady=5)
        ttk.Label(right_frame, text=f"🔒 Role: {self.current_user['role']}", font=("Segoe UI", 12)).pack(anchor='w', pady=5)

        num_favorites = len(self.current_user.get('favorites', []))
        ttk.Label(right_frame, text=f"❤ Số phim yêu thích: {num_favorites}", font=("Segoe UI", 12)).pack(anchor='w', pady=5)

        # ==== NÚT QUAY LẠI ====
        ttk.Button(right_frame, text="⬅ Quay lại trang chính", command=self.create_main_gui).pack(anchor='w', pady=(30, 5))

    def create_admin_gui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ==== ẢNH BÊN TRÁI ====
        left_frame = tk.Frame(main_frame, width=300, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

        try:
            img = Image.open("images/login.png")
            img = img.resize((250, 200), Image.LANCZOS)
            self.admin_img = ImageTk.PhotoImage(img)
            tk.Label(left_frame, image=self.admin_img, bg="white").pack()
            tk.Label(left_frame, text="🎬 Movie Manager", font=("Segoe UI", 16, "bold"), fg="#007BFF", bg="white").pack(pady=10)
        except:
            tk.Label(left_frame, text="[Không thể tải ảnh]", fg="red", bg="white").pack()

        # ==== NOTEBOOK BÊN PHẢI ====
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Menu", menu=file_menu)
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Exit", command=self.root.quit)

        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # === TAB QUẢN LÝ PHIM ===
        movies_frame = ttk.Frame(notebook)
        notebook.add(movies_frame, text="Quản lý phim")

        movie_canvas = tk.Canvas(movies_frame, bg="white")
        movie_scrollbar = ttk.Scrollbar(movies_frame, orient="vertical", command=movie_canvas.yview)
        scrollable_movie_frame = ttk.Frame(movie_canvas)

        scrollable_movie_frame.bind("<Configure>", lambda e: movie_canvas.configure(scrollregion=movie_canvas.bbox("all")))
        movie_canvas.create_window((0, 0), window=scrollable_movie_frame, anchor="nw")
        movie_canvas.configure(yscrollcommand=movie_scrollbar.set)

        movie_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        movie_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for movie in self.movies:
            movie_row = ttk.Frame(scrollable_movie_frame, padding=5)
            movie_row.pack(fill=tk.X, pady=2)
            ttk.Label(movie_row, text=movie["title"], width=40).pack(side=tk.LEFT, padx=5)
            ttk.Button(movie_row, text="Sửa", command=lambda m=movie: self.edit_movie(m)).pack(side=tk.LEFT, padx=2)
            ttk.Button(movie_row, text="Xóa", command=lambda m=movie: self.delete_movie(m)).pack(side=tk.LEFT, padx=2)

        # === TAB QUẢN LÝ NGƯỜI DÙNG ===
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="Quản lý người dùng")

        user_canvas = tk.Canvas(users_frame, bg="white")
        user_scrollbar = ttk.Scrollbar(users_frame, orient="vertical", command=user_canvas.yview)
        scrollable_user_frame = ttk.Frame(user_canvas)

        scrollable_user_frame.bind("<Configure>", lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all")))
        user_canvas.create_window((0, 0), window=scrollable_user_frame, anchor="nw")
        user_canvas.configure(yscrollcommand=user_scrollbar.set)

        user_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        user_scrollbar.pack(side=tk.RIGHT, fill="y")

        # Dòng tiêu đề
        header = ttk.Frame(scrollable_user_frame, padding=5)
        header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header, text="Username", width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(header, text="Role", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(header, text="Actions", width=20).pack(side=tk.LEFT, padx=5)

        # Danh sách user
        for user in self.users:
            user_row = ttk.Frame(scrollable_user_frame, padding=5)
            user_row.pack(fill=tk.X, pady=2)

            ttk.Label(user_row, text=user["username"], width=20).pack(side=tk.LEFT, padx=5)
            ttk.Label(user_row, text=user["role"], width=10).pack(side=tk.LEFT, padx=5)

            # Chỉ tạo nút cho user thường
            if user["role"] != "admin":
                ttk.Button(
                    user_row, text="Khóa/Mở khóa",
                    command=lambda u=user: self.toggle_user_lock(u)
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    user_row, text="Xóa",
                    command=lambda u=user: self.delete_user(u)
                ).pack(side=tk.LEFT, padx=2)


    def edit_movie(self, movie):
        """Sửa thông tin phim"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Sửa thông tin phim")
        edit_window.geometry("400x300")
        
        ttk.Label(edit_window, text="Tiêu đề:").pack(pady=5)
        title_entry = ttk.Entry(edit_window, width=40)
        title_entry.insert(0, movie['title'])
        title_entry.pack(pady=5)
        
        ttk.Label(edit_window, text="Năm:").pack(pady=5)
        year_entry = ttk.Entry(edit_window, width=40)
        year_entry.insert(0, movie.get('year', ''))
        year_entry.pack(pady=5)
        
        ttk.Label(edit_window, text="Mô tả:").pack(pady=5)
        desc_text = tk.Text(edit_window, width=40, height=5)
        desc_text.insert('1.0', movie.get('description', ''))
        desc_text.pack(pady=5)
        
        def save_changes():
            movie['title'] = title_entry.get()
            movie['year'] = year_entry.get()
            movie['description'] = desc_text.get('1.0', 'end-1c')
            self.save_data()
            self.create_admin_gui()  # Refresh admin interface
            edit_window.destroy()
            messagebox.showinfo("Success", "Movie information updated successfully!")
        
        ttk.Button(edit_window, text="Lưu", command=save_changes).pack(pady=10)
    
    def delete_movie(self, movie):
        """Xóa phim"""
        if messagebox.askyesno("Confirm", f"Bạn có chắc muốn xóa phim '{movie['title']}'?"):
            self.movies.remove(movie)
            self.save_data()
            self.create_admin_gui()  # Refresh admin interface
            messagebox.showinfo("Success", "Movie deleted successfully!")
    
    def toggle_user_lock(self, user):
        """Khóa/Mở khóa tài khoản người dùng"""
        user['is_locked'] = not user.get('is_locked', False)
        self.save_data()
        self.create_admin_gui()  # Refresh admin interface
        status = "locked" if user['is_locked'] else "unlocked"
        messagebox.showinfo("Success", f"User {user['username']} has been {status}!")
    
    def delete_user(self, user):
        """Xóa tài khoản người dùng"""
        if messagebox.askyesno("Confirm", f"Bạn có chắc muốn xóa tài khoản '{user['username']}'?"):
            self.users.remove(user)
            self.save_data()
            self.create_admin_gui()  # Refresh admin interface
            messagebox.showinfo("Success", "User deleted successfully!")



if __name__ == "__main__":
    root = tk.Tk()
    app = MovieApp(root)
    root.mainloop()
