import sys
import os

# Thêm thư mục gốc vào sys.path để nạp đúng server.py, src và data
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app

# Vercel Serverless Function entry point
# Exposes ASGI 'app' for @vercel/python

