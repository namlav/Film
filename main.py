#acc ad: admin,admin123
"""
được rồi về cơ bản ứng dụng xem phim hoạt động như vậy đã ổn. Giờ đến phần xử lý hệ thống ứng dụng. Tôi cần bạn giúp phân quyền người dùng, đơn giản là thêm một phần đăng nhập dành cho quản trị viên ở màn hình đăng nhập. Quản trị viên sẽ có toàn quyền truy cập dữ liệu ứng dụng (như thêm, xóa, sửa phim thông tin phim; khóa tài khoản người dùng,...). Người dùng bình thường chỉ có thể đăng nhập vào và chọn phim để xem cũng như thêm các phim vào mục yêu thích.
"""
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

class MovieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Streaming Application")
        self.root.geometry("1200x800")
        
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
    
    def show_login_screen(self):
        """Hiển thị màn hình đăng nhập"""
        # Xóa các widget cũ
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Tạo frame chính
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Tạo frame cho form đăng nhập
        login_frame = ttk.Frame(main_frame)
        login_frame.pack(expand=True)
        
        # Tiêu đề
        ttk.Label(login_frame, text="Movie Streaming App", font=('Arial', 20, 'bold')).pack(pady=20)
        
        # Form đăng nhập
        ttk.Label(login_frame, text="Username:").pack(pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.pack(pady=5)
        
        ttk.Label(login_frame, text="Password:").pack(pady=5)
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.pack(pady=5)
        
        # Thêm checkbox cho đăng nhập quản trị
        self.is_admin = tk.BooleanVar()
        ttk.Checkbutton(login_frame, text="Đăng nhập với tư cách quản trị viên", 
                       variable=self.is_admin).pack(pady=5)
        
        # Nút đăng nhập và đăng ký
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Register", command=self.show_register).pack(side=tk.LEFT, padx=5)
    
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
            if username == "admin" and password == "admin123":  # Mật khẩu mặc định cho admin
                self.current_user = {
                    'username': 'admin',
                    'role': 'admin'
                }
                messagebox.showinfo("Success", "Admin login successful!")
                self.create_admin_gui()
                return
            else:
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
        """Tạo giao diện chính sau khi đăng nhập"""
        # Xóa các widget cũ
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Tạo menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Menu File
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Movies", command=self.refresh_movies)
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
        self.criteria_combobox = ttk.Combobox(search_frame, textvariable=self.search_criteria, values=["Tên phim", "Năm", "Thể loại"], state="readonly", width=12)
        self.criteria_combobox.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Tìm kiếm", command=self.search_movies).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Hiện tất cả", command=self.show_all_movies).pack(side=tk.LEFT, padx=5)
        
        # Tạo frame cho danh sách phim
        self.movie_frame = ttk.Frame(self.main_frame)
        self.movie_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tạo canvas và scrollbar
        self.canvas = tk.Canvas(self.movie_frame)
        self.scrollbar = ttk.Scrollbar(self.movie_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Thêm binding để cập nhật width khi canvas thay đổi kích thước
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Hiển thị danh sách phim
        self.display_movies()

        # Gắn sự kiện scroll chuột
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows/macOS
    
    def show_all_movies(self):
        self.display_movies()

    def search_movies(self):
        keyword = self.search_var.get().strip().lower()
        criteria = self.search_criteria.get()
        if not keyword:
            self.display_movies()
            return
        filtered = []
        for movie in self.movies:
            if criteria == "Tên phim" and keyword in movie.get('title', '').lower():
                filtered.append(movie)
            elif criteria == "Năm" and keyword in str(movie.get('year', '')).lower():
                filtered.append(movie)
            elif criteria == "Thể loại" and keyword in movie.get('genre', '').lower():
                filtered.append(movie)
        self.display_movies(filtered)

    def display_movies(self, movies=None):
        """Hiển thị danh sách phim"""
        # Xóa các widget cũ
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        movie_list = movies if movies is not None else self.movies
        print("Số lượng phim để hiển thị:", len(movie_list))  # Debug

        if not movie_list:
            ttk.Label(self.scrollable_frame, text="No movies available. Please refresh the list.", font=('Arial', 12)).pack(pady=20)
            return

        for movie in movie_list:
            print("Movie:", movie)  # Debug
            movie_frame = ttk.Frame(self.scrollable_frame, padding=10)
            movie_frame.pack(fill=tk.X, pady=5)

            # Hiển thị poster (nếu có)
            poster_displayed = False
            poster_path = f"images/{movie['title'].replace(' ', '_')}.jpg"
            try:
                if not os.path.exists(poster_path) and movie.get('poster_url'):
                    response = requests.get(movie['poster_url'], timeout=10)
                    if response.status_code == 200:
                        with open(poster_path, 'wb') as f:
                            f.write(response.content)
                if os.path.exists(poster_path):
                    try:
                        image = Image.open(poster_path)
                        image = image.resize((150, 200), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        poster_label = ttk.Label(movie_frame, image=photo)
                        poster_label.image = photo
                        poster_label.pack(side=tk.LEFT, padx=10)
                        poster_displayed = True
                    except UnidentifiedImageError:
                        print(f"Ảnh poster bị lỗi: {poster_path}")
            except Exception as e:
                print(f"Error loading poster: {str(e)}")

            # Nếu không có poster, hiển thị label trống hoặc ảnh mặc định
            if not poster_displayed:
                poster_label = ttk.Label(movie_frame, text="[No Poster]", width=20)
                poster_label.pack(side=tk.LEFT, padx=10)

            # Luôn hiển thị thông tin phim
            info_frame = ttk.Frame(movie_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            ttk.Label(info_frame, text=movie.get('title', 'No title'), font=('Arial', 14, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"Year: {movie.get('year', 'Unknown')}").pack(anchor='w')
            ttk.Label(info_frame, text=f"Rating: {movie.get('rating', 'N/A')}").pack(anchor='w')
            ttk.Label(info_frame, text=movie.get('description', ''), wraplength=600).pack(anchor='w', pady=5)
            ttk.Button(
                info_frame,
                text="Xem phim",
                command=lambda m=movie: self.watch_movie(m)
            ).pack(anchor='w', pady=5)
            ttk.Button(
                info_frame,
                text="Yêu thích",
                command=lambda m=movie: self.add_to_favorites(m)
            ).pack(anchor='w', pady=5)
    
    def watch_movie(self, movie):
        webbrowser.open(movie['movie_url'])
    
    def add_to_favorites(self, movie):
        if 'favorites' not in self.current_user:
            self.current_user['favorites'] = []
        if movie['url'] not in [f['url'] for f in self.current_user['favorites']]:
            self.current_user['favorites'].append(movie)
            self.save_data()
            messagebox.showinfo("Thành công", f"Đã thêm {movie['title']} vào danh sách yêu thích!")
        else:
            messagebox.showinfo("Thông báo", f"{movie['title']} đã có trong danh sách yêu thích.")
    
    def show_favorites(self):
        fav_movies = self.current_user.get('favorites', [])
        fav_window = tk.Toplevel(self.root)
        fav_window.title("Danh sách yêu thích")
        fav_window.geometry("800x600")
        frame = ttk.Frame(fav_window)
        frame.pack(fill=tk.BOTH, expand=True)
        for movie in fav_movies:
            ttk.Label(frame, text=movie['title'], font=('Arial', 12, 'bold')).pack(anchor='w', pady=2)
            ttk.Button(frame, text="Xem phim", command=lambda m=movie: self.watch_movie(m)).pack(anchor='w')
    
    def refresh_movies(self):
        """Làm mới danh sách phim"""
        try:
            crawler = MotphimCrawler()
            if crawler.crawl_movies():
                self.movies = crawler.movies
                self.save_data()
                self.display_movies()
                messagebox.showinfo("Success", "Movies refreshed successfully!")
            else:
                messagebox.showerror("Error", "Failed to refresh movies. Please check your internet connection and try again.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while refreshing movies: {str(e)}")
    
    def show_register(self):
        """Hiển thị form đăng ký"""
        register_window = tk.Toplevel(self.root)
        register_window.title("Register")
        register_window.geometry("300x200")
        
        ttk.Label(register_window, text="Username:").pack(pady=5)
        username_entry = ttk.Entry(register_window)
        username_entry.pack(pady=5)
        
        ttk.Label(register_window, text="Password:").pack(pady=5)
        password_entry = ttk.Entry(register_window, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(register_window, text="Confirm Password:").pack(pady=5)
        confirm_password_entry = ttk.Entry(register_window, show="*")
        confirm_password_entry.pack(pady=5)
        
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
            register_window.destroy()
        
        ttk.Button(register_window, text="Register", command=register).pack(pady=10)
    
    def logout(self):
        """Đăng xuất"""
        self.current_user = None
        self.show_login_screen()
    
    def show_profile(self):
        """Hiển thị thông tin người dùng"""
        if not self.current_user:
            return
        
        profile_window = tk.Toplevel(self.root)
        profile_window.title("User Profile")
        profile_window.geometry("300x150")
        
        ttk.Label(profile_window, text=f"Username: {self.current_user['username']}", font=('Arial', 12)).pack(pady=10)
        ttk.Label(profile_window, text=f"Role: {self.current_user['role']}", font=('Arial', 12)).pack(pady=10)

    def create_admin_gui(self):
        """Tạo giao diện quản trị"""
        # Xóa các widget cũ
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Tạo menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Menu File
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Movies", command=self.refresh_movies)
        file_menu.add_separator()
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tạo notebook cho các tab quản lý
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab quản lý phim
        movies_frame = ttk.Frame(notebook)
        notebook.add(movies_frame, text="Quản lý phim")
        
        # Tạo canvas và scrollbar cho danh sách phim
        canvas = tk.Canvas(movies_frame)
        scrollbar = ttk.Scrollbar(movies_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Hiển thị danh sách phim với các nút quản lý
        for movie in self.movies:
            movie_frame = ttk.Frame(scrollable_frame, padding=5)
            movie_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(movie_frame, text=movie['title'], width=40).pack(side=tk.LEFT, padx=5)
            ttk.Button(movie_frame, text="Sửa", 
                      command=lambda m=movie: self.edit_movie(m)).pack(side=tk.LEFT, padx=2)
            ttk.Button(movie_frame, text="Xóa", 
                      command=lambda m=movie: self.delete_movie(m)).pack(side=tk.LEFT, padx=2)
        
        # Tab quản lý người dùng
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="Quản lý người dùng")
        
        # Tạo canvas và scrollbar cho danh sách người dùng
        canvas_users = tk.Canvas(users_frame)
        scrollbar_users = ttk.Scrollbar(users_frame, orient="vertical", command=canvas_users.yview)
        scrollable_frame_users = ttk.Frame(canvas_users)
        
        scrollable_frame_users.bind(
            "<Configure>",
            lambda e: canvas_users.configure(scrollregion=canvas_users.bbox("all"))
        )
        
        canvas_users.create_window((0, 0), window=scrollable_frame_users, anchor="nw")
        canvas_users.configure(yscrollcommand=scrollbar_users.set)
        
        canvas_users.pack(side="left", fill="both", expand=True)
        scrollbar_users.pack(side="right", fill="y")
        
        # Hiển thị danh sách người dùng với các nút quản lý
        for user in self.users:
            user_frame = ttk.Frame(scrollable_frame_users, padding=5)
            user_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(user_frame, text=user['username'], width=20).pack(side=tk.LEFT, padx=5)
            ttk.Label(user_frame, text=user['role'], width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(user_frame, text="Khóa/Mở khóa", 
                      command=lambda u=user: self.toggle_user_lock(u)).pack(side=tk.LEFT, padx=2)
            ttk.Button(user_frame, text="Xóa", 
                      command=lambda u=user: self.delete_user(u)).pack(side=tk.LEFT, padx=2)

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