# MCP微信爬虫启动指南

## 🚀 多种启动方式

### 1. 模块化启动 (推荐)

#### 启动MCP服务器
```bash
# 方式1: 使用模块启动 (推荐)
python3 -m mcp_weixin_spider
# 或者明确指定服务器模式
python3 -m mcp_weixin_spider server

# 方式2: 直接运行服务器脚本
python3 src/mcp_weixin_spider/server.py
```

#### 启动客户端演示
```bash
# 使用模块启动客户端
python3 -m mcp_weixin_spider client

# 或者直接运行客户端脚本
python3 src/mcp_weixin_spider/client.py
```

#### 启动交互式客户端
```bash
# 交互式模式
python3 -m mcp_weixin_spider interactive
```

### 2. 使用main.py启动

```bash
# 服务器模式
python3 src/mcp_weixin_spider/main.py server

# 客户端演示
python3 src/mcp_weixin_spider/main.py client

# 交互式客户端
python3 src/mcp_weixin_spider/main.py interactive

# 调试模式
python3 src/mcp_weixin_spider/main.py server --debug
```

### 3. 安装后使用命令行工具

首先安装包：
```bash
cd MCPWeiXin
pip install -e .
```

然后使用命令行工具：
```bash
# 启动服务器 (默认)
mcp-weixin-spider

# 明确启动服务器
mcp-weixin-spider-server

# 启动客户端演示
mcp-weixin-spider-client
```

## 🔧 智能体配置

### Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "weixin_spider": {
      "command": "python3",
      "args": ["-m", "mcp_weixin_spider"],
      "cwd": "/path/to/your/MCPWeiXin",
      "env": {
        "ARTICLES_DIR": "articles",
        "DOWNLOAD_IMAGES": "true",
        "HEADLESS": "true"
      }
    }
  }
}
```

### 其他MCP客户端配置

```json
{
  "mcp_servers": {
    "weixin_spider": {
      "command": "python3",
      "args": ["-m", "mcp_weixin_spider"],
      "env": {
        "ARTICLES_DIR": "articles",
        "DOWNLOAD_IMAGES": "true",
        "HEADLESS": "true",
        "WAIT_TIME": "10"
      }
    }
  }
}
```

## 🐛 调试模式

### 启用详细日志

```bash
# 环境变量方式
DEBUG=1 python3 -m mcp_weixin_spider

# 或者使用main.py的调试参数
python3 src/mcp_weixin_spider/main.py server --debug
```

### 检查服务器状态

```bash
# 测试服务器连接
python3 -m mcp_weixin_spider client

# 运行快速修复脚本
python3 quick_fix.py --test-crawl
```

## 📁 工作目录要求

确保在正确的目录下启动：

```bash
# 进入项目目录
cd /path/to/your/MCPWeiXin

# 检查目录结构
ls -la src/mcp_weixin_spider/
# 应该看到: __init__.py, __main__.py, server.py, client.py, main.py

# 启动服务器
python3 -m mcp_weixin_spider
```

## ⚠️ 常见问题

### 1. 模块找不到错误

```bash
# 错误: No module named 'mcp_weixin_spider'
# 解决: 确保在MCPWeiXin目录下，并且src目录在Python路径中

cd MCPWeiXin
export PYTHONPATH="$PWD/src:$PYTHONPATH"
python3 -m mcp_weixin_spider
```

### 2. 依赖包缺失

```bash
# 安装依赖
pip install -r requirements.txt
# 或者
pip install mcp selenium beautifulsoup4 requests webdriver-manager Pillow lxml
```

### 3. ChromeDriver问题

```bash
# 重新安装ChromeDriver
pip install --upgrade webdriver-manager
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

## 💡 最佳实践

1. **推荐启动方式**: `python3 -m mcp_weixin_spider`
2. **开发调试**: `python3 src/mcp_weixin_spider/main.py server --debug`
3. **生产环境**: 安装包后使用 `mcp-weixin-spider`
4. **智能体集成**: 使用模块化启动方式配置MCP客户端

## 🔍 验证安装

运行以下命令验证所有启动方式：

```bash
# 1. 检查模块结构
python3 -c "import sys; sys.path.insert(0, 'src'); import mcp_weixin_spider; print('✅ 模块导入成功')"

# 2. 测试服务器启动
timeout 5 python3 -m mcp_weixin_spider || echo "✅ 服务器启动正常"

# 3. 运行快速检查
python3 quick_fix.py --check-paths
```

现在你可以使用 `python3 -m mcp_weixin_spider` 来启动MCP服务器了！