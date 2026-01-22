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
from openpyxl import load_workbook

#配置参数
PORT = 3000
BASE_URL = 'http://localhost:16380'
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
        """处理API请求，读取Excel文件并返回统计数据"""
        try:
            #读取Excel文件并统计数据
            excel_path = os.path.join('.', 'mock_bugs.xlsx')
            if not os.path.exists(excel_path):
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Excel file not found'}).encode())
                return
            
            #加载Excel文件
            wb = load_workbook(excel_path)
            ws = wb.active
            
            #统计数据
            projects = {}
            total_bugs = 0
            
            #跳过表头，从第二行开始读取
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[0]:  # 跳过空行
                    continue
                
                project_name = row[0]
                bug_id = row[1]
                title = row[2]
                priority = row[3]
                status = row[4]
                
                #初始化项目数据
                if project_name not in projects:
                    projects[project_name] = {
                        'total_bugs': 0,
                        'bugs_by_priority': {
                            '高': 0,
                            '中': 0,
                            '低': 0
                        },
                        'bugs_by_status': {
                            '未解决': 0,
                            '进行中': 0,
                            '已解决': 0
                        },
                        'bugs': []
                    }
                
                #更新统计数据
                projects[project_name]['total_bugs'] += 1
                projects[project_name]['bugs_by_priority'][priority] += 1
                projects[project_name]['bugs_by_status'][status] += 1
                projects[project_name]['bugs'].append({
                    'id': bug_id,
                    'title': title,
                    'priority': priority,
                    'status': status
                })
                
                total_bugs += 1
            
            #构建响应数据
            response_data = {
                'total_bugs': total_bugs,
                'projects': projects
            }
            
            #设置响应头
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            #返回响应数据
            self.wfile.write(json.dumps(response_data).encode())
            
            print("[API处理] 成功读取并统计Excel数据")
            
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
        
        #处理路径，移除查询参数
        path = self.path.split('?')[0]
        
        #处理根路径
        if path == '/':
            path = '/index.html'
        
        #处理特殊路径
        if path == '/@vite/client':
            #返回空响应，避免404错误
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', '0')
            self.end_headers()
            print("[静态文件] 处理特殊路径: /@vite/client")
            return
        
        #构建文件路径
        file_path = os.path.join(static_dir, path[1:])  # 去掉开头的'/'
        
        #如果文件不存在，尝试在当前目录查找
        if not (os.path.exists(file_path) and os.path.isfile(file_path)) and static_dir == 'public':
            file_path = os.path.join('.', path[1:])
        
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
            #如果是根路径或index.html，尝试返回index.html
            if path == '/' or path == '/index.html':
                index_path = os.path.join(static_dir, 'index.html')
                if not (os.path.exists(index_path) and os.path.isfile(index_path)) and static_dir == 'public':
                    index_path = os.path.join('.', 'index.html')
                
                if os.path.exists(index_path) and os.path.isfile(index_path):
                    try:
                        #读取index.html文件内容
                        with open(index_path, 'rb') as file:
                            content = file.read()
                        
                        #发送响应
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Length', str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                        
                        print(f"[静态文件] 成功发送: {index_path}")
                        return
                    except Exception as e:
                        print(f"[静态文件错误] 读取index.html失败: {str(e)}")
                        self.send_error(500, "Internal server error")
                        return
            
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
