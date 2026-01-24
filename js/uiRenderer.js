class UIRenderer {
    constructor() {
        this.container = null;
    }

    setContainer(container) {
        this.container = container;
    }

    createElement(tag, className = '', innerHTML = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    }

    showLoading(message = '加载中...') {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p class="loading-text">${message}</p>
            </div>
        `;
    }

    hideLoading() {
        const loadingContainer = this.container.querySelector('.loading-container');
        if (loadingContainer) {
            loadingContainer.remove();
        }
    }

    showError(message) {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <p class="error-message">${message}</p>
                <button class="retry-button" onclick="window.location.reload()">重试</button>
            </div>
        `;
    }

    renderProjects(projects) {
        if (!this.container) return;

        const projectsContainer = this.createElement('div', 'projects-container');
        
        projects.forEach((project, index) => {
            const projectCard = this.renderProjectCard(project, index);
            projectsContainer.appendChild(projectCard);
        });

        this.container.innerHTML = '';
        
        const header = this.createElement('div', 'projects-header');
        header.innerHTML = `
            <h2>项目统计</h2>
            <div class="header-actions">
                <div class="search-box">
                    <input type="text" 
                           class="search-input" 
                           placeholder="搜索项目..." 
                           id="projectSearch"
                           oninput="app.handleProjectSearch(this.value)">
                    <span class="search-icon">🔍</span>
                </div>
                <div class="export-buttons">
                    <button class="export-button" onclick="app.exportToCSV()">
                        <span class="export-icon">📄</span>
                        导出CSV
                    </button>
                    <button class="export-button" onclick="app.exportToExcel()">
                        <span class="export-icon">📊</span>
                        导出Excel
                    </button>
                </div>
            </div>
        `;
        
        this.container.appendChild(header);
        this.container.appendChild(projectsContainer);
    }

    renderProjectCard(project, index = 0) {
        const card = this.createElement('div', `project-card fade-in-up delay-${index + 1}`);
        const chartId = `pieChart-${index}`;
        
        const stats = project.stats || this.calculateStats(project.bugs || []);
        
        card.innerHTML = `
            <div class="project-header">
                <h3>${project.name}</h3>
                <p class="project-path">${project.name_with_namespace || ''}</p>
            </div>
            <div class="project-content">
                <div class="stats-section">
                    <div class="stats-grid">
                        <div class="stat-item total">
                            <div class="stat-label">总Bug数</div>
                            <div class="stat-value">${stats.total}</div>
                        </div>
                        <div class="stat-item high">
                            <div class="stat-label">严重</div>
                            <div class="stat-value">${stats.high}</div>
                        </div>
                        <div class="stat-item medium">
                            <div class="stat-label">中等</div>
                            <div class="stat-value">${stats.medium}</div>
                        </div>
                        <div class="stat-item low">
                            <div class="stat-label">轻微</div>
                            <div class="stat-value">${stats.low}</div>
                        </div>
                        <div class="stat-item open">
                            <div class="stat-label">未解决</div>
                            <div class="stat-value">${stats.open}</div>
                        </div>
                        <div class="stat-item closed">
                            <div class="stat-label">已解决</div>
                            <div class="stat-value">${stats.closed}</div>
                        </div>
                    </div>
                    <div class="progress-bars">
                        ${this.renderProgressBar('严重', stats.high, stats.total, 'high')}
                        ${this.renderProgressBar('中等', stats.medium, stats.total, 'medium')}
                        ${this.renderProgressBar('轻微', stats.low, stats.total, 'low')}
                    </div>
                </div>
                <div class="chart-section">
                    <div class="pie-chart-container">
                        <canvas id="${chartId}"></canvas>
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item high">
                            <span class="legend-color"></span>
                            <span>严重 (${stats.high})</span>
                        </div>
                        <div class="legend-item medium">
                            <span class="legend-color"></span>
                            <span>中等 (${stats.medium})</span>
                        </div>
                        <div class="legend-item low">
                            <span class="legend-color"></span>
                            <span>轻微 (${stats.low})</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        setTimeout(() => {
            this.initPieChart(chartId, stats);
        }, 100);

        return card;
    }

    renderProgressBar(label, value, total, type) {
        const percentage = total > 0 ? (value / total * 100).toFixed(1) : 0;
        
        return `
            <div class="progress-bar-container">
                <div class="progress-label">
                    <span>${label}</span>
                    <span>${value} (${percentage}%)</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${type}" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }

    renderBugList(bugs, title = 'Bug列表') {
        if (!this.container) return;

        const listContainer = this.createElement('div', 'bug-list-container');
        
        listContainer.innerHTML = `
            <div class="bug-list-header">
                <div class="bug-list-title-section">
                    <h2>${title}</h2>
                    <div class="bug-list-stats">
                        <span class="stat-badge total">总计: ${bugs.length}</span>
                        <span class="stat-badge high">严重: ${bugs.filter(b => b.priority === 'high').length}</span>
                        <span class="stat-badge medium">中等: ${bugs.filter(b => b.priority === 'medium').length}</span>
                        <span class="stat-badge low">轻微: ${bugs.filter(b => b.priority === 'low').length}</span>
                    </div>
                </div>
                <div class="bug-list-actions">
                    <div class="search-box">
                        <input type="text" 
                               class="search-input" 
                               placeholder="搜索Bug..." 
                               id="bugSearch"
                               oninput="app.handleBugSearch(this.value)">
                        <span class="search-icon">🔍</span>
                    </div>
                    <button class="filter-toggle-button" onclick="app.toggleFilterPanel()">
                        <span>筛选</span>
                        <span class="filter-icon">⚙️</span>
                    </button>
                </div>
            </div>
            <div class="filter-panel" id="filterPanel" style="display: none;">
                <div class="filter-section">
                    <h4>状态</h4>
                    <div class="filter-options">
                        <label class="filter-option">
                            <input type="checkbox" id="filterStatusOpen" onchange="app.applyFilters()" checked>
                            <span>未解决</span>
                        </label>
                        <label class="filter-option">
                            <input type="checkbox" id="filterStatusClosed" onchange="app.applyFilters()" checked>
                            <span>已解决</span>
                        </label>
                    </div>
                </div>
                <div class="filter-section">
                    <h4>优先级</h4>
                    <div class="filter-options">
                        <label class="filter-option">
                            <input type="checkbox" id="filterPriorityHigh" onchange="app.applyFilters()" checked>
                            <span>严重</span>
                        </label>
                        <label class="filter-option">
                            <input type="checkbox" id="filterPriorityMedium" onchange="app.applyFilters()" checked>
                            <span>中等</span>
                        </label>
                        <label class="filter-option">
                            <input type="checkbox" id="filterPriorityLow" onchange="app.applyFilters()" checked>
                            <span>轻微</span>
                        </label>
                    </div>
                </div>
                <div class="filter-section">
                    <h4>时间范围</h4>
                    <div class="filter-options">
                        <div class="date-filter">
                            <label>开始日期</label>
                            <input type="date" id="filterStartDate" onchange="app.applyFilters()">
                        </div>
                        <div class="date-filter">
                            <label>结束日期</label>
                            <input type="date" id="filterEndDate" onchange="app.applyFilters()">
                        </div>
                    </div>
                </div>
                <div class="filter-actions">
                    <button class="filter-reset-button" onclick="app.resetFilters()">重置筛选</button>
                </div>
            </div>
            <div class="bug-list">
                ${bugs.length > 0 ? bugs.map(bug => this.renderBugItem(bug)).join('') : '<p class="no-data">暂无数据</p>'}
            </div>
        `;

        this.container.innerHTML = '';
        this.container.appendChild(listContainer);
    }

    renderBugItem(bug) {
        const priorityClass = bug.priority;
        const statusClass = bug.status;
        
        return `
            <div class="bug-item ${priorityClass} ${statusClass}">
                <div class="bug-header">
                    <span class="bug-id">#${bug.id}</span>
                    <span class="bug-priority ${priorityClass}">${this.getPriorityLabel(bug.priority)}</span>
                    <span class="bug-status ${statusClass}">${this.getStatusLabel(bug.status)}</span>
                </div>
                <h4 class="bug-title">${bug.title}</h4>
                <div class="bug-meta">
                    <span class="bug-date">创建时间: ${this.formatDate(bug.created_at)}</span>
                    ${bug.updated_at ? `<span class="bug-date">更新时间: ${this.formatDate(bug.updated_at)}</span>` : ''}
                </div>
                ${bug.web_url ? `<a href="${bug.web_url}" target="_blank" class="bug-link">查看详情 →</a>` : ''}
            </div>
        `;
    }

    renderTrendChart(trends, title = 'Bug趋势', predictionDays = 7) {
        if (!this.container) return;

        const chartContainer = this.createElement('div', 'chart-container');
        
        chartContainer.innerHTML = `
            <div class="chart-header">
                <h2>${title}</h2>
                <div class="prediction-controls">
                    <label for="predictionDays">预测天数:</label>
                    <select id="predictionDays" onchange="app.updatePrediction(this.value)">
                        <option value="3" ${predictionDays === 3 ? 'selected' : ''}>3天</option>
                        <option value="7" ${predictionDays === 7 ? 'selected' : ''}>7天</option>
                        <option value="14" ${predictionDays === 14 ? 'selected' : ''}>14天</option>
                        <option value="30" ${predictionDays === 30 ? 'selected' : ''}>30天</option>
                    </select>
                </div>
            </div>
            <div class="chart-canvas">
                <canvas id="trendChart"></canvas>
            </div>
        `;

        this.container.innerHTML = '';
        this.container.appendChild(chartContainer);

        return this.initChart(trends, predictionDays);
    }

    initChart(trends, predictionDays = 7) {
        const ctx = document.getElementById('trendChart');
        if (!ctx) return null;

        const prediction = this.calculatePrediction(trends, predictionDays);
        const allDates = [...trends.dates, ...prediction.dates];
        const allTotal = [...trends.total, ...prediction.total];
        const allHigh = [...trends.high, ...prediction.high];
        const allMedium = [...trends.medium, ...prediction.medium];
        const allLow = [...trends.low, ...prediction.low];

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: allDates,
                datasets: [
                    {
                        label: '总数',
                        data: allTotal,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4,
                        fill: true,
                        segment: {
                            borderColor: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? 'rgba(0, 123, 255, 0.5)' : '#007bff';
                            },
                            borderDash: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? [5, 5] : [];
                            }
                        }
                    },
                    {
                        label: '严重',
                        data: allHigh,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.4,
                        fill: true,
                        segment: {
                            borderColor: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? 'rgba(220, 53, 69, 0.5)' : '#dc3545';
                            },
                            borderDash: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? [5, 5] : [];
                            }
                        }
                    },
                    {
                        label: '中等',
                        data: allMedium,
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4,
                        fill: true,
                        segment: {
                            borderColor: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? 'rgba(255, 193, 7, 0.5)' : '#ffc107';
                            },
                            borderDash: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? [5, 5] : [];
                            }
                        }
                    },
                    {
                        label: '轻微',
                        data: allLow,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true,
                        segment: {
                            borderColor: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? 'rgba(40, 167, 69, 0.5)' : '#28a745';
                            },
                            borderDash: ctx => {
                                const index = ctx.p0DataIndex;
                                return index >= trends.dates.length ? [5, 5] : [];
                            }
                        }
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const isPrediction = index >= trends.dates.length;
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}${isPrediction ? ' (预测)' : ''}: ${value}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    calculatePrediction(trends, days) {
        const total = this.predictNextValues(trends.total, days);
        const high = this.predictNextValues(trends.high, days);
        const medium = this.predictNextValues(trends.medium, days);
        const low = this.predictNextValues(trends.low, days);

        const lastDate = new Date(trends.dates[trends.dates.length - 1]);
        const dates = [];
        for (let i = 1; i <= days; i++) {
            const nextDate = new Date(lastDate);
            nextDate.setDate(nextDate.getDate() + i);
            dates.push(nextDate.toISOString().split('T')[0]);
        }

        return { dates, total, high, medium, low };
    }

    predictNextValues(data, days) {
        if (data.length < 3) {
            return Array(days).fill(data.length > 0 ? data[data.length - 1] : 0);
        }

        const predictions = [];
        const n = data.length;

        for (let i = 0; i < days; i++) {
            let sum = 0;
            let count = 0;

            for (let j = 1; j <= Math.min(3, n + i); j++) {
                const index = n - 1 + i - j;
                if (index >= 0 && index < data.length) {
                    sum += data[index];
                    count++;
                }
            }

            const avg = count > 0 ? sum / count : 0;
            const lastValue = predictions.length > 0 ? predictions[predictions.length - 1] : data[n - 1];
            
            const trend = data.length > 1 ? (data[data.length - 1] - data[data.length - 2]) / 2 : 0;
            const predictedValue = Math.max(0, Math.round(avg + trend));
            
            predictions.push(predictedValue);
        }

        return predictions;
    }

    initPieChart(chartId, stats) {
        const ctx = document.getElementById(chartId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['严重', '中等', '轻微'],
                datasets: [{
                    data: [stats.high, stats.medium, stats.low],
                    backgroundColor: [
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(40, 167, 69, 0.8)'
                    ],
                    borderColor: [
                        '#dc3545',
                        '#ffc107',
                        '#28a745'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderProjectComparison(projects) {
        if (!this.container) return;

        const comparisonContainer = this.createElement('div', 'comparison-container');
        
        const totalStats = this.calculateTotalStats(projects);
        
        comparisonContainer.innerHTML = `
            <div class="comparison-header">
                <h2>项目Bug对比</h2>
                <div class="total-stats">
                    <div class="stat-card total">
                        <div class="stat-label">总Bug数</div>
                        <div class="stat-value">${totalStats.total}</div>
                    </div>
                    <div class="stat-card high">
                        <div class="stat-label">严重</div>
                        <div class="stat-value">${totalStats.high}</div>
                    </div>
                    <div class="stat-card medium">
                        <div class="stat-label">中等</div>
                        <div class="stat-value">${totalStats.medium}</div>
                    </div>
                    <div class="stat-card low">
                        <div class="stat-label">轻微</div>
                        <div class="stat-value">${totalStats.low}</div>
                    </div>
                </div>
            </div>
            
            <div class="comparison-content">
                <div class="comparison-section">
                    <h3>项目间Bug对比（纵向）</h3>
                    <div class="comparison-chart">
                        <canvas id="comparisonChart"></canvas>
                    </div>
                </div>
                
                <div class="comparison-section">
                    <h3>项目详情对比（横向）</h3>
                    <div class="comparison-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>项目名称</th>
                                    <th>总数</th>
                                    <th>严重</th>
                                    <th>中等</th>
                                    <th>轻微</th>
                                    <th>未解决</th>
                                    <th>已解决</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${projects.map(project => {
                                    const stats = project.stats || this.calculateStats(project.bugs || []);
                                    return `
                                        <tr>
                                            <td class="project-name">${project.name}</td>
                                            <td class="stat-value total">${stats.total}</td>
                                            <td class="stat-value high">${stats.high}</td>
                                            <td class="stat-value medium">${stats.medium}</td>
                                            <td class="stat-value low">${stats.low}</td>
                                            <td class="stat-value open">${stats.open}</td>
                                            <td class="stat-value closed">${stats.closed}</td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        this.container.innerHTML = '';
        this.container.appendChild(comparisonContainer);

        this.initComparisonChart(projects);
    }

    calculateTotalStats(projects) {
        const total = {
            total: 0,
            high: 0,
            medium: 0,
            low: 0,
            open: 0,
            closed: 0
        };

        projects.forEach(project => {
            const stats = project.stats || this.calculateStats(project.bugs || []);
            total.total += stats.total;
            total.high += stats.high;
            total.medium += stats.medium;
            total.low += stats.low;
            total.open += stats.open;
            total.closed += stats.closed;
        });

        return total;
    }

    initComparisonChart(projects) {
        const ctx = document.getElementById('comparisonChart');
        if (!ctx) return;

        const projectNames = projects.map(p => p.name);
        const totalBugs = projects.map(p => (p.stats || this.calculateStats(p.bugs || [])).total);
        const highBugs = projects.map(p => (p.stats || this.calculateStats(p.bugs || [])).high);
        const mediumBugs = projects.map(p => (p.stats || this.calculateStats(p.bugs || [])).medium);
        const lowBugs = projects.map(p => (p.stats || this.calculateStats(p.bugs || [])).low);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: projectNames,
                datasets: [
                    {
                        label: '总数',
                        data: totalBugs,
                        backgroundColor: 'rgba(0, 123, 255, 0.7)',
                        borderColor: '#007bff',
                        borderWidth: 1
                    },
                    {
                        label: '严重',
                        data: highBugs,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        borderColor: '#dc3545',
                        borderWidth: 1
                    },
                    {
                        label: '中等',
                        data: mediumBugs,
                        backgroundColor: 'rgba(255, 193, 7, 0.7)',
                        borderColor: '#ffc107',
                        borderWidth: 1
                    },
                    {
                        label: '轻微',
                        data: lowBugs,
                        backgroundColor: 'rgba(40, 167, 69, 0.7)',
                        borderColor: '#28a745',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Bug数量'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '项目'
                        }
                    }
                }
            }
        });
    }

    renderUserList(users) {
        if (!this.container) return;

        const listContainer = this.createElement('div', 'user-list-container');
        
        listContainer.innerHTML = `
            <div class="user-list-header">
                <h2>用户列表</h2>
                <button class="add-user-button" onclick="app.showAddUserModal()">添加用户</button>
            </div>
            <div class="user-list">
                ${users.length > 0 ? users.map(user => this.renderUserItem(user)).join('') : '<p class="no-data">暂无用户</p>'}
            </div>
        `;

        this.container.innerHTML = '';
        this.container.appendChild(listContainer);
    }

    renderUserItem(user) {
        const roleClass = user.role;
        
        return `
            <div class="user-item">
                <div class="user-info">
                    <div class="user-avatar">
                        ${user.username.charAt(0).toUpperCase()}
                    </div>
                    <div class="user-details">
                        <h4 class="user-name">${user.username}</h4>
                        <p class="user-email">${user.email || '无邮箱'}</p>
                    </div>
                </div>
                <div class="user-actions">
                    <span class="user-role ${roleClass}">${this.getRoleLabel(user.role)}</span>
                    ${user.role !== 'admin' ? `
                        <select class="role-select" onchange="app.changeUserRole(${user.id}, this.value)">
                            <option value="viewer" ${user.role === 'viewer' ? 'selected' : ''}>查看者</option>
                            <option value="editor" ${user.role === 'editor' ? 'selected' : ''}>编辑者</option>
                            <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>管理员</option>
                        </select>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderLoginForm() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="login-container">
                <div class="login-form">
                    <h2>Bug统计系统</h2>
                    <form id="loginForm" onsubmit="app.handleLogin(event)">
                        <div class="form-group">
                            <label for="username">用户名</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="password">密码</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        <button type="submit" class="login-button">登录</button>
                    </form>
                    <p class="register-link">
                        还没有账号？<a href="#" onclick="app.showRegisterForm()">注册</a>
                    </p>
                </div>
            </div>
        `;
    }

    renderRegisterForm() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="register-container">
                <div class="register-form">
                    <h2>注册账号</h2>
                    <form id="registerForm" onsubmit="app.handleRegister(event)">
                        <div class="form-group">
                            <label for="username">用户名</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="email">邮箱</label>
                            <input type="email" id="email" name="email">
                        </div>
                        <div class="form-group">
                            <label for="password">密码</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        <div class="form-group">
                            <label for="confirmPassword">确认密码</label>
                            <input type="password" id="confirmPassword" name="confirmPassword" required>
                        </div>
                        <button type="submit" class="register-button">注册</button>
                    </form>
                    <p class="login-link">
                        已有账号？<a href="#" onclick="app.showLoginForm()">登录</a>
                    </p>
                </div>
            </div>
        `;
    }

    calculateStats(bugs) {
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

    getPriorityLabel(priority) {
        const labels = {
            high: '严重',
            medium: '中等',
            low: '轻微'
        };
        return labels[priority] || priority;
    }

    getStatusLabel(status) {
        const labels = {
            open: '未解决',
            closed: '已解决'
        };
        return labels[status] || status;
    }

    getRoleLabel(role) {
        const labels = {
            viewer: '查看者',
            editor: '编辑者',
            admin: '管理员'
        };
        return labels[role] || role;
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    }

    showNotification(message, type = 'info') {
        const notification = this.createElement('div', `notification ${type}`);
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

const uiRenderer = new UIRenderer();