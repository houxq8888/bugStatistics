class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('auth_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(url, options = {}) {
        const fullUrl = this.baseURL + url;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers
            }
        };

        try {
            const response = await fetch(fullUrl, config);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.message || '请求失败');
            }

            return await response.json();
        } catch (error) {
            console.error('[API错误]', error);
            throw error;
        }
    }

    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl, { method: 'GET' });
    }

    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    async getProjects(params = {}) {
        return this.get('/api/projects', params);
    }

    async getProjectsStats() {
        return this.get('/api/projects/stats');
    }

    async getProjectIssues(projectId, params = {}) {
        return this.get(`/api/projects/${projectId}/issues`, params);
    }

    async getProjectTrends(projectId, params = {}) {
        return this.get(`/api/projects/${projectId}/trends`, params);
    }

    async getDBProjects() {
        return this.get('/api/db/projects');
    }

    async getDBProjectBugs(projectId, params = {}) {
        return this.get(`/api/db/projects/${projectId}/bugs`, params);
    }

    async login(username, password) {
        const result = await this.post('/api/auth/login', { username, password });
        if (result.success && result.token) {
            this.setToken(result.token);
        }
        return result;
    }

    async register(username, password, email, role = 'viewer') {
        return this.post('/api/auth/register', { username, password, email, role });
    }

    async logout() {
        const result = await this.post('/api/auth/logout');
        this.setToken(null);
        return result;
    }

    async getCurrentUser() {
        return this.get('/api/auth/me');
    }

    async getUsers() {
        return this.get('/api/auth/users');
    }

    async updateUserRole(userId, role) {
        return this.put(`/api/auth/users/${userId}/role`, { role });
    }

    async clearCache() {
        return this.post('/api/cache/clear');
    }

    async healthCheck() {
        return this.get('/api/health');
    }
}

const apiClient = new APIClient();