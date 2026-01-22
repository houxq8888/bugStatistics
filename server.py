#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python HTTP服务器，用于替代Node.js服务器
实现静态文件服务和GitLab API代理功能
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import os
import sys

#配置参数
PORT = 3000
BASE_URL = 'http://192.168.1.152:16380'
API_TOKEN = '' # GitLab API令牌，根据实际情况填写

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def do_GET(self):
        #记录请求的详细信息
        client_ip = self.client_address[0]
        print(f"[GET请求] 客户端IP: {client_ip}, 请求路径: {self.path}")
        
        #处理API代理请求
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            #处理静态文件请求
            self.handle_static_file()
    
    def do_POST(self):
        #记录请求的详细信息
        client_ip = self.client_address[0]
        print(f"[POST请求] 客户端IP: {client_ip}, 请求路径: {self.path}")
        
        #处理API代理请求
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404, "File not found")
    
    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    
    def handle_api_request(self):
        """处理GitLab API代理请求"""
        try:
            #构建GitLab API URL
            api_path = self.path[4:]  # 去掉'/api'前缀
            gitlab_url = f"{BASE_URL}{api_path}"
            
            print(f"[API代理] 转发到: {gitlab_url}")
            
            #构建请求头
            headers = {}
            if API_TOKEN:
                headers['Authorization'] = f'Bearer {API_TOKEN}'
            
            #转发请求到GitLab API
            req = urllib.request.Request(gitlab_url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                data = response.read()
                
                #设置响应头
                self.send_response(response.getcode())
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                #返回响应数据
                self.wfile.write(data)
                
        except urllib.error.HTTPError as e:
            print(f"[API错误] HTTP错误: {e.code} - {e.reason}")
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
            
        except Exception as e:
            print(f"[API错误] 未知错误: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Internal server error'}).encode())
    
    def handle_static_file(self):
        """处理静态文件请求"""
        #设置静态文件目录
        static_dir = 'public' if os.path.exists('public') else '.'
        
        #处理根路径
        if self.path == '/':
            self.path = '/index.html'
        
        #构建文件路径
        file_path = os.path.join(static_dir, self.path[1:])  # 去掉开头的'/'
        
        #如果文件不存在，尝试在当前目录查找
        if not (os.path.exists(file_path) and os.path.isfile(file_path)) and static_dir == 'public':
            file_path = os.path.join('.', self.path[1:])
        
        #检查文件是否存在
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                #根据文件扩展名设置Content-Type
                content_type = self.guess_type(file_path)
                
                #读取文件内容
                with open(file_path, 'rb') as file:
                    content = file.read()
                
                #发送响应
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                
                print(f"[静态文件] 成功发送: {file_path}")
                
            except Exception as e:
                print(f"[静态文件错误] 读取文件失败: {str(e)}")
                self.send_error(500, "Internal server error")
        else:
            print(f"[静态文件] 文件不存在: {file_path}")
            self.send_error(404, "File not found")
    
    def guess_type(self, path):
        """根据文件扩展名猜测Content-Type"""
        ext = os.path.splitext(path)[1]
        
        content_types = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.txt': 'text/plain'
        }
        
        return content_types.get(ext.lower(), 'application/octet-stream')

def main():
    """主函数"""
    #检查是否需要创建public目录
    if not os.path.exists('public'):
        print("警告: public目录不存在，将使用当前目录作为静态文件目录")
    
    #创建HTTP服务器
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"服务器启动成功!")
        print(f"监听地址: http://localhost:{PORT}")
        print(f"静态文件目录: {'public' if os.path.exists('public') else '当前目录'}")
        print(f"GitLab API代理: {BASE_URL}")
        print("按 Ctrl+C 停止服务器")
        
        try:
            #启动服务器
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    main()
