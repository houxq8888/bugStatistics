// Cloudflare Pages Functions - GitLab API Proxy
export async function onRequest(context) {
    // 提取请求方法，URL等信息
    const { request,env } = context;
    const { pathname, search } = new URL(request.url);
    
    // 只处理/api/v4/开头的请求
    if (!pathname.startsWith('/api/v4/')) {
        return new Response('Not Found', { status: 404 });
    }

    // GitLab配置
    const GITLAB_CONFIG = {
       BASE_URL: 'http://192.168.1.152:16380',
       API_TOKEN: '' // GitLab API令牌，根据实际情况填写
    }

    // 构建目标URL(去年/api/v4前缀)
    const targetPath=pathname.replace('/api/v4','');
    const targetUrl=`${GITLAB_CONFIG.BASE_URL}/api/v4/${targetPath}${search}`;

    console.log(`[API代理] 转发请求: ${request.url} -> ${targetUrl}`);

    //构建请求头
    const headers = new Headers(request.headers);
    headers.set('Host', new URL(GITLAB_CONFIG.BASE_URL).host);
    headers.delete('CF-Connecting-IP');
    headers.delete('CF-IPCountry');

    // 添加GitLab API令牌
    if (GITLAB_CONFIG.API_TOKEN) {
        headers.set('Authorization', `Bearer ${GITLAB_CONFIG.API_TOKEN}`);
    }

    try {
      // 转发请求到Gitlab API
      const response = await fetch(targetUrl,{
        method: request.method,
        header: headers,
        body: request.body
      });

      console.log(`[API代理] Gitlab响应状态: ${response.status} ${response.statusText}`);

      // 构建响应头
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set('Access-Control-Allow-Origin', '*');
      responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

      // 返回响应
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });
    } catch (error){
      console.error(`[API代理] 转发请求失败: ${error.message}`);
      return new Response(`Proxy error: ${error.message}`, { status: 500 });
    }
}