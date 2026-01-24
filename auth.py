#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证和权限控制模块
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from database import db_manager

logger = logging.getLogger(__name__)

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.session_duration_hours = 24
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.hash_password(password) == hashed_password
    
    def generate_session_token(self) -> str:
        """生成会话令牌"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username: str, password: str, 
                     email: Optional[str] = None, role: str = 'viewer') -> Dict:
        """注册用户"""
        try:
            # 检查用户名是否已存在
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                if cursor.fetchone():
                    return {'success': False, 'message': '用户名已存在'}
                
                # 创建用户
                password_hash = self.hash_password(password)
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, email, role))
                
                user_id = cursor.lastrowid
                logger.info(f"[认证] 用户注册成功: {username} (ID: {user_id})")
                
                return {
                    'success': True,
                    'message': '注册成功',
                    'user_id': user_id
                }
                
        except Exception as e:
            logger.error(f"[认证] 用户注册失败: {str(e)}")
            return {'success': False, 'message': f'注册失败: {str(e)}'}
    
    def login_user(self, username: str, password: str) -> Dict:
        """用户登录"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, password_hash, email, role 
                    FROM users WHERE username = ?
                ''', (username,))
                
                user = cursor.fetchone()
                
                if not user:
                    return {'success': False, 'message': '用户名或密码错误'}
                
                user_dict = dict(user)
                
                # 验证密码
                if not self.verify_password(password, user_dict['password_hash']):
                    return {'success': False, 'message': '用户名或密码错误'}
                
                # 生成会话令牌
                session_token = self.generate_session_token()
                expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)
                
                # 保存会话
                cursor.execute('''
                    INSERT INTO sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_dict['id'], session_token, expires_at.isoformat()))
                
                # 更新最后登录时间
                cursor.execute('''
                    UPDATE users SET last_login = ? WHERE id = ?
                ''', (datetime.now().isoformat(), user_dict['id']))
                
                logger.info(f"[认证] 用户登录成功: {username}")
                
                return {
                    'success': True,
                    'message': '登录成功',
                    'user': {
                        'id': user_dict['id'],
                        'username': user_dict['username'],
                        'email': user_dict['email'],
                        'role': user_dict['role']
                    },
                    'token': session_token,
                    'expires_at': expires_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"[认证] 用户登录失败: {str(e)}")
            return {'success': False, 'message': f'登录失败: {str(e)}'}
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """验证会话令牌"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.id, s.user_id, s.expires_at, u.username, u.email, u.role
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.expires_at > datetime('now')
                ''', (session_token,))
                
                session = cursor.fetchone()
                
                if not session:
                    return None
                
                session_dict = dict(session)
                
                # 返回用户信息
                return {
                    'user_id': session_dict['user_id'],
                    'username': session_dict['username'],
                    'email': session_dict['email'],
                    'role': session_dict['role'],
                    'expires_at': session_dict['expires_at']
                }
                
        except Exception as e:
            logger.error(f"[认证] 会话验证失败: {str(e)}")
            return None
    
    def logout_user(self, session_token: str) -> Dict:
        """用户登出"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM sessions WHERE session_token = ?
                ''', (session_token,))
                
                deleted_count = cursor.rowcount
                logger.info(f"[认证] 用户登出，删除会话: {deleted_count}")
                
                return {
                    'success': True,
                    'message': '登出成功'
                }
                
        except Exception as e:
            logger.error(f"[认证] 用户登出失败: {str(e)}")
            return {'success': False, 'message': f'登出失败: {str(e)}'}
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM sessions WHERE expires_at < datetime('now')
                ''')
                
                deleted_count = cursor.rowcount
                logger.info(f"[认证] 清理过期会话: {deleted_count}")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"[认证] 清理过期会话失败: {str(e)}")
            return 0
    
    def check_permission(self, user_role: str, required_role: str) -> bool:
        """检查用户权限"""
        role_hierarchy = {
            'admin': 3,
            'editor': 2,
            'viewer': 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户信息"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, role, created_at, last_login
                    FROM users WHERE id = ?
                ''', (user_id,))
                
                user = cursor.fetchone()
                
                if not user:
                    return None
                
                return dict(user)
                
        except Exception as e:
            logger.error(f"[认证] 获取用户信息失败: {str(e)}")
            return None
    
    def update_user_role(self, user_id: int, new_role: str, operator_role: str) -> Dict:
        """更新用户角色"""
        try:
            # 检查操作者权限
            if not self.check_permission(operator_role, 'admin'):
                return {'success': False, 'message': '权限不足'}
            
            # 验证新角色
            valid_roles = ['viewer', 'editor', 'admin']
            if new_role not in valid_roles:
                return {'success': False, 'message': '无效的角色'}
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET role = ? WHERE id = ?
                ''', (new_role, user_id))
                
                logger.info(f"[认证] 用户角色更新: 用户ID {user_id} -> {new_role}")
                
                return {
                    'success': True,
                    'message': '角色更新成功'
                }
                
        except Exception as e:
            logger.error(f"[认证] 更新用户角色失败: {str(e)}")
            return {'success': False, 'message': f'更新失败: {str(e)}'}
    
    def list_users(self, operator_role: str) -> Dict:
        """列出所有用户"""
        try:
            # 检查权限
            if not self.check_permission(operator_role, 'editor'):
                return {'success': False, 'message': '权限不足'}
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, role, created_at, last_login
                    FROM users
                    ORDER BY created_at DESC
                ''')
                
                users = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'success': True,
                    'users': users
                }
                
        except Exception as e:
            logger.error(f"[认证] 列出用户失败: {str(e)}")
            return {'success': False, 'message': f'获取用户列表失败: {str(e)}'}

# 初始化认证管理器
auth_manager = AuthManager()

def require_auth(required_role: str = 'viewer'):
    """认证装饰器"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # 从请求头获取token
            auth_header = self.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                self.send_json_response({'error': '未提供认证令牌'}, 401)
                return
            
            session_token = auth_header[7:]
            
            # 验证会话
            user_info = auth_manager.verify_session(session_token)
            
            if not user_info:
                self.send_json_response({'error': '无效或过期的令牌'}, 401)
                return
            
            # 检查权限
            if not auth_manager.check_permission(user_info['role'], required_role):
                self.send_json_response({'error': '权限不足'}, 403)
                return
            
            # 将用户信息添加到kwargs
            kwargs['user_info'] = user_info
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator