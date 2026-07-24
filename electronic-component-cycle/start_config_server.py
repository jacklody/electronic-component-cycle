#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理本地服务
使用方法：python start_config_server.py
然后打开 config-manager.html 就可以点按钮直接保存配置，不用下载替换
不需要安装任何依赖，Python标准库就能跑
"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

class ConfigHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/api/config":
            # 返回当前配置
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self._set_headers()
                self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "not found"}')
    
    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/api/save":
            # 保存配置
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                config = json.loads(post_data.decode('utf-8'))
                
                # 备份旧配置
                if os.path.exists(CONFIG_PATH):
                    backup_path = CONFIG_PATH + ".bak"
                    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                        with open(backup_path, 'w', encoding='utf-8') as f2:
                            f2.write(f.read())
                
                # 写入新配置
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                self._set_headers()
                self.wfile.write(json.dumps({"success": True, "message": "配置保存成功"}, ensure_ascii=False).encode('utf-8'))
                print("✅ 配置已保存到 config.json")
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
                print(f"❌ 保存失败：{e}")
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "not found"}')
    
    def log_message(self, format, *args):
        # 简化日志
        print(f"[{self.log_date_time_string()}] {args[0]}")

def run_server(port=8765):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ConfigHandler)
    print("=" * 60)
    print("🔧 电子元器件周期智能体 - 配置管理服务已启动")
    print(f"📡 服务地址：http://localhost:{port}")
    print("📂 现在打开 config-manager.html 就可以直接保存配置了")
    print("⏹️  按 Ctrl+C 停止服务")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
