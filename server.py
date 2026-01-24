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
import urllib.parse
import json
import os
import sys
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Any

# 导入数据库模块
from database import db_manager
# 导入认证模块
from auth import auth_manager, require_auth

# 配置参数
PORT = 9000
BASE_URL = 'http://localhost:16380'
API_TOKEN = ''
CACHE_ENABLED = True
CACHE_DURATION = 300

# HTTPS/SSL配置
SSL_ENABLED = False
SSL_CERT_FILE = 'server.crt'
SSL_KEY_FILE = 'server.key'

# 邮件通知配置
EMAIL_ENABLED = False
EMAIL_SMTP_SERVER = 'smtp.gmail.com'
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = ''
EMAIL_PASSWORD = ''
EMAIL_FROM = ''
EMAIL_TO = ''
BUG_THRESHOLD = 100  # Bug数量阈值

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 简单的内存缓存
cache_store: Dict[str, Dict[str, Any]] = {}

class GitLabAPIError(Exception):
    """GitLab API错误"""
    pass

class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if not CACHE_ENABLED:
            return None
        
        if key in cache_store:
            cache_data = cache_store[key]
            if datetime.now().timestamp() - cache_data['timestamp'] < CACHE_DURATION:
                logger.info(f"[缓存命中] {key}")
                return cache_data['data']
            else:
                del cache_store[key]
                logger.info(f"[缓存过期] {key}")
        return None
    
    @staticmethod
    def set(key: str, data: Any) -> None:
        """设置缓存"""
        if CACHE_ENABLED:
            cache_store[key] = {
                'data': data,
                'timestamp': datetime.now().timestamp()
            }
            logger.info(f"[缓存设置] {key}")
    
    @staticmethod
    def clear() -> None:
        """清空缓存"""
        cache_store.clear()
        logger.info("[缓存清空]")

