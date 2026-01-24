# SSL/HTTPS 配置说明

## 概述

本系统支持HTTPS加密传输，可以通过配置SSL证书来启用HTTPS服务。

## 生成自签名SSL证书

### 使用OpenSSL生成自签名证书

```bash
# 生成私钥
openssl genrsa -out server.key 2048

# 生成证书签名请求
openssl req -new -key server.key -out server.csr

# 生成自签名证书（有效期365天）
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

### 使用Python生成自签名证书

```bash
# 安装依赖
pip install pyopenssl

# 运行证书生成脚本
python generate_cert.py
```

## 配置HTTPS

### 1. 编辑 server.py

在 `server.py` 文件中修改以下配置：

```python
# HTTPS/SSL配置
SSL_ENABLED = True  # 设置为True启用HTTPS
SSL_CERT_FILE = 'server.crt'  # 证书文件路径
SSL_KEY_FILE = 'server.key'  # 私钥文件路径
```

### 2. 将证书文件放在项目根目录

确保 `server.crt` 和 `server.key` 文件位于项目根目录。

### 3. 重启服务器

```bash
python server.py
```

服务器将以HTTPS模式启动，监听地址为 `https://localhost:9000`

## 浏览器访问

### 访问HTTPS服务

在浏览器中访问：
```
https://localhost:9000
```

### 处理自签名证书警告

由于使用的是自签名证书，浏览器会显示安全警告。这是正常的，可以：

1. 点击"高级"或"Advanced"
2. 点击"继续访问"或"Proceed to localhost"
3. 添加安全例外

## 生产环境部署

### 使用Let's Encrypt获取免费SSL证书

```bash
# 安装certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d yourdomain.com

# 证书位置
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem -> server.crt
# /etc/letsencrypt/live/yourdomain.com/privkey.pem -> server.key
```

### 配置生产环境

```python
# HTTPS/SSL配置
SSL_ENABLED = True
SSL_CERT_FILE = '/etc/letsencrypt/live/yourdomain.com/fullchain.pem'
SSL_KEY_FILE = '/etc/letsencrypt/live/yourdomain.com/privkey.pem'
```

## 安全建议

1. **生产环境**：使用受信任的CA签名的证书（如Let's Encrypt）
2. **证书有效期**：定期更新证书，避免过期
3. **私钥保护**：确保私钥文件权限设置为只读
4. **端口配置**：HTTPS默认使用443端口，需要管理员权限

## 故障排除

### 证书文件不存在

错误信息：
```
SSL证书文件不存在: server.crt 或 server.key
```

解决方法：
- 确保证书文件存在于项目根目录
- 检查文件路径配置是否正确

### 端口被占用

错误信息：
```
[Errno 48] Address already in use
```

解决方法：
- 修改PORT配置使用其他端口
- 停止占用该端口的其他服务

### 浏览器无法连接

检查项：
- 服务器是否正常启动
- 防火墙是否阻止连接
- 浏览器是否支持HTTPS

## 生成证书脚本

创建 `generate_cert.py` 文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成自签名SSL证书"""

from OpenSSL import crypto
from datetime import datetime, timedelta

def generate_self_signed_cert():
    """生成自签名SSL证书"""
    # 创建密钥对
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # 创建证书
    cert = crypto.X509()
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1年有效期
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # 保存证书和私钥
    with open("server.crt", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open("server.key", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print("SSL证书生成成功！")
    print("证书文件: server.crt")
    print("私钥文件: server.key")

if __name__ == "__main__":
    generate_self_signed_cert()
```

运行脚本：
```bash
python generate_cert.py
```
