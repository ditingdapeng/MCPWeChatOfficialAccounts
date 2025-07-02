# MCP微信爬虫使用指南

## 🚨 常见问题解决方案

### 问题1: "Could not find file 'weixin_articles/xxx.txt'"

**原因：** 智能体在错误的路径查找文件

**解决方案：**
1. **确认文件保存位置**：文章实际保存在 `articles/` 目录
2. **使用正确的MCP配置**：参考 `mcp_config.json`
3. **智能体配置**：确保智能体使用正确的路径映射

```bash
# 检查文章是否存在
ls -la articles/

# 查看最近爬取的文章
ls -la articles/*/
```

### 问题2: "Missing required parameter 'article_data'"

**原因：** 直接调用分析工具而没有先爬取文章数据

**解决方案：**
1. **正确的调用顺序**：
   ```
   1. 先调用 crawl_weixin_article 爬取文章
   2. 再调用 analyze_article_content 分析文章
   ```

2. **示例工作流程**：
   ```json
   // 步骤1: 爬取文章
   {
     "tool": "crawl_weixin_article",
     "parameters": {
       "url": "https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA",
       "download_images": true
     }
   }
   
   // 步骤2: 分析文章（使用步骤1返回的article_data）
   {
     "tool": "analyze_article_content",
     "parameters": {
       "article_data": "<从步骤1获取的文章数据>",
       "analysis_type": "full"
     }
   }
   ```

### 问题3: "download_images: false" 但期望下载图片

**原因：** 智能体传递了错误的参数值

**解决方案：**
1. **检查智能体配置**：确保使用默认参数
2. **明确指定参数**：
   ```json
   {
     "url": "https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA",
     "download_images": true  // 明确设置为true
   }
   ```

## 🔧 MCP服务器配置

### 1. 环境变量配置

```bash
# 设置文章保存目录
export ARTICLES_DIR="articles"

# 设置默认下载图片
export DOWNLOAD_IMAGES="true"

# 设置无头模式
export HEADLESS="true"
```

### 2. 智能体配置文件

使用提供的 `mcp_config.json` 配置文件：

```json
{
  "mcp_servers": {
    "weixin_spider": {
      "command": "python",
      "args": ["src/mcp_weixin_spider/server.py"],
      "env": {
        "ARTICLES_DIR": "articles",
        "DOWNLOAD_IMAGES": "true"
      }
    }
  },
  "default_parameters": {
    "crawl_weixin_article": {
      "download_images": true
    }
  }
}
```

## 📋 正确的使用流程

### 1. 启动MCP服务器

```bash
cd MCPWeiXin
python src/mcp_weixin_spider/server.py
```

### 2. 爬取文章

```python
# 使用Python客户端
import asyncio
from mcp_weixin_spider.client import WeixinSpiderClient

async def main():
    client = WeixinSpiderClient()
    await client.connect("src/mcp_weixin_spider/server.py")
    
    # 爬取文章（默认下载图片）
    result = await client.crawl_article(
        "https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA",
        download_images=True
    )
    
    print("爬取结果:", result)
    
    # 分析文章
    if "article" in result:
        analysis = await client.analyze_article(
            result["article"], 
            analysis_type="full"
        )
        print("分析结果:", analysis)
    
    await client.disconnect()

asyncio.run(main())
```

### 3. 查看爬取的文章

```python
# 查看最近文章
recent = await client.read_resource("weixin://articles/recent")
print("最近文章:", recent)

# 查看配置
config = await client.read_resource("weixin://config/spider")
print("配置信息:", config)
```

## 🛠️ 故障排除

### 1. 检查文件路径

```bash
# 检查当前目录结构
tree articles/ -L 2

# 或者使用ls
find articles/ -name "*.json" -o -name "*.txt" | head -10
```

### 2. 检查MCP服务器日志

```bash
# 启动服务器时查看详细日志
DEBUG=1 python src/mcp_weixin_spider/server.py
```

### 3. 验证参数

```python
# 测试参数验证
from mcp_weixin_spider.server import validate_crawl_parameters

try:
    params = validate_crawl_parameters({
        "url": "https://mp.weixin.qq.com/s/test",
        "download_images": True
    })
    print("参数验证通过:", params)
except ValueError as e:
    print("参数错误:", e)
```

## 📊 性能优化建议

### 1. 批量处理

```python
# 批量爬取多篇文章
urls = [
    "https://mp.weixin.qq.com/s/url1",
    "https://mp.weixin.qq.com/s/url2",
    "https://mp.weixin.qq.com/s/url3"
]

for i, url in enumerate(urls):
    result = await client.crawl_article(url, custom_filename=f"article_{i+1}")
    print(f"完成第{i+1}篇文章")
    
    # 添加延时避免被限制
    await asyncio.sleep(2)
```

### 2. 选择性下载图片

```python
# 只爬取文本，不下载图片（提高速度）
result = await client.crawl_article(url, download_images=False)

# 后续需要时再下载图片
if need_images:
    result_with_images = await client.crawl_article(url, download_images=True)
```

### 3. 自定义文件名

```python
# 使用自定义文件名避免重复
from datetime import datetime

custom_name = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
result = await client.crawl_article(url, custom_filename=custom_name)
```

## 🔍 调试技巧

### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 检查返回数据结构

```python
import json

result = await client.crawl_article(url)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 3. 验证文章数据完整性

```python
def check_article_data(article_data):
    required_fields = ["title", "author", "content", "url"]
    missing = [f for f in required_fields if f not in article_data]
    if missing:
        print(f"缺少字段: {missing}")
    else:
        print("文章数据完整")
    
    print(f"内容长度: {len(article_data.get('content', ''))} 字符")
    print(f"图片数量: {len(article_data.get('images', []))} 张")
```

## 📞 获取帮助

如果遇到其他问题：

1. **查看日志文件**：检查详细的错误信息
2. **检查网络连接**：确保能访问微信公众号文章
3. **验证URL格式**：确保使用正确的微信文章链接
4. **更新依赖**：确保所有Python包都是最新版本

```bash
# 更新依赖
pip install -U selenium beautifulsoup4 requests webdriver-manager Pillow
```