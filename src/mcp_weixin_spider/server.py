#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP微信公众号文章爬虫服务器 - FastMCP版本

基于MCP标准实现，使用FastMCP高级封装
提供以下功能：
1. 爬取微信公众号文章内容
2. 下载文章中的图片
3. 返回结构化的文章数据
4. 提供文章内容分析
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 导入MCP FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # 如果FastMCP不可用，回退到标准实现
    print("FastMCP不可用，请使用标准server.py")
    sys.exit(1)

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

try:
    # 使用简化版爬虫
    from weixin_spider_simple import WeixinSpiderWithImages
    logging.info("使用简化版爬虫模块")
except ImportError as e:
    logging.error(f"导入简化版爬虫模块失败: {e}")
    WeixinSpiderWithImages = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastMCP应用实例
app = FastMCP("mcp-weixin-spider")

# 全局爬虫实例
spider_instance: Optional[WeixinSpiderWithImages] = None


def get_spider_instance() -> WeixinSpiderWithImages:
    """获取爬虫实例（单例模式）"""
    global spider_instance
    if spider_instance is None:
        if WeixinSpiderWithImages is None:
            raise RuntimeError("爬虫模块未正确导入")
        try:
            spider_instance = WeixinSpiderWithImages(
                headless=True,  # MCP服务器中使用无头模式
                wait_time=10,
                download_images=True
            )
            logger.info("爬虫实例初始化成功")
        except Exception as e:
            logger.error(f"爬虫实例初始化失败: {e}")
            raise RuntimeError(f"无法初始化爬虫实例: {e}")
    
    # 检查驱动是否仍然有效
    if spider_instance.driver is None:
        logger.warning("检测到驱动已失效，重新初始化...")
        try:
            spider_instance.setup_driver(headless=True)
            logger.info("驱动重新初始化成功")
        except Exception as e:
            logger.error(f"驱动重新初始化失败: {e}")
            # 创建新的爬虫实例
            try:
                spider_instance = WeixinSpiderWithImages(
                    headless=True,
                    wait_time=10,
                    download_images=True
                )
                logger.info("创建新的爬虫实例成功")
            except Exception as new_e:
                logger.error(f"创建新爬虫实例失败: {new_e}")
                raise RuntimeError(f"无法创建爬虫实例: {new_e}")
    
    return spider_instance


