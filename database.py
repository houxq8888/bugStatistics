#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块 - 使用SQLite存储历史数据
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = 'bug_stats.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"[数据库错误] {str(e)}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建项目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    gitlab_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_with_namespace TEXT,
                    description TEXT,
                    web_url TEXT,
                    created_at TEXT,
                    last_activity_at TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建Bug统计快照表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bug_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    snapshot_time TEXT NOT NULL,
                    total_bugs INTEGER DEFAULT 0,
                    high_priority INTEGER DEFAULT 0,
                    medium_priority INTEGER DEFAULT 0,
                    low_priority INTEGER DEFAULT 0,
                    open_bugs INTEGER DEFAULT 0,
                    closed_bugs INTEGER DEFAULT 0,
                    raw_data TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建Bug详情表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bug_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gitlab_bug_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    priority TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    web_url TEXT,
                    labels TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE(gitlab_bug_id, project_id)
                )
            ''')
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'viewer',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            ''')
            
            # 创建会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bug_snapshots_project_time ON bug_snapshots(project_id, snapshot_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bug_details_project ON bug_details(project_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
            
            logger.info("[数据库] 数据库表结构初始化完成")
    
    def upsert_project(self, project_data: Dict[str, Any]) -> int:
        """插入或更新项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO projects 
                (gitlab_id, name, name_with_namespace, description, web_url, created_at, last_activity_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                project_data.get('id'),
                project_data.get('name'),
                project_data.get('name_with_namespace'),
                project_data.get('description'),
                project_data.get('web_url'),
                project_data.get('created_at'),
                project_data.get('last_activity_at')
            ))
            
            # 获取项目ID
            cursor.execute('SELECT id FROM projects WHERE gitlab_id = ?', (project_data.get('id'),))
            row = cursor.fetchone()
            project_id = row['id'] if row else None
            
            logger.info(f"[数据库] 项目更新: {project_data.get('name')} (ID: {project_id})")
            return project_id
    
    def save_bug_snapshot(self, project_id: int, stats: Dict[str, Any], 
                          raw_data: Optional[List[Dict]] = None) -> int:
        """保存Bug统计快照"""
        snapshot_time = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bug_snapshots 
                (project_id, snapshot_time, total_bugs, high_priority, medium_priority, 
                 low_priority, open_bugs, closed_bugs, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_id,
                snapshot_time,
                stats.get('total', 0),
                stats.get('high', 0),
                stats.get('medium', 0),
                stats.get('low', 0),
                stats.get('open', 0),
                stats.get('closed', 0),
                json.dumps(raw_data) if raw_data else None
            ))
            
            snapshot_id = cursor.lastrowid
            logger.info(f"[数据库] 保存快照: 项目ID {project_id}, 时间 {snapshot_time}")
            return snapshot_id
    
    def upsert_bug(self, project_id: int, bug_data: Dict[str, Any]) -> int:
        """插入或更新Bug详情"""
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查Bug是否已存在
            cursor.execute('''
                SELECT id, first_seen FROM bug_details 
                WHERE gitlab_bug_id = ? AND project_id = ?
            ''', (bug_data.get('id'), project_id))
            row = cursor.fetchone()
            
            if row:
                # 更新现有Bug
                cursor.execute('''
                    UPDATE bug_details 
                    SET title = ?, priority = ?, status = ?, updated_at = ?, 
                        web_url = ?, labels = ?, last_seen = ?
                    WHERE id = ?
                ''', (
                    bug_data.get('title'),
                    bug_data.get('priority'),
                    bug_data.get('status'),
                    bug_data.get('updated_at'),
                    bug_data.get('web_url'),
                    json.dumps(bug_data.get('labels', [])),
                    now,
                    row['id']
                ))
                bug_id = row['id']
            else:
                # 插入新Bug
                cursor.execute('''
                    INSERT INTO bug_details 
                    (gitlab_bug_id, project_id, title, priority, status, created_at, 
                     updated_at, web_url, labels, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bug_data.get('id'),
                    project_id,
                    bug_data.get('title'),
                    bug_data.get('priority'),
                    bug_data.get('status'),
                    bug_data.get('created_at'),
                    bug_data.get('updated_at'),
                    bug_data.get('web_url'),
                    json.dumps(bug_data.get('labels', [])),
                    now,
                    now
                ))
                bug_id = cursor.lastrowid
            
            return bug_id
    
    def get_project_snapshots(self, project_id: int, days: int = 30) -> List[Dict]:
        """获取项目的Bug统计快照"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM bug_snapshots 
                WHERE project_id = ? AND snapshot_time >= datetime('now', '-' || ? || ' days')
                ORDER BY snapshot_time DESC
            ''', (project_id, days))
            
            snapshots = []
            for row in cursor.fetchall():
                snapshot = dict(row)
                if snapshot['raw_data']:
                    snapshot['raw_data'] = json.loads(snapshot['raw_data'])
                snapshots.append(snapshot)
            
            return snapshots
    
    def get_project_trends(self, project_id: int, days: int = 30) -> Dict[str, List]:
        """获取项目Bug趋势数据"""
        snapshots = self.get_project_snapshots(project_id, days)
        
        trends = {
            'dates': [],
            'total': [],
            'high': [],
            'medium': [],
            'low': [],
            'open': [],
            'closed': []
        }
        
        for snapshot in reversed(snapshots):
            trends['dates'].append(snapshot['snapshot_time'][:10])  # 只取日期部分
            trends['total'].append(snapshot['total_bugs'])
            trends['high'].append(snapshot['high_priority'])
            trends['medium'].append(snapshot['medium_priority'])
            trends['low'].append(snapshot['low_priority'])
            trends['open'].append(snapshot['open_bugs'])
            trends['closed'].append(snapshot['closed_bugs'])
        
        return trends
    
    def get_all_projects(self) -> List[Dict]:
        """获取所有项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM projects ORDER BY name')
            projects = [dict(row) for row in cursor.fetchall()]
            
            return projects
    
    def get_project_by_gitlab_id(self, gitlab_id: int) -> Optional[Dict]:
        """根据GitLab ID获取项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM projects WHERE gitlab_id = ?', (gitlab_id,))
            row = cursor.fetchone()
            
            return dict(row) if row else None
    
    def get_project_bugs(self, project_id: int, status: Optional[str] = None, 
                       priority: Optional[str] = None) -> List[Dict]:
        """获取项目的Bug列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM bug_details WHERE project_id = ?'
            params = [project_id]
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            if priority:
                query += ' AND priority = ?'
                params.append(priority)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            bugs = []
            for row in cursor.fetchall():
                bug = dict(row)
                if bug['labels']:
                    bug['labels'] = json.loads(bug['labels'])
                bugs.append(bug)
            
            return bugs
    
    def get_bug_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """获取Bug统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if project_id:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high,
                        SUM(CASE WHEN priority = 'medium' THEN 1 ELSE 0 END) as medium,
                        SUM(CASE WHEN priority = 'low' THEN 1 ELSE 0 END) as low,
                        SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                        SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed
                    FROM bug_details WHERE project_id = ?
                ''', (project_id,))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high,
                        SUM(CASE WHEN priority = 'medium' THEN 1 ELSE 0 END) as medium,
                        SUM(CASE WHEN priority = 'low' THEN 1 ELSE 0 END) as low,
                        SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                        SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed
                    FROM bug_details
                ''')
            
            row = cursor.fetchone()
            return {
                'total': row['total'] or 0,
                'high': row['high'] or 0,
                'medium': row['medium'] or 0,
                'low': row['low'] or 0,
                'open': row['open'] or 0,
                'closed': row['closed'] or 0
            }
    
    def cleanup_old_snapshots(self, days: int = 90) -> int:
        """清理旧的快照数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM bug_snapshots 
                WHERE snapshot_time < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted_count = cursor.rowcount
            logger.info(f"[数据库] 清理了 {deleted_count} 条旧快照记录")
            
            return deleted_count

# 初始化数据库管理器
db_manager = DatabaseManager()