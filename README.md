# Bug统计系统

## 项目简介

这是一个用于统计和展示项目Bug信息的Web应用系统。系统通过Web界面直观展示各个项目的Bug统计数据，帮助团队了解项目质量状况，优化开发流程。

## 核心功能

### 1. Bug统计展示
- **项目级统计**：支持多个项目的Bug数据展示
- **严重级别分类**：按严重级别（高、中、低）统计Bug数量
- **状态跟踪**：按状态（未解决、已解决）统计Bug
- **可视化展示**：使用进度条和卡片形式直观展示数据
- **趋势分析**：展示Bug数量随时间的变化趋势
- **饼图展示**：环形图展示Bug严重级别占比

### 2. 数据源支持
- **GitLab集成**：完整的GitLab API集成，支持获取真实Issue数据
- **数据持久化**：使用SQLite存储历史数据，支持趋势分析
- **缓存机制**：智能缓存API响应，提升性能
- **实时更新**：前端支持实时时间显示和动态数据刷新

### 3. 用户认证与权限
- **用户注册/登录**：完整的用户认证系统
- **角色权限**：支持查看者、编辑者、管理员三种角色
- **会话管理**：安全的会话令牌机制
- **用户管理**：管理员可管理用户和分配角色

### 4. 数据导出功能
- **CSV导出**：支持将项目统计数据导出为CSV格式
- **Excel导出**：支持将项目统计数据导出为Excel格式
- **自动命名**：文件名包含日期，便于管理
- **完整数据**：包含项目名称、路径、Bug统计等所有信息

### 5. 高级筛选与搜索
- **项目搜索**：在仪表盘页面可以按项目名称或路径搜索
- **Bug搜索**：在Bug列表页面可以按标题、ID、标签搜索
- **状态筛选**：可按"未解决"和"已解决"状态筛选Bug
- **优先级筛选**：可按"严重"、"中等"、"轻微"优先级筛选Bug
- **时间范围筛选**：可按开始日期和结束日期筛选Bug
- **实时过滤**：输入关键词后立即显示搜索结果

### 6. 趋势预测功能
- **智能预测算法**：基于历史数据使用移动平均和趋势分析预测未来Bug数量
- **可配置预测天数**：支持3天、7天、14天、30天的预测
- **可视化展示**：预测数据用虚线显示，与实际数据区分
- **实时更新**：切换预测天数时立即更新图表
- **多维度预测**：分别预测总数、严重、中等、轻微Bug

### 7. 邮件通知功能
- **自动告警**：当项目Bug数量超过阈值时自动发送邮件
- **HTML格式邮件**：美观的HTML邮件模板，包含详细信息
- **可配置参数**：支持SMTP服务器、邮件账号、阈值等配置
- **详细告警信息**：包含项目名称、当前Bug数、告警阈值、超出数量、告警时间

### 8. 界面主题与响应式
- **暗黑模式**：支持一键切换暗黑/明亮主题
- **主题保存**：主题选择会保存到本地存储，刷新后保持
- **完整适配**：所有页面和组件都已适配暗黑模式
- **响应式设计**：支持桌面、平板、手机等多种设备
- **移动端优化**：触摸操作友好，布局自适应

### 9. 安全与加密
- **HTTPS支持**：支持SSL/TLS加密传输
- **自签名证书**：支持使用自签名证书
- **生产环境支持**：支持Let's Encrypt等受信任CA证书
- **灵活配置**：可启用/禁用HTTPS

### 10. 服务架构
- **静态文件服务**：提供HTML、CSS、JavaScript等静态资源服务
- **API代理服务**：代理GitLab API请求，解决跨域问题
- **多后端支持**：
  - Python HTTP服务器（主要实现）
  - Node.js服务器（备用方案）
  - Cloudflare Pages Functions（云端部署支持）
- **模块化设计**：前后端代码模块化，易于维护和扩展

## 技术栈

- **前端**：原生HTML5、CSS3、JavaScript (ES6+)、Chart.js
- **后端**：Python 3 (http.server)、SQLite
- **部署**：支持本地部署和Cloudflare Pages云端部署

## 项目结构

