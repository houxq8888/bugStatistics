class BugStatsApp {
    constructor() {
        this.container = document.getElementById('appContainer');
        this.currentUser = null;
        this.currentView = 'dashboard';
        this.theme = localStorage.getItem('theme') || 'light';
        this.filters = {
            status: null,
            priority: null,
            search: '',
            startDate: null,
            endDate: null
        };
    }

    async init() {
        uiRenderer.setContainer(this.container);
        
        this.currentUser = { username: '访客', role: 'viewer' };
        this.initTheme();
        this.showDashboard();

        this.setupEventListeners();
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    }

    initTheme() {
        if (this.theme === 'dark') {
            document.body.classList.add('dark-mode');
        }
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        
        if (this.theme === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        
        uiRenderer.showNotification(`已切换到${this.theme === 'dark' ? '暗黑' : '明亮'}模式`, 'success');
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModals();
            }
        });
    }

    updateTime() {
        const timeDisplay = document.getElementById('currentTime');
        if (timeDisplay) {
            const now = new Date();
            timeDisplay.textContent = now.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const username = form.username.value;
        const password = form.password.value;

        try {
            uiRenderer.showLoading('登录中...');
            const result = await dataService.login(username, password);
            
            if (result.success) {
                this.currentUser = result.user;
                uiRenderer.showNotification('登录成功', 'success');
                this.showDashboard();
            } else {
                uiRenderer.showNotification(result.message || '登录失败', 'error');
            }
        } catch (error) {
            uiRenderer.showNotification(error.message || '登录失败', 'error');
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        
        const form = event.target;
        const username = form.username.value;
        const email = form.email.value;
        const password = form.password.value;
        const confirmPassword = form.confirmPassword.value;

        if (password !== confirmPassword) {
            uiRenderer.showNotification('两次密码输入不一致', 'error');
            return;
        }

        try {
            uiRenderer.showLoading('注册中...');
            const result = await apiClient.register(username, password, email);
            
            if (result.success) {
                uiRenderer.showNotification('注册成功，请登录', 'success');
                this.showLoginForm();
            } else {
                uiRenderer.showNotification(result.message || '注册失败', 'error');
            }
        } catch (error) {
            uiRenderer.showNotification(error.message || '注册失败', 'error');
        }
    }

    async handleLogout() {
        try {
            await dataService.logout();
            this.currentUser = null;
            uiRenderer.showNotification('已登出', 'success');
            this.showLoginForm();
        } catch (error) {
            uiRenderer.showNotification(error.message || '登出失败', 'error');
        }
    }

    showLoginForm() {
        this.currentView = 'login';
        uiRenderer.renderLoginForm();
    }

    showRegisterForm() {
        this.currentView = 'register';
        uiRenderer.renderRegisterForm();
    }

    async showDashboard() {
        this.currentView = 'dashboard';
        this.renderHeader();
        
        try {
            uiRenderer.showLoading('加载数据...');
            const result = await dataService.getProjectsStats();
            
            if (result && result.projects) {
                this.allProjects = result.projects;
                uiRenderer.renderProjects(result.projects);
            } else {
                uiRenderer.showError('加载数据失败');
            }
        } catch (error) {
            uiRenderer.showError(error.message || '加载数据失败');
        }
    }

    handleProjectSearch(searchTerm) {
        if (!this.allProjects) return;
        
        const term = searchTerm.toLowerCase().trim();
        
        if (!term) {
            uiRenderer.renderProjects(this.allProjects);
            return;
        }
        
        const filteredProjects = this.allProjects.filter(project => {
            const name = project.name.toLowerCase();
            const path = (project.name_with_namespace || '').toLowerCase();
            return name.includes(term) || path.includes(term);
        });
        
        uiRenderer.renderProjects(filteredProjects);
    }

    async showProjectDetails(projectId) {
        this.currentView = 'projectDetails';
        this.renderHeader();
        
        try {
            uiRenderer.showLoading('加载Bug列表...');
            const result = await dataService.getProjectIssues(projectId, this.filters);
            
            if (result && result.issues) {
                this.allBugs = result.issues;
                uiRenderer.renderBugList(result.issues, `Bug列表`);
            } else {
                uiRenderer.showError('加载数据失败');
            }
        } catch (error) {
            uiRenderer.showError(error.message || '加载数据失败');
        }
    }

    handleBugSearch(searchTerm) {
        if (!this.allBugs) return;
        
        const term = searchTerm.toLowerCase().trim();
        
        if (!term) {
            this.updateBugList(this.allBugs, `Bug列表`);
            return;
        }
        
        const filteredBugs = this.allBugs.filter(bug => {
            const title = (bug.title || '').toLowerCase();
            const id = String(bug.id);
            const labels = (bug.labels || []).join(' ').toLowerCase();
            return title.includes(term) || id.includes(term) || labels.includes(term);
        });
        
        this.updateBugList(filteredBugs, `Bug列表 (搜索结果: ${filteredBugs.length})`);
    }

    toggleFilterPanel() {
        const panel = document.getElementById('filterPanel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }

    applyFilters() {
        if (!this.allBugs) return;

        const statusOpen = document.getElementById('filterStatusOpen')?.checked;
        const statusClosed = document.getElementById('filterStatusClosed')?.checked;
        const priorityHigh = document.getElementById('filterPriorityHigh')?.checked;
        const priorityMedium = document.getElementById('filterPriorityMedium')?.checked;
        const priorityLow = document.getElementById('filterPriorityLow')?.checked;
        const startDate = document.getElementById('filterStartDate')?.value;
        const endDate = document.getElementById('filterEndDate')?.value;

        const filteredBugs = this.allBugs.filter(bug => {
            if (!statusOpen && bug.status === 'open') return false;
            if (!statusClosed && bug.status === 'closed') return false;
            if (!priorityHigh && bug.priority === 'high') return false;
            if (!priorityMedium && bug.priority === 'medium') return false;
            if (!priorityLow && bug.priority === 'low') return false;
            
            if (startDate && bug.created_at) {
                const bugDate = new Date(bug.created_at).toISOString().split('T')[0];
                if (bugDate < startDate) return false;
            }
            
            if (endDate && bug.created_at) {
                const bugDate = new Date(bug.created_at).toISOString().split('T')[0];
                if (bugDate > endDate) return false;
            }
            
            return true;
        });

        // 只更新bug列表部分，保持筛选面板的状态不变
        this.updateBugList(filteredBugs, `Bug列表 (筛选结果: ${filteredBugs.length})`);
    }

    updateBugList(bugs, title = 'Bug列表') {
        if (!this.container) return;

        // 更新标题和统计信息
        const titleElement = document.querySelector('.bug-list-title-section h2');
        if (titleElement) {
            titleElement.textContent = title;
        }

        const statsElement = document.querySelector('.bug-list-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <span class="stat-badge total">总计: ${bugs.length}</span>
                <span class="stat-badge high">严重: ${bugs.filter(b => b.priority === 'high').length}</span>
                <span class="stat-badge medium">中等: ${bugs.filter(b => b.priority === 'medium').length}</span>
                <span class="stat-badge low">轻微: ${bugs.filter(b => b.priority === 'low').length}</span>
            `;
        }

        // 更新bug列表
        const bugListElement = document.querySelector('.bug-list');
        if (bugListElement) {
            if (bugs.length > 0) {
                bugListElement.innerHTML = bugs.map(bug => {
                    const priorityClass = bug.priority;
                    const statusClass = bug.status;
                    return `
                        <div class="bug-item ${priorityClass} ${statusClass}">
                            <div class="bug-header">
                                <span class="bug-id">#${bug.id}</span>
                                <span class="bug-priority ${priorityClass}">${uiRenderer.getPriorityLabel(bug.priority)}</span>
                                <span class="bug-status ${statusClass}">${uiRenderer.getStatusLabel(bug.status)}</span>
                            </div>
                            <h4 class="bug-title">${bug.title}</h4>
                            <div class="bug-meta">
                                <span class="bug-date">创建时间: ${uiRenderer.formatDate(bug.created_at)}</span>
                                ${bug.updated_at ? `<span class="bug-date">更新时间: ${uiRenderer.formatDate(bug.updated_at)}</span>` : ''}
                            </div>
                            ${bug.web_url ? `<a href="${bug.web_url}" target="_blank" class="bug-link">查看详情 →</a>` : ''}
                        </div>
                    `;
                }).join('');
            } else {
                bugListElement.innerHTML = '<p class="no-data">暂无数据</p>';
            }
        }
    }

    resetFilters() {
        if (!this.allBugs) return;

        document.getElementById('filterStatusOpen').checked = true;
        document.getElementById('filterStatusClosed').checked = true;
        document.getElementById('filterPriorityHigh').checked = true;
        document.getElementById('filterPriorityMedium').checked = true;
        document.getElementById('filterPriorityLow').checked = true;
        document.getElementById('filterStartDate').value = '';
        document.getElementById('filterEndDate').value = '';
        
        const searchInput = document.getElementById('bugSearch');
        if (searchInput) {
            searchInput.value = '';
        }

        this.updateBugList(this.allBugs, `Bug列表`);
    }

    async showProjectTrends(projectId) {
        this.currentView = 'projectTrends';
        this.currentProjectId = projectId;
        this.renderHeader();
        
        try {
            uiRenderer.showLoading('加载趋势数据...');
            const result = await dataService.getProjectTrends(projectId, 30);
            
            if (result && result.trends) {
                this.currentTrends = result.trends;
                uiRenderer.renderTrendChart(result.trends, `${result.project_name} - Bug趋势`);
            } else {
                uiRenderer.showError('加载数据失败');
            }
        } catch (error) {
            uiRenderer.showError(error.message || '加载数据失败');
        }
    }

    updatePrediction(days) {
        if (!this.currentTrends) return;
        
        const predictionDays = parseInt(days);
        uiRenderer.renderTrendChart(this.currentTrends, `${this.currentTrends.project_name || 'Bug趋势'}`, predictionDays);
    }

    async showProjectComparison() {
        this.currentView = 'projectComparison';
        this.renderHeader();
        
        try {
            uiRenderer.showLoading('加载项目对比数据...');
            const result = await dataService.getProjectsStats();
            
            if (result && result.projects) {
                uiRenderer.renderProjectComparison(result.projects);
            } else {
                uiRenderer.showError('加载数据失败');
            }
        } catch (error) {
            uiRenderer.showError(error.message || '加载数据失败');
        }
    }

    async exportToCSV() {
        try {
            const result = await dataService.getProjectsStats();
            
            if (!result || !result.projects) {
                uiRenderer.showNotification('没有数据可导出', 'error');
                return;
            }

            let csvContent = '项目名称,项目路径,总Bug数,严重,中等,轻微,未解决,已解决\n';
            
            result.projects.forEach(project => {
                const stats = project.stats || uiRenderer.calculateStats(project.bugs || []);
                csvContent += `"${project.name}","${project.name_with_namespace || ''}",${stats.total},${stats.high},${stats.medium},${stats.low},${stats.open},${stats.closed}\n`;
            });

            const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `bug_stats_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            uiRenderer.showNotification('CSV导出成功', 'success');
        } catch (error) {
            uiRenderer.showNotification('导出失败: ' + error.message, 'error');
        }
    }

    async exportToExcel() {
        try {
            const result = await dataService.getProjectsStats();
            
            if (!result || !result.projects) {
                uiRenderer.showNotification('没有数据可导出', 'error');
                return;
            }

            let excelContent = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">';
            excelContent += '<head><meta charset="utf-8"><style>';
            excelContent += 'table { border-collapse: collapse; }';
            excelContent += 'td, th { border: 1px solid #ddd; padding: 8px; text-align: left; }';
            excelContent += 'th { background-color: #667eea; color: white; }';
            excelContent += '</style></head><body>';
            excelContent += '<table>';
            
            excelContent += '<tr><th>项目名称</th><th>项目路径</th><th>总Bug数</th><th>严重</th><th>中等</th><th>轻微</th><th>未解决</th><th>已解决</th></tr>';
            
            result.projects.forEach(project => {
                const stats = project.stats || uiRenderer.calculateStats(project.bugs || []);
                excelContent += `<tr><td>${project.name}</td><td>${project.name_with_namespace || ''}</td><td>${stats.total}</td><td>${stats.high}</td><td>${stats.medium}</td><td>${stats.low}</td><td>${stats.open}</td><td>${stats.closed}</td></tr>`;
            });
            
            excelContent += '</table></body></html>';

            const blob = new Blob([excelContent], { type: 'application/vnd.ms-excel' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `bug_stats_${new Date().toISOString().split('T')[0]}.xls`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            uiRenderer.showNotification('Excel导出成功', 'success');
        } catch (error) {
            uiRenderer.showNotification('导出失败: ' + error.message, 'error');
        }
    }

    async showUserManagement() {
        this.currentView = 'userManagement';
        this.renderHeader();
        
        try {
            uiRenderer.showLoading('加载用户列表...');
            const result = await dataService.getUsers();
            
            if (result && result.users) {
                uiRenderer.renderUserList(result.users);
            } else {
                uiRenderer.showError('加载数据失败');
            }
        } catch (error) {
            uiRenderer.showError(error.message || '加载数据失败');
        }
    }

    renderHeader() {
        const header = document.querySelector('header');
        if (!header) return;

        header.innerHTML = `
            <div class="header-content">
                <h1>Bug统计系统</h1>
                <div class="header-actions">
                    <button class="theme-toggle" onclick="app.toggleTheme()" title="切换主题">
                        ${this.theme === 'dark' ? '☀️' : '🌙'}
                    </button>
                    <span class="user-info">${this.currentUser?.username || '访客'}</span>
                    <button class="header-button" onclick="app.showDashboard()">仪表盘</button>
                    <button class="header-button" onclick="app.showProjectComparison()">项目对比</button>
                    ${this.currentUser?.role === 'admin' ? `
                        <button class="header-button" onclick="app.showUserManagement()">用户管理</button>
                    ` : ''}
                    <button class="header-button logout" onclick="app.handleLogout()">登出</button>
                </div>
            </div>
        `;
    }

    applyFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        
        if (this.currentView === 'projectDetails') {
            const projectId = this.currentProjectId;
            this.showProjectDetails(projectId);
        }
    }

    resetFilters() {
        this.filters = {
            status: null,
            priority: null,
            search: ''
        };
        
        if (this.currentView === 'projectDetails') {
            const projectId = this.currentProjectId;
            this.showProjectDetails(projectId);
        }
    }

    async refreshData() {
        dataService.clearCache();
        
        switch (this.currentView) {
            case 'dashboard':
                await this.showDashboard();
                break;
            case 'projectDetails':
                await this.showProjectDetails(this.currentProjectId);
                break;
            case 'projectTrends':
                await this.showProjectTrends(this.currentProjectId);
                break;
            case 'projectComparison':
                await this.showProjectComparison();
                break;
            case 'userManagement':
                await this.showUserManagement();
                break;
        }
        
        uiRenderer.showNotification('数据已刷新', 'success');
    }

    async changeUserRole(userId, newRole) {
        try {
            const result = await dataService.updateUserRole(userId, newRole);
            
            if (result.success) {
                uiRenderer.showNotification('角色更新成功', 'success');
                await this.showUserManagement();
            } else {
                uiRenderer.showNotification(result.message || '更新失败', 'error');
            }
        } catch (error) {
            uiRenderer.showNotification(error.message || '更新失败', 'error');
        }
    }

    showAddUserModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>添加用户</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                <form id="addUserForm" onsubmit="app.handleAddUser(event)">
                    <div class="form-group">
                        <label for="newUsername">用户名</label>
                        <input type="text" id="newUsername" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="newEmail">邮箱</label>
                        <input type="email" id="newEmail" name="email">
                    </div>
                    <div class="form-group">
                        <label for="newPassword">密码</label>
                        <input type="password" id="newPassword" name="password" required>
                    </div>
                    <div class="form-group">
                        <label for="newRole">角色</label>
                        <select id="newRole" name="role">
                            <option value="viewer">查看者</option>
                            <option value="editor">编辑者</option>
                            <option value="admin">管理员</option>
                        </select>
                    </div>
                    <button type="submit" class="submit-button">添加</button>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    async handleAddUser(event) {
        event.preventDefault();
        
        const form = event.target;
        const username = form.username.value;
        const email = form.email.value;
        const password = form.password.value;
        const role = form.role.value;

        try {
            const result = await apiClient.register(username, password, email, role);
            
            if (result.success) {
                uiRenderer.showNotification('用户添加成功', 'success');
                form.closest('.modal').remove();
                await this.showUserManagement();
            } else {
                uiRenderer.showNotification(result.message || '添加失败', 'error');
            }
        } catch (error) {
            uiRenderer.showNotification(error.message || '添加失败', 'error');
        }
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.remove());
    }

    async testApiConnection() {
        try {
            const result = await dataService.healthCheck();
            
            if (result && result.status === 'ok') {
                uiRenderer.showNotification('API连接正常', 'success');
                return true;
            } else {
                uiRenderer.showNotification('API连接异常', 'error');
                return false;
            }
        } catch (error) {
            uiRenderer.showNotification('API连接失败', 'error');
            return false;
        }
    }
}

const app = new BugStatsApp();

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});