@app.tool()
def crawl_weixin_article(url: str, download_images: bool = True, custom_filename: str = None) -> str:
    """
    爬取微信公众号文章内容和图片
    
    Args:
        url: 微信公众号文章的URL链接
        download_images: 是否下载文章中的图片
        custom_filename: 自定义文件名（可选）
    
    Returns:
        爬取结果的JSON字符串
    """
    try:
        # 验证URL
        if not url or not isinstance(url, str) or not url.startswith("https://mp.weixin.qq.com/"):
            raise ValueError("无效的微信文章URL，必须以 https://mp.weixin.qq.com/ 开头")
        
        logger.info(f"开始爬取文章: {url}")
        
        # 获取爬虫实例
        spider = get_spider_instance()
        
        # 设置是否下载图片
        spider.download_images = download_images
        
        # 爬取文章
        article_data = spider.crawl_article_by_url(url)
        
        if not article_data:
            raise RuntimeError("无法获取文章内容")
        
        # 保存文章到文件
        success = spider.save_article_to_file(article_data, custom_filename)
        
        if success:
            # 构建返回结果
            result = {
                "status": "success",
                "message": "文章爬取成功",
                "article": {
                    "title": article_data.get("title", ""),
                    "author": article_data.get("author", ""),
                    "publish_time": article_data.get("publish_time", ""),
                    "url": article_data.get("url", ""),
                    "content_length": len(article_data.get("content", "")),
                    "images_count": len(article_data.get("images", [])),
                    "crawl_time": article_data.get("crawl_time", "")
                },
                "files_saved": {
                    "json": True,
                    "txt": True,
                    "images": download_images
                }
            }
            
            if download_images:
                images = article_data.get("images", [])
                success_count = sum(1 for img in images if img.get("download_success", False))
                result["article"]["images_downloaded"] = f"{success_count}/{len(images)}"
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            raise RuntimeError("保存文件时出错")
            
    except Exception as e:
        logger.error(f"爬取文章失败: {e}")
        error_result = {
            "status": "error",
            "message": f"爬取失败: {str(e)}",
            "url": url
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@app.tool()
def analyze_article_content(article_data: dict, analysis_type: str = "full") -> str:
    """
    分析已爬取的文章内容，提取关键信息
    
    Args:
        article_data: 文章数据对象
        analysis_type: 分析类型：summary(摘要), keywords(关键词), images(图片信息), full(完整分析)
    
    Returns:
        分析结果的JSON字符串
    """
    try:
        if not article_data or not isinstance(article_data, dict):
            raise ValueError("article_data 必须是字典格式的文章数据")
        
        # 检查文章数据的基本字段
        required_fields = ["title", "content"]
        missing_fields = [field for field in required_fields if field not in article_data]
        if missing_fields:
            logger.warning(f"文章数据缺少字段: {missing_fields}")
        
        logger.info(f"分析文章内容: analysis_type={analysis_type}, 文章标题={article_data.get('title', 'N/A')[:30]}...")
        
        result = {"analysis_type": analysis_type}
        
        if analysis_type in ["summary", "full"]:
            content = article_data.get("content", "")
            result["summary"] = {
                "title": article_data.get("title", ""),
                "author": article_data.get("author", ""),
                "publish_time": article_data.get("publish_time", ""),
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "word_count": len(content),
                "paragraph_count": len(content.split("\n\n")) if content else 0
            }
        
        if analysis_type in ["keywords", "full"]:
            content = article_data.get("content", "")
            # 简单的关键词提取
            words = content.split()
            word_freq = {}
            for word in words:
                if len(word) > 1:  # 过滤单字符
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 获取前10个高频词
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            result["keywords"] = [word for word, freq in top_words]
        
        if analysis_type in ["images", "full"]:
            images = article_data.get("images", [])
            result["images_analysis"] = {
                "total_count": len(images),
                "downloaded_count": sum(1 for img in images if img.get("download_success", False)),
                "failed_count": sum(1 for img in images if not img.get("download_success", False)),
                "image_details": [
                    {
                        "filename": img.get("filename", ""),
                        "alt_text": img.get("alt", ""),
                        "download_success": img.get("download_success", False)
                    }
                    for img in images[:5]  # 只显示前5张图片的详情
                ]
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"分析文章内容失败: {e}")
        error_result = {
            "status": "error",
            "message": f"分析失败: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@app.tool()
def get_article_statistics(article_data: dict) -> str:
    """
    获取文章统计信息（字数、图片数量等）
    
    Args:
        article_data: 文章数据对象
    
    Returns:
        统计信息的JSON字符串
    """
    try:
        if not article_data or not isinstance(article_data, dict):
            raise ValueError("article_data 必须是字典格式的文章数据")
        
        content = article_data.get("content", "")
        images = article_data.get("images", [])
        
        stats = {
            "basic_info": {
                "title": article_data.get("title", ""),
                "author": article_data.get("author", ""),
                "publish_time": article_data.get("publish_time", ""),
                "crawl_time": article_data.get("crawl_time", "")
            },
            "content_statistics": {
                "total_characters": len(content),
                "total_words": len(content.split()),
                "paragraphs": len(content.split("\n\n")) if content else 0,
                "lines": len(content.split("\n")) if content else 0
            },
            "image_statistics": {
                "total_images": len(images),
                "downloaded_successfully": sum(1 for img in images if img.get("download_success", False)),
                "download_failed": sum(1 for img in images if not img.get("download_success", False)),
                "download_success_rate": f"{(sum(1 for img in images if img.get('download_success', False)) / len(images) * 100):.1f}%" if images else "0%"
            }
        }
        
        return json.dumps(stats, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        error_result = {
            "status": "error",
            "message": f"统计失败: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


def cleanup():
    """清理资源"""
    global spider_instance
    if spider_instance:
        try:
            spider_instance.close()
            logger.info("爬虫实例已关闭")
        except Exception as e:
            logger.error(f"关闭爬虫实例时出错: {e}")
        finally:
            spider_instance = None


def main():
    """启动MCP服务器"""
    try:
        logger.info("启动MCP微信爬虫服务器 (FastMCP版本)")
        if WeixinSpiderWithImages is None:
            logger.error("爬虫模块未正确导入，无法启动服务器")
            return
        
        logger.info("爬虫模块导入成功")
        logger.info("MCP微信爬虫服务器启动")
        
        # 运行FastMCP应用
        app.run(transport="stdio")
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
    finally:
        cleanup()
        logger.info("MCP微信爬虫服务器已关闭")


if __name__ == "__main__":
    main()