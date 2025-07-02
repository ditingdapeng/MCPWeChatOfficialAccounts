#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确使用MCP微信爬虫的示例
"""

import asyncio
import json
from pathlib import Path

# 方法1: 直接使用爬虫模块
def direct_crawl_example():
    """直接使用爬虫模块示例"""
    from weixin_spider_simple import WeixinSpiderWithImages
    
    # 创建爬虫实例 - 确保参数正确
    spider = WeixinSpiderWithImages(
        headless=True,           # 无头模式
        wait_time=10,           # 等待时间
        download_images=True    # 下载图片 - 默认为True
    )
    
    try:
        # 爬取文章
        url = "https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA"
        print(f"开始爬取: {url}")
        
        article_data = spider.crawl_article_by_url(url)
        
        if article_data:
            print("✅ 爬取成功!")
            print(f"标题: {article_data.get('title', 'N/A')}")
            print(f"作者: {article_data.get('author', 'N/A')}")
            print(f"内容长度: {len(article_data.get('content_text', ''))} 字符")
            print(f"图片数量: {len(article_data.get('images', []))} 张")
            
            # 保存文章
            if spider.save_article_to_file(article_data):
                print("✅ 文章保存成功")
                
                # 检查保存的文件
                articles_dir = Path("articles")
                if articles_dir.exists():
                    print(f"📁 文章保存在: {articles_dir.absolute()}")
                    
        else:
            print("❌ 爬取失败")
            
    finally:
        spider.close()

# 方法2: 使用MCP客户端
async def mcp_client_example():
    """MCP客户端使用示例"""
    try:
        from mcp_weixin_spider.client import WeixinSpiderClient
        
        client = WeixinSpiderClient()
        await client.connect("src/mcp_weixin_spider/server.py")
        
        # 爬取文章 - 明确指定参数
        result = await client.crawl_article(
            url="https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA",
            download_images=True  # 明确设置为True
        )
        
        print("MCP爬取结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 如果爬取成功，进行分析
        if "article" in result:
            analysis = await client.analyze_article(
                article_data=result["article"],
                analysis_type="full"
            )
            print("
分析结果:")
            print(json.dumps(analysis, ensure_ascii=False, indent=2))
        
        await client.disconnect()
        
    except Exception as e:
        print(f"MCP客户端示例失败: {e}")

if __name__ == "__main__":
    print("=== MCP微信爬虫使用示例 ===")
    
    print("
1. 直接使用爬虫模块:")
    direct_crawl_example()
    
    print("
2. 使用MCP客户端:")
    asyncio.run(mcp_client_example())