class EmailNotifier:
    """邮件通知器"""
    
    @staticmethod
    def send_bug_alert(project_name: str, bug_count: int, threshold: int) -> bool:
        """发送Bug数量告警邮件"""
        if not EMAIL_ENABLED:
            logger.info("邮件通知未启用")
            return False
        
        if not EMAIL_USERNAME or not EMAIL_PASSWORD or not EMAIL_TO:
            logger.warning("邮件配置不完整，无法发送邮件")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            msg['Subject'] = f'[Bug告警] {project_name} - Bug数量超过阈值'
            
            body = f"""
            <html>
            <body>
                <h2>Bug数量告警</h2>
                <p>项目 <strong>{project_name}</strong> 的Bug数量已超过阈值！</p>
                <table border="1" cellpadding="10" style="border-collapse: collapse;">
                    <tr>
                        <td><strong>项目名称</strong></td>
                        <td>{project_name}</td>
                    </tr>
                    <tr>
                        <td><strong>当前Bug数</strong></td>
                        <td style="color: red; font-weight: bold;">{bug_count}</td>
                    </tr>
                    <tr>
                        <td><strong>告警阈值</strong></td>
                        <td>{threshold}</td>
                    </tr>
                    <tr>
                        <td><strong>超出数量</strong></td>
                        <td style="color: red; font-weight: bold;">{bug_count - threshold}</td>
                    </tr>
                    <tr>
                        <td><strong>告警时间</strong></td>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                <p>请及时处理项目中的Bug问题。</p>
                <p><a href="http://localhost:{PORT}">点击查看详情</a></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件发送成功: {project_name} - {bug_count} bugs")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    @staticmethod
    def check_and_notify(projects: List[Dict]) -> None:
        """检查所有项目并发送告警"""
        for project in projects:
            stats = project.get('stats', {})
            total_bugs = stats.get('total', 0)
            
            if total_bugs > BUG_THRESHOLD:
                project_name = project.get('name', '未知项目')
                EmailNotifier.send_bug_alert(project_name, total_bugs, BUG_THRESHOLD)

class GitLabAPIClient:
    """GitLab API客户端"""
    
    def __init__(self, base_url: str, api_token: str = ''):
        self.base_url = base_url
        self.api_token = api_token
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 构建查询参数
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        # 构建请求头
        headers = {
            'Content-Type': 'application/json'
        }
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        logger.info(f"[API请求] {method} {url}")
        
        try:
            if method == 'GET':
                req = urllib.request.Request(url, headers=headers)
            else:
                req_data = json.dumps(data).encode('utf-8') if data else None
                req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                logger.info(f"[API响应] 状态码: {response.getcode()}")
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP错误: {e.code} - {e.reason}"
            logger.error(f"[API错误] {error_msg}")
            raise GitLabAPIError(error_msg)
        except urllib.error.URLError as e:
            error_msg = f"URL错误: {e.reason}"
            logger.error(f"[API错误] {error_msg}")
            raise GitLabAPIError(error_msg)
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(f"[API错误] {error_msg}")
            raise GitLabAPIError(error_msg)
    
    def get_projects(self, page: int = 1, per_page: int = 20, 
                    search: Optional[str] = None) -> List[Dict]:
        """获取项目列表"""
        params = {'page': page, 'per_page': per_page}
        if search:
            params['search'] = search
        
        cache_key = f"projects_page_{page}_per_{per_page}_search_{search}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            projects = self._make_request('/api/v4/projects', params=params)
            CacheManager.set(cache_key, projects)
            return projects
        except GitLabAPIError:
            return []
    
    def get_issues(self, project_id: int, state: Optional[str] = None,
                  labels: Optional[str] = None, page: int = 1,
                  per_page: int = 100) -> List[Dict]:
        """获取项目的Issue列表"""
        params = {'page': page, 'per_page': per_page}
        if state:
            params['state'] = state
        if labels:
            params['labels'] = labels
        
        cache_key = f"issues_{project_id}_state_{state}_labels_{labels}_page_{page}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            issues = self._make_request(f'/api/v4/projects/{project_id}/issues', params=params)
            CacheManager.set(cache_key, issues)
            return issues
        except GitLabAPIError:
            return []
    
    def get_all_project_issues(self, project_id: int) -> List[Dict]:
        """获取项目的所有Issues（自动分页）"""
        all_issues = []
        page = 1
        per_page = 100
        
        while True:
            issues = self.get_issues(project_id, page=page, per_page=per_page)
            if not issues:
                break
            all_issues.extend(issues)
            if len(issues) < per_page:
                break
            page += 1
        
        return all_issues

# 初始化GitLab客户端
gitlab_client = GitLabAPIClient(BASE_URL, API_TOKEN)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def log_message(self, format: str, *args: Any) -> None:
        """自定义日志格式"""
        logger.info(f"[HTTP] {self.address_string()} - {format % args}")
    
    def do_GET(self):
        client_ip = self.client_address[0]
        logger.info(f"[GET请求] 客户端IP: {client_ip}, 请求路径: {self.path}")
        
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.handle_static_file()
    
    def do_POST(self):
        client_ip = self.client_address[0]
        logger.info(f"[POST请求] 客户端IP: {client_ip}, 请求路径: {self.path}")
        
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
    
    def send_json_response(self, data: Any, status: int = 200) -> None:
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def handle_api_request(self):
        """处理API请求"""
        try:
            api_path = self.path[4:]
            path_parts = api_path.split('?')
            endpoint = path_parts[0]
            
            # 解析查询参数
            query_params = {}
            if len(path_parts) > 1:
                query_string = path_parts[1]
                query_params = dict(urllib.parse.parse_qsl(query_string))
            
            # 获取项目列表
            if endpoint == '/projects':
                self.handle_get_projects(query_params)
            # 获取项目统计
            elif endpoint == '/projects/stats':
                self.handle_get_projects_stats(query_params)
            # 获取项目详情
            elif endpoint.startswith('/projects/') and endpoint.endswith('/issues'):
                project_id = int(endpoint.split('/')[2])
                self.handle_get_project_issues(project_id, query_params)
            # 获取项目趋势
            elif endpoint.startswith('/projects/') and endpoint.endswith('/trends'):
                project_id = int(endpoint.split('/')[2])
                self.handle_get_project_trends(project_id, query_params)
            # 获取所有项目列表（从数据库）
            elif endpoint == '/db/projects':
                self.handle_get_db_projects()
            # 获取项目Bug列表（从数据库）
            elif endpoint.startswith('/db/projects/') and endpoint.endswith('/bugs'):
                project_id = int(endpoint.split('/')[3])
                self.handle_get_db_project_bugs(project_id, query_params)
            # 用户注册
            elif endpoint == '/auth/register':
                self.handle_register()
            # 用户登录
            elif endpoint == '/auth/login':
                self.handle_login()
            # 用户登出
            elif endpoint == '/auth/logout':
                self.handle_logout()
            # 获取当前用户信息
            elif endpoint == '/auth/me':
                self.handle_get_current_user()
            # 列出用户
            elif endpoint == '/auth/users':
                self.handle_list_users()
            # 更新用户角色
            elif endpoint.startswith('/auth/users/') and endpoint.endswith('/role'):
                user_id = int(endpoint.split('/')[3])
                self.handle_update_user_role(user_id)
            # 清除缓存
            elif endpoint == '/cache/clear':
                CacheManager.clear()
                self.send_json_response({'message': '缓存已清除'})
            # 健康检查
            elif endpoint == '/health':
                self.send_json_response({'status': 'ok', 'timestamp': datetime.now().isoformat()})
            else:
                self.send_json_response({'error': '未知的API端点'}, 404)
                
        except Exception as e:
            logger.error(f"[API处理错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_projects(self, params: Dict) -> None:
        """处理获取项目列表请求"""
        try:
            page = int(params.get('page', 1))
            per_page = int(params.get('per_page', 20))
            search = params.get('search')
            
            projects = gitlab_client.get_projects(page, per_page, search)
            
            # 格式化项目数据
            formatted_projects = []
            for project in projects:
                formatted_projects.append({
                    'id': project.get('id'),
                    'name': project.get('name'),
                    'name_with_namespace': project.get('name_with_namespace'),
                    'description': project.get('description'),
                    'web_url': project.get('web_url'),
                    'created_at': project.get('created_at'),
                    'last_activity_at': project.get('last_activity_at')
                })
            
            self.send_json_response({'projects': formatted_projects})
            
        except Exception as e:
            logger.error(f"[获取项目列表错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_projects_stats(self, params: Dict) -> None:
        """处理获取项目统计请求"""
        try:
            projects = gitlab_client.get_projects(per_page=100)
            
            if not projects:
                logger.warning("[GitLab API不可用，使用模拟数据] 未获取到项目数据")
                self.send_json_response(self.get_mock_projects_stats())
                return
            
            projects_with_stats = []
            for project in projects:
                project_id = project.get('id')
                issues = gitlab_client.get_all_project_issues(project_id)
                
                # 统计Bug数据
                total_bugs = len(issues)
                high_priority = sum(1 for i in issues if i.get('labels', '').lower().find('bug') != -1 and 
                                   i.get('labels', '').lower().find('critical') != -1)
                medium_priority = sum(1 for i in issues if i.get('labels', '').lower().find('bug') != -1 and 
                                    i.get('labels', '').lower().find('critical') == -1)
                low_priority = total_bugs - high_priority - medium_priority
                
                open_bugs = sum(1 for i in issues if i.get('state') == 'opened')
                closed_bugs = sum(1 for i in issues if i.get('state') == 'closed')
                
                # 保存项目信息到数据库
                db_project_id = db_manager.upsert_project(project)
                
                # 保存统计快照到数据库
                stats = {
                    'total': total_bugs,
                    'high': high_priority,
                    'medium': medium_priority,
                    'low': low_priority,
                    'open': open_bugs,
                    'closed': closed_bugs
                }
                
                # 格式化Bug数据
                bug_list = []
                for issue in issues[:20]:  # 限制返回数量
                    priority = 'high' if 'critical' in issue.get('labels', '').lower() else \
                              'medium' if 'bug' in issue.get('labels', '').lower() else 'low'
                    bug_data = {
                        'id': issue.get('id'),
                        'title': issue.get('title'),
                        'priority': priority,
                        'status': 'open' if issue.get('state') == 'opened' else 'closed',
                        'created_at': issue.get('created_at'),
                        'updated_at': issue.get('updated_at'),
                        'web_url': issue.get('web_url'),
                        'labels': issue.get('labels', '').split(',') if issue.get('labels') else []
                    }
                    bug_list.append(bug_data)
                    
                    # 保存Bug详情到数据库
                    if db_project_id:
                        db_manager.upsert_bug(db_project_id, bug_data)
                
                # 保存快照
                if db_project_id:
                    db_manager.save_bug_snapshot(db_project_id, stats, bug_list)
                
                projects_with_stats.append({
                    'id': project_id,
                    'name': project.get('name'),
                    'name_with_namespace': project.get('name_with_namespace'),
                    'bugs': bug_list,
                    'stats': stats
                })
            
            if not projects_with_stats:
                logger.warning("[GitLab API不可用，使用模拟数据] 未获取到项目统计数据")
                self.send_json_response(self.get_mock_projects_stats())
                return
            
            # 检查并发送邮件告警
            EmailNotifier.check_and_notify(projects_with_stats)
            
            self.send_json_response({'projects': projects_with_stats})
            
        except GitLabAPIError as e:
            logger.warning(f"[GitLab API不可用，使用模拟数据] {str(e)}")
            self.send_json_response(self.get_mock_projects_stats())
        except Exception as e:
            logger.error(f"[获取项目统计错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_project_issues(self, project_id: int, params: Dict) -> None:
        """处理获取项目Issues请求"""
        try:
            state = params.get('state')
            labels = params.get('labels')
            
            issues = gitlab_client.get_issues(project_id, state, labels)
            
            formatted_issues = []
            for issue in issues:
                priority = 'high' if 'critical' in issue.get('labels', '').lower() else \
                          'medium' if 'bug' in issue.get('labels', '').lower() else 'low'
                formatted_issues.append({
                    'id': issue.get('id'),
                    'iid': issue.get('iid'),
                    'title': issue.get('title'),
                    'description': issue.get('description'),
                    'priority': priority,
                    'status': 'open' if issue.get('state') == 'opened' else 'closed',
                    'created_at': issue.get('created_at'),
                    'updated_at': issue.get('updated_at'),
                    'web_url': issue.get('web_url'),
                    'labels': issue.get('labels', '').split(',') if issue.get('labels') else []
                })
            
            self.send_json_response({'issues': formatted_issues})
            
        except Exception as e:
            logger.error(f"[获取项目Issues错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_project_trends(self, gitlab_project_id: int, params: Dict) -> None:
        """处理获取项目趋势请求"""
        try:
            days = int(params.get('days', 30))
            
            # 从数据库获取项目ID
            db_project = db_manager.get_project_by_gitlab_id(gitlab_project_id)
            if not db_project:
                self.send_json_response({'error': '项目未找到'}, 404)
                return
            
            # 获取趋势数据
            trends = db_manager.get_project_trends(db_project['id'], days)
            
            self.send_json_response({
                'project_id': gitlab_project_id,
                'project_name': db_project['name'],
                'trends': trends
            })
            
        except Exception as e:
            logger.error(f"[获取项目趋势错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_db_projects(self) -> None:
        """处理获取数据库项目列表请求"""
        try:
            projects = db_manager.get_all_projects()
            self.send_json_response({'projects': projects})
            
        except Exception as e:
            logger.error(f"[获取数据库项目错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_db_project_bugs(self, gitlab_project_id: int, params: Dict) -> None:
        """处理获取数据库项目Bug列表请求"""
        try:
            # 从数据库获取项目ID
            db_project = db_manager.get_project_by_gitlab_id(gitlab_project_id)
            if not db_project:
                self.send_json_response({'error': '项目未找到'}, 404)
                return
            
            status = params.get('status')
            priority = params.get('priority')
            
            bugs = db_manager.get_project_bugs(db_project['id'], status, priority)
            
            self.send_json_response({
                'project_id': gitlab_project_id,
                'project_name': db_project['name'],
                'bugs': bugs
            })
            
        except Exception as e:
            logger.error(f"[获取数据库项目Bug错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_register(self) -> None:
        """处理用户注册请求"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            role = data.get('role', 'viewer')
            
            if not username or not password:
                self.send_json_response({'error': '用户名和密码不能为空'}, 400)
                return
            
            result = auth_manager.register_user(username, password, email, role)
            
            if result['success']:
                self.send_json_response(result, 201)
            else:
                self.send_json_response(result, 400)
                
        except Exception as e:
            logger.error(f"[用户注册错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_login(self) -> None:
        """处理用户登录请求"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                self.send_json_response({'error': '用户名和密码不能为空'}, 400)
                return
            
            result = auth_manager.login_user(username, password)
            
            if result['success']:
                self.send_json_response(result)
            else:
                self.send_json_response(result, 401)
                
        except Exception as e:
            logger.error(f"[用户登录错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_logout(self) -> None:
        """处理用户登出请求"""
        try:
            auth_header = self.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                self.send_json_response({'error': '未提供认证令牌'}, 401)
                return
            
            session_token = auth_header[7:]
            result = auth_manager.logout_user(session_token)
            
            self.send_json_response(result)
            
        except Exception as e:
            logger.error(f"[用户登出错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_current_user(self) -> None:
        """处理获取当前用户信息请求"""
        try:
            auth_header = self.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                self.send_json_response({'error': '未提供认证令牌'}, 401)
                return
            
            session_token = auth_header[7:]
            user_info = auth_manager.verify_session(session_token)
            
            if not user_info:
                self.send_json_response({'error': '无效或过期的令牌'}, 401)
                return
            
            self.send_json_response({'user': user_info})
            
        except Exception as e:
            logger.error(f"[获取用户信息错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_list_users(self) -> None:
        """处理列出用户请求"""
        try:
            auth_header = self.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                self.send_json_response({'error': '未提供认证令牌'}, 401)
                return
            
            session_token = auth_header[7:]
            user_info = auth_manager.verify_session(session_token)
            
            if not user_info:
                self.send_json_response({'error': '无效或过期的令牌'}, 401)
                return
            
            result = auth_manager.list_users(user_info['role'])
            
            if result['success']:
                self.send_json_response(result)
            else:
                self.send_json_response(result, 403)
            
        except Exception as e:
            logger.error(f"[列出用户错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_update_user_role(self, user_id: int) -> None:
        """处理更新用户角色请求"""
        try:
            auth_header = self.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                self.send_json_response({'error': '未提供认证令牌'}, 401)
                return
            
            session_token = auth_header[7:]
            user_info = auth_manager.verify_session(session_token)
            
            if not user_info:
                self.send_json_response({'error': '无效或过期的令牌'}, 401)
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            new_role = data.get('role')
            
            if not new_role:
                self.send_json_response({'error': '角色不能为空'}, 400)
                return
            
            result = auth_manager.update_user_role(user_id, new_role, user_info['role'])
            
            if result['success']:
                self.send_json_response(result)
            else:
                self.send_json_response(result, 403)
            
        except Exception as e:
            logger.error(f"[更新用户角色错误] {str(e)}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_static_file(self):
        """处理静态文件请求"""
        static_dir = 'public' if os.path.exists('public') else '.'
        
        path = self.path.split('?')[0]
        
        if path == '/':
            path = '/index.html'
        
        file_path = os.path.join(static_dir, path[1:])
        
        if not (os.path.exists(file_path) and os.path.isfile(file_path)) and static_dir == 'public':
            file_path = os.path.join('.', path[1:])
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                content_type = self.guess_type(file_path)
                
                with open(file_path, 'rb') as file:
                    content = file.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                
                logger.info(f"[静态文件] 成功发送: {file_path}")
                
            except Exception as e:
                logger.error(f"[静态文件错误] {str(e)}")
                self.send_error(500, "Internal server error")
        else:
            logger.warning(f"[静态文件] 文件不存在: {file_path}")
            self.send_error(404, "File not found")
    
    def guess_type(self, path: str) -> str:
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
    
    def get_mock_projects_stats(self) -> Dict[str, Any]:
        """获取模拟项目统计数据"""
        return {
            'projects': [
                {
                    'id': 1,
                    'name': 'Web应用项目',
                    'name_with_namespace': 'dev-team/web-app',
                    'bugs': [
                        {'id': 1, 'title': '登录页面响应缓慢', 'priority': 'high', 'status': 'open', 'created_at': '2026-01-20T10:00:00Z'},
                        {'id': 2, 'title': '用户头像上传失败', 'priority': 'high', 'status': 'open', 'created_at': '2026-01-21T10:00:00Z'},
                        {'id': 3, 'title': '数据表格排序功能异常', 'priority': 'medium', 'status': 'open', 'created_at': '2026-01-21T11:00:00Z'},
                        {'id': 4, 'title': '导航菜单样式错误', 'priority': 'medium', 'status': 'closed', 'created_at': '2026-01-19T10:00:00Z'},
                        {'id': 5, 'title': '按钮文字显示不全', 'priority': 'low', 'status': 'open', 'created_at': '2026-01-22T10:00:00Z'}
                    ],
                    'stats': {
                        'total': 5,
                        'high': 2,
                        'medium': 2,
                        'low': 1,
                        'open': 4,
                        'closed': 1
                    }
                },
                {
                    'id': 2,
                    'name': '移动应用项目',
                    'name_with_namespace': 'mobile-team/mobile-app',
                    'bugs': [
                        {'id': 6, 'title': '应用启动崩溃', 'priority': 'high', 'status': 'open', 'created_at': '2026-01-20T10:00:00Z'},
                        {'id': 7, 'title': '推送通知不及时', 'priority': 'medium', 'status': 'open', 'created_at': '2026-01-21T10:00:00Z'},
                        {'id': 8, 'title': '电池消耗过快', 'priority': 'medium', 'status': 'open', 'created_at': '2026-01-21T11:00:00Z'},
                        {'id': 9, 'title': '界面文字重叠', 'priority': 'low', 'status': 'closed', 'created_at': '2026-01-19T10:00:00Z'},
                        {'id': 10, 'title': '图标显示模糊', 'priority': 'low', 'status': 'open', 'created_at': '2026-01-22T10:00:00Z'}
                    ],
                    'stats': {
                        'total': 5,
                        'high': 1,
                        'medium': 2,
                        'low': 2,
                        'open': 4,
                        'closed': 1
                    }
                },
                {
                    'id': 3,
                    'name': '后端服务项目',
                    'name_with_namespace': 'backend-team/api-service',
                    'bugs': [
                        {'id': 11, 'title': 'API响应超时', 'priority': 'high', 'status': 'open', 'created_at': '2026-01-20T10:00:00Z'},
                        {'id': 12, 'title': '数据库连接池耗尽', 'priority': 'high', 'status': 'closed', 'created_at': '2026-01-18T10:00:00Z'},
                        {'id': 13, 'title': '日志文件过大', 'priority': 'medium', 'status': 'open', 'created_at': '2026-01-21T10:00:00Z'},
                        {'id': 14, 'title': '缓存失效问题', 'priority': 'medium', 'status': 'open', 'created_at': '2026-01-21T11:00:00Z'},
                        {'id': 15, 'title': '配置文件格式错误', 'priority': 'low', 'status': 'closed', 'created_at': '2026-01-19T10:00:00Z'}
                    ],
                    'stats': {
                        'total': 5,
                        'high': 2,
                        'medium': 2,
                        'low': 1,
                        'open': 3,
                        'closed': 2
                    }
                }
            ]
        }

def main():
    """主函数"""
    if not os.path.exists('public'):
        logger.warning("public目录不存在，将使用当前目录作为静态文件目录")
    
    logger.info("=" * 60)
    logger.info("Bug统计系统服务器启动")
    logger.info("=" * 60)
    
    if SSL_ENABLED:
        if not os.path.exists(SSL_CERT_FILE) or not os.path.exists(SSL_KEY_FILE):
            logger.warning(f"SSL证书文件不存在: {SSL_CERT_FILE} 或 {SSL_KEY_FILE}")
            logger.warning("将使用HTTP模式启动服务器")
            SSL_ENABLED = False
        else:
            logger.info(f"SSL证书: {SSL_CERT_FILE}")
            logger.info(f"SSL密钥: {SSL_KEY_FILE}")
    
    protocol = "HTTPS" if SSL_ENABLED else "HTTP"
    logger.info(f"监听地址: {protocol}://localhost:{PORT}")
    logger.info(f"静态文件目录: {'public' if os.path.exists('public') else '当前目录'}")
    logger.info(f"GitLab API代理: {BASE_URL}")
    logger.info(f"缓存状态: {'启用' if CACHE_ENABLED else '禁用'}")
    logger.info("按 Ctrl+C 停止服务器")
    logger.info("=" * 60)
    
    try:
        if SSL_ENABLED:
            httpd = socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler)
            httpd.socket = ssl.wrap_socket(
                httpd.socket,
                server_side=True,
                certfile=SSL_CERT_FILE,
                keyfile=SSL_KEY_FILE,
                ssl_version=ssl.PROTOCOL_TLS
            )
        else:
            httpd = socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler)
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}")

if __name__ == "__main__":
    main()
