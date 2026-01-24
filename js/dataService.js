class DataService {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5分钟
    }

    getCacheKey(method, ...args) {
        return `${method}_${JSON.stringify(args)}`;
    }

    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    getCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        if (Date.now() - cached.timestamp > this.cacheTimeout) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    clearCache() {
        this.cache.clear();
    }

    async getProjects(useCache = true) {
        const cacheKey = this.getCacheKey('getProjects');
        
        if (useCache) {
            const cached = this.getCache(cacheKey);
            if (cached) return cached;
        }

        const result = await this.apiClient.getProjects();
        
        if (useCache) {
            this.setCache(cacheKey, result);
        }

        return result;
    }

    async getProjectsStats(useCache = true) {
        const cacheKey = this.getCacheKey('getProjectsStats');
        
        if (useCache) {
            const cached = this.getCache(cacheKey);
            if (cached) return cached;
        }

        try {
            const result = await this.apiClient.getProjectsStats();
            
            if (useCache) {
                this.setCache(cacheKey, result);
            }
            
            return result;
        } catch (error) {
            console.warn('[数据服务] API请求失败，使用模拟数据:', error);
            return this.getMockProjectsStats();
        }
    }

    async getProjectIssues(projectId, params = {}, useCache = true) {
        const cacheKey = this.getCacheKey('getProjectIssues', projectId, params);
        
        if (useCache) {
            const cached = this.getCache(cacheKey);
            if (cached) return cached;
        }

        const result = await this.apiClient.getProjectIssues(projectId, params);
        
        if (useCache) {
            this.setCache(cacheKey, result);
        }

        return result;
    }

    async getProjectTrends(projectId, days = 30, useCache = true) {
        const cacheKey = this.getCacheKey('getProjectTrends', projectId, days);
        
        if (useCache) {
            const cached = this.getCache(cacheKey);
            if (cached) return cached;
        }

        const result = await this.apiClient.getProjectTrends(projectId, { days });
        
        if (useCache) {
            this.setCache(cacheKey, result);
        }

        return result;
    }

    async getDBProjects(useCache = true) {
        const cacheKey = this.getCacheKey('getDBProjects');
        
        if (useCache) {
            const cached = this.getCache(cacheKey);
            if (cached) return cached;
        }

        const result = await this.apiClient.getDBProjects();
        
        if (useCache) {
            this.setCache(cacheKey, result);
        }

        return result;
    }

    async getDBProjectBugs(projectId, params = {}, useCache = true) {
        const cacheKey = this.getCacheKey('getDBProjectBugs', projectId, params);
        
        if (useCache) {
            const cached = this.getCache(cacheKey);
            if (cached) return cached;
        }

        const result = await this.apiClient.getDBProjectBugs(projectId, params);
        
        if (useCache) {
            this.setCache(cacheKey, result);
        }

        return result;
    }

    async login(username, password) {
        this.clearCache();
        return await this.apiClient.login(username, password);
    }

    async logout() {
        this.clearCache();
        return await this.apiClient.logout();
    }

    async getCurrentUser() {
        return await this.apiClient.getCurrentUser();
    }

    async getUsers() {
        return await this.apiClient.getUsers();
    }

    async updateUserRole(userId, role) {
        return await this.apiClient.updateUserRole(userId, role);
    }

    async clearServerCache() {
        this.clearCache();
        return await this.apiClient.clearCache();
    }

    async healthCheck() {
        return await this.apiClient.healthCheck();
    }

    calculateBugStats(bugs) {
        const stats = {
            total: bugs.length,
            high: 0,
            medium: 0,
            low: 0,
            open: 0,
            closed: 0
        };

        bugs.forEach(bug => {
            if (bug.priority === 'high') stats.high++;
            else if (bug.priority === 'medium') stats.medium++;
            else if (bug.priority === 'low') stats.low++;

            if (bug.status === 'open') stats.open++;
            else if (bug.status === 'closed') stats.closed++;
        });

        return stats;
    }

    formatTrendData(trends) {
        return {
            dates: trends.dates || [],
            datasets: [
                {
                    label: '总数',
                    data: trends.total || [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)'
                },
                {
                    label: '严重',
                    data: trends.high || [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)'
                },
                {
                    label: '中等',
                    data: trends.medium || [],
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)'
                },
                {
                    label: '轻微',
                    data: trends.low || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)'
                }
            ]
        };
    }

    filterBugs(bugs, filters = {}) {
        return bugs.filter(bug => {
            if (filters.status && bug.status !== filters.status) return false;
            if (filters.priority && bug.priority !== filters.priority) return false;
            if (filters.search && !bug.title.toLowerCase().includes(filters.search.toLowerCase())) return false;
            return true;
        });
    }

    sortBugs(bugs, sortBy = 'created_at', sortOrder = 'desc') {
        return [...bugs].sort((a, b) => {
            let comparison = 0;
            if (a[sortBy] < b[sortBy]) comparison = -1;
            if (a[sortBy] > b[sortBy]) comparison = 1;
            return sortOrder === 'asc' ? comparison : -comparison;
        });
    }

    getMockProjectsStats() {
        return {
            projects: [
                {
                    id: 1,
                    name: 'Web应用项目',
                    name_with_namespace: 'dev-team/web-app',
                    bugs: [
                        { id: 1, title: '登录页面响应缓慢', priority: 'high', status: 'open', created_at: '2026-01-20T10:00:00Z' },
                        { id: 2, title: '用户头像上传失败', priority: 'high', status: 'open', created_at: '2026-01-21T10:00:00Z' },
                        { id: 3, title: '数据表格排序功能异常', priority: 'medium', status: 'open', created_at: '2026-01-21T11:00:00Z' },
                        { id: 4, title: '导航菜单样式错误', priority: 'medium', status: 'closed', created_at: '2026-01-19T10:00:00Z' },
                        { id: 5, title: '按钮文字显示不全', priority: 'low', status: 'open', created_at: '2026-01-22T10:00:00Z' }
                    ],
                    stats: {
                        total: 5,
                        high: 2,
                        medium: 2,
                        low: 1,
                        open: 4,
                        closed: 1
                    }
                },
                {
                    id: 2,
                    name: '移动应用项目',
                    name_with_namespace: 'mobile-team/mobile-app',
                    bugs: [
                        { id: 6, title: '应用启动崩溃', priority: 'high', status: 'open', created_at: '2026-01-20T10:00:00Z' },
                        { id: 7, title: '推送通知不及时', priority: 'medium', status: 'open', created_at: '2026-01-21T10:00:00Z' },
                        { id: 8, title: '电池消耗过快', priority: 'medium', status: 'open', created_at: '2026-01-21T11:00:00Z' },
                        { id: 9, title: '界面文字重叠', priority: 'low', status: 'closed', created_at: '2026-01-19T10:00:00Z' },
                        { id: 10, title: '图标显示模糊', priority: 'low', status: 'open', created_at: '2026-01-22T10:00:00Z' }
                    ],
                    stats: {
                        total: 5,
                        high: 1,
                        medium: 2,
                        low: 2,
                        open: 4,
                        closed: 1
                    }
                },
                {
                    id: 3,
                    name: '后端服务项目',
                    name_with_namespace: 'backend-team/api-service',
                    bugs: [
                        { id: 11, title: 'API响应超时', priority: 'high', status: 'open', created_at: '2026-01-20T10:00:00Z' },
                        { id: 12, title: '数据库连接池耗尽', priority: 'high', status: 'closed', created_at: '2026-01-18T10:00:00Z' },
                        { id: 13, title: '日志文件过大', priority: 'medium', status: 'open', created_at: '2026-01-21T10:00:00Z' },
                        { id: 14, title: '缓存失效问题', priority: 'medium', status: 'open', created_at: '2026-01-21T11:00:00Z' },
                        { id: 15, title: '配置文件格式错误', priority: 'low', status: 'closed', created_at: '2026-01-19T10:00:00Z' }
                    ],
                    stats: {
                        total: 5,
                        high: 2,
                        medium: 2,
                        low: 1,
                        open: 3,
                        closed: 2
                    }
                }
            ]
        };
    }
}

const dataService = new DataService(apiClient);