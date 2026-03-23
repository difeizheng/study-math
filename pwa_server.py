"""
PWA 静态文件服务器
与 Streamlit 并行运行，提供 PWA 所需的静态文件
"""
import http.server
import socketserver
import threading
import os

PORT = 8502
DIRECTORY = "static"

class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # 添加 CORS 头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def run_server():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with socketserver.TCPServer(("", PORT), StaticHandler) as httpd:
        print(f"[PWA 静态文件服务器] 运行在 http://localhost:{PORT}")
        print(f"[PWA] Manifest: http://localhost:{PORT}/manifest.json")
        print(f"[PWA] Service Worker: http://localhost:{PORT}/sw.js")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
