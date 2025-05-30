import re

def slugify_title(title):
    """Chuyển tiêu đề phim thành tên file an toàn để lưu ảnh"""
    return re.sub(r'[^\w]', '_', title.strip())