```
bugStatistics/
├── index.html              # 前端主页面
├── login.html              # 登录页面
├── register.html           # 注册页面
├── server.py               # Python HTTP服务器
├── database.py             # 数据库管理模块
├── auth.py                 # 认证和权限模块
├── mock_data.json          # 模拟数据文件
├── package.json            # Node.js项目配置
├── SSL_CONFIG.md          # SSL/HTTPS配置文档
├── functions/api/[[path]].js  # Cloudflare Pages Functions
├── css/
│   └── styles.css          # 样式文件
├── js/
│   ├── apiClient.js        # API客户端模块
│   ├── dataService.js      # 数据服务模块
│   ├── uiRenderer.js       # UI渲染模块
│   └── app.js              # 应用主逻辑
├── README.md               # 项目说明文档
└── .gitignore              # Git忽略文件配置
```

## 快速开始

### 使用Python服务器启动

```bash
python server.py
```

服务器将在 http://localhost:3000 启动

### 使用Node.js服务器启动

```bash
npm install
npm start
```

## 配置说明

### GitLab API配置

在 [server.py](file:///d:/virtualMachine/github/0123/bugStatistics/server.py) 中配置GitLab连接信息：

```python
BASE_URL = 'http://localhost:16380'  # GitLab服务器地址
API_TOKEN = ''  # GitLab API令牌
```

### 端口配置

在 [server.py](file:///d:/virtualMachine/github/0123/bugStatistics/server.py) 中修改 `PORT` 变量：

```python
PORT = 3000  # 修改为所需端口
```

### 缓存配置

在 [server.py](file:///d:/virtualMachine/github/0123/bugStatistics/server.py) 中配置缓存：

```python
CACHE_ENABLED = True  # 启用/禁用缓存
CACHE_DURATION = 300  # 缓存持续时间（秒）
```

### 邮件通知配置

在 [server.py](file:///d:/virtualMachine/github/0123/bugStatistics/server.py) 中配置邮件通知：

```python
# 启用邮件通知
EMAIL_ENABLED = True

# SMTP配置
EMAIL_SMTP_SERVER = 'smtp.gmail.com'
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-app-password'
EMAIL_FROM = 'your-email@gmail.com'
EMAIL_TO = 'admin@example.com'

# 设置阈值
BUG_THRESHOLD = 100
```

### HTTPS/SSL配置

在 [server.py](file:///d:/virtualMachine/github/0123/bugStatistics/server.py) 中配置HTTPS：

```python
# 启用HTTPS
SSL_ENABLED = True
SSL_CERT_FILE = 'server.crt'
SSL_KEY_FILE = 'server.key'
```

详细的SSL配置说明请参考 [SSL_CONFIG.md](file:///d:/virtualMachine/github/0123/bugStatistics/SSL_CONFIG.md)

## 使用说明

### 首次使用

1. 启动服务器后，在浏览器中访问 http://localhost:3000
2. 点击"注册"创建账号
3. 使用注册的账号登录系统

### 主要功能

#### 仪表盘
- 查看所有项目的Bug统计概览
- 按严重级别和状态分类展示
- 实时数据刷新
- 项目搜索功能
- 饼图展示Bug严重级别占比
- 数据导出（CSV/Excel）
- 主题切换（暗黑/明亮模式）

#### 项目详情
- 查看项目的Bug列表
- 按状态、优先级筛选Bug
- 按时间范围筛选Bug
- Bug搜索功能（标题、ID、标签）
- 查看Bug详细信息

#### 趋势分析
- 查看Bug数量随时间的变化趋势
- 支持自定义时间范围
- 多维度数据对比
- 趋势预测功能（3/7/14/30天）
- 预测数据可视化展示

#### 项目对比
- 查看多个项目的Bug对比
- 表格形式展示对比数据
- 统计总Bug数量和各优先级分布

#### 用户管理（管理员）
- 查看所有用户列表
- 添加新用户
- 修改用户角色

#### 邮件通知
- 自动监控项目Bug数量
- 超过阈值时发送告警邮件
- HTML格式邮件，包含详细信息

#### 主题切换
- 一键切换暗黑/明亮主题
- 主题自动保存到本地存储
- 所有页面完整适配

#### 响应式设计
- 支持桌面、平板、手机等多种设备
- 移动端触摸操作友好
- 布局自适应屏幕尺寸

## API文档

### 认证相关

#### 用户注册
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "用户名",
  "password": "密码",
  "email": "邮箱（可选）",
  "role": "viewer|editor|admin（可选，默认viewer）"
}
```

#### 用户登录
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "用户名",
  "password": "密码"
}
```

#### 用户登出
```
POST /api/auth/logout
Authorization: Bearer <token>
```

#### 获取当前用户信息
```
GET /api/auth/me
Authorization: Bearer <token>
```

#### 列出用户
```
GET /api/auth/users
Authorization: Bearer <token>
```

#### 更新用户角色
```
PUT /api/auth/users/<user_id>/role
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "viewer|editor|admin"
}
```

### 项目相关

#### 获取项目列表
```
GET /api/projects?page=1&per_page=20&search=关键词
```

#### 获取项目统计
```
GET /api/projects/stats
```

#### 获取项目Issues
```
GET /api/projects/<project_id>/issues?state=opened&labels=bug
```

#### 获取项目趋势
```
GET /api/projects/<project_id>/trends?days=30
```

### 数据库相关

#### 获取数据库项目列表
```
GET /api/db/projects
```

#### 获取数据库项目Bug
```
GET /api/db/projects/<project_id>/bugs?status=open&priority=high
```

### 系统相关

#### 清除缓存
```
POST /api/cache/clear
```

#### 健康检查
```
GET /api/health
```

## 数据库

系统使用SQLite存储数据，主要包含以下表：

- `projects` - 项目信息
- `bug_snapshots` - Bug统计快照
- `bug_details` - Bug详细信息
- `users` - 用户信息
- `sessions` - 会话信息

数据库文件：`bug_stats.db`

## 权限说明

### 角色定义

- **查看者 (viewer)**：只能查看数据，不能修改
- **编辑者 (editor)**：可以查看和编辑数据
- **管理员 (admin)**：拥有所有权限，包括用户管理

### 权限矩阵

| 功能 | 查看者 | 编辑者 | 管理员 |
|------|--------|--------|--------|
| 查看仪表盘 | ✓ | ✓ | ✓ |
| 查看项目详情 | ✓ | ✓ | ✓ |
| 查看趋势分析 | ✓ | ✓ | ✓ |
| 用户管理 | ✗ | ✗ | ✓ |
| 修改用户角色 | ✗ | ✗ | ✓ |

## 部署选项

### 本地部署
直接运行Python或Node.js服务器

### Cloudflare Pages部署
```bash
npm run deploy
```

### Docker部署（推荐）

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "server.py"]
```

构建和运行：

```bash
docker build -t bug-stats .
docker run -p 3000:3000 -v $(pwd)/data:/app/data bug-stats
```

## 开发指南

### 前端模块说明

- **apiClient.js** - 封装所有API调用
- **dataService.js** - 数据处理和缓存管理
- **uiRenderer.js** - UI渲染和组件生成
- **app.js** - 应用主逻辑和事件处理

### 后端模块说明

- **server.py** - HTTP服务器和路由处理
- **database.py** - 数据库操作和模型定义
- **auth.py** - 用户认证和权限管理

### 添加新功能

1. 在相应的模块中添加功能代码
2. 更新API文档
3. 添加相应的UI组件
4. 更新测试用例

## 更新日志

### v3.0.0 (2026-01-24)

#### 新增功能
- **数据导出功能**：支持CSV和Excel格式导出项目统计数据
- **暗黑模式**：一键切换暗黑/明亮主题，自动保存用户偏好
- **高级筛选**：支持按状态、优先级、时间范围筛选Bug
- **搜索功能**：项目搜索和Bug搜索，支持关键词匹配
- **饼图展示**：环形图展示Bug严重级别占比
- **趋势预测**：基于历史数据预测未来Bug趋势（3/7/14/30天）
- **邮件通知**：Bug数量超过阈值时自动发送告警邮件
- **HTTPS支持**：支持SSL/TLS加密传输
- **响应式设计**：完整的移动端适配，支持多种设备

#### 改进
- UI/UX全面优化
- 性能进一步提升
- 移动端体验改进
- 安全性增强

#### 修复
- 修复筛选功能交互问题
- 修复图表渲染问题
- 修复移动端布局问题

### v2.0.0 (2026-01-24)

#### 新增功能
- 完整的GitLab API集成
- SQLite数据持久化
- 用户认证和权限系统
- 前端代码模块化重构
- Bug趋势分析功能
- 用户管理界面
- 缓存机制优化

#### 改进
- 代码架构优化
- 性能提升
- 用户体验改进
- 安全性增强

#### 修复
- 修复API代理错误处理
- 修复数据格式问题

### v1.0.0

- 初始版本发布
- 基础Bug统计功能
- 模拟数据支持

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
