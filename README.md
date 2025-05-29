# Movie Streaming Application

Ứng dụng xem phim được phát triển bằng Python và tkinter, cho phép người dùng xem, quản lý và tương tác với các bộ phim.

## Tính năng

- Giao diện người dùng thân thiện với tkinter
- Quản lý người dùng (đăng ký, đăng nhập)
- Phân quyền người dùng (admin/user)
- CRUD (Create, Read, Update, Delete) cho phim
- Crawl dữ liệu phim từ 
- Lưu trữ dữ liệu bằng JSON
- Tải và hiển thị poster phim

## Yêu cầu hệ thống

- Python 3.7 trở lên
- Các thư viện Python:
  - tkinter
  - requests
  - beautifulsoup4
  - pillow
  - pyinstaller

## Cài đặt

1. Clone repository:
```bash
git clone [repository-url]
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Sử dụng

1. Chạy ứng dụng:
```bash
python main.py
```

2. Đăng ký tài khoản mới hoặc đăng nhập với tài khoản hiện có

3. Sử dụng các chức năng:
   - Xem danh sách phim
   - Thêm phim mới
   - Chỉnh sửa thông tin phim
   - Xóa phim
   - Tìm kiếm phim

## Đóng gói ứng dụng

Để tạo file thực thi:
```bash
pyinstaller --onefile --windowed main.py
```

File thực thi sẽ được tạo trong thư mục `dist/`

## Cấu trúc thư mục

```
movie-app/
├── data/
│   ├── movies.json
│   └── users.json
├── images/
│   └── [poster files]
├── main.py
├── movie_crawler.py
├── requirements.txt
└── README.md
```

## Lưu ý

- Đảm bảo có kết nối internet để sử dụng chức năng crawl dữ liệu
- Dữ liệu được lưu trữ cục bộ trong thư mục `data/`
- Hình ảnh poster được lưu trong thư mục `images/` 