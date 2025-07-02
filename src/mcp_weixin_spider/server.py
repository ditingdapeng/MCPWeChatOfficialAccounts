#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP微信公众号文章爬虫服务器

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
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.models import ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# 添加项目根目录到Python路径
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

try:
    # 优先使用简化版爬虫
    from weixin_spider_simple import WeixinSpiderWithImages
    logging.info("使用简化版爬虫模块")
except ImportError:
    try:
        # 备用：使用原版爬虫
        python_spider_path = os.path.join(project_root, 'pythonSpider')
        sys.path.append(python_spider_path)
        from weixin_spider_with_image import WeixinSpiderWithImages
        logging.info("使用原版爬虫模块")
    except ImportError as e:
        logging.error(f"导入爬虫模块失败: {e}")
        logging.error(f"Python路径: {sys.path}")
        logging.error(f"当前工作目录: {os.getcwd()}")
        logging.error(f"项目根目录: {project_root}")
        WeixinSpiderWithImages = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
server = Server("mcp-weixin-spider")

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
    return spider_instance


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="crawl_weixin_article",
            description="爬取微信公众号文章内容和图片",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "微信公众号文章的URL链接"
                    },
                    "download_images": {
                        "type": "boolean",
                        "description": "是否下载文章中的图片",
                        "default": True
                    },
                    "custom_filename": {
                        "type": "string",
                        "description": "自定义文件名（可选）",
                        "default": None
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="analyze_article_content",
            description="分析已爬取的文章内容，提取关键信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_data": {
                        "type": "object",
                        "description": "文章数据对象"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["summary", "keywords", "images", "full"],
                        "description": "分析类型：summary(摘要), keywords(关键词), images(图片信息), full(完整分析)",
                        "default": "full"
                    }
                },
                "required": ["article_data"]
            }
        ),
        Tool(
            name="get_article_statistics",
            description="获取文章统计信息（字数、图片数量等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_data": {
                        "type": "object",
                        "description": "文章数据对象"
                    }
                },
                "required": ["article_data"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        if name == "crawl_weixin_article":
            return await crawl_weixin_article(arguments)
        elif name == "analyze_article_content":
            return await analyze_article_content(arguments)
        elif name == "get_article_statistics":
            return await get_article_statistics(arguments)
        else:
            raise ValueError(f"未知的工具: {name}")
    except Exception as e:
        logger.error(f"工具调用失败 {name}: {e}")
        return [TextContent(type="text", text=f"错误: {str(e)}")]


def validate_crawl_parameters(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """验证和标准化爬取参数"""
    url = arguments.get("url")
    if not url:
        raise ValueError("缺少必需参数: url")
    
    if not isinstance(url, str) or not url.startswith("https://mp.weixin.qq.com/"):
        raise ValueError("无效的微信文章URL，必须以 https://mp.weixin.qq.com/ 开头")
    
    # 设置默认值并验证
    validated = {
        "url": url,
        "download_images": arguments.get("download_images", True),  # 默认为True
        "custom_filename": arguments.get("custom_filename")
    }
    
    logger.info(f"参数验证通过: download_images={validated['download_images']}, url={url[:50]}...")
    return validated

async def crawl_weixin_article(arguments: Dict[str, Any]) -> List[TextContent]:
    """爬取微信公众号文章"""
    try:
        # 验证和标准化参数
        validated_args = validate_crawl_parameters(arguments)
        url = validated_args["url"]
        download_images = validated_args["download_images"]
        custom_filename = validated_args["custom_filename"]
        
    except ValueError as e:
        return [TextContent(type="text", text=f"参数错误: {str(e)}")]
    
    try:
        # 获取爬虫实例
        spider = get_spider_instance()
        
        # 设置是否下载图片
        spider.download_images = download_images
        
        logger.info(f"开始爬取文章: {url}")
        
        # 爬取文章
        article_data = spider.crawl_article_by_url(url)
        
        if not article_data:
            return [TextContent(type="text", text="爬取失败: 无法获取文章内容")]
        
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
            
            return [TextContent(
                type="text", 
                text=f"✅ 文章爬取成功\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            )]
        else:
            return [TextContent(type="text", text="爬取失败: 保存文件时出错")]
            
    except Exception as e:
        logger.error(f"爬取文章失败: {e}")
        return [TextContent(type="text", text=f"爬取失败: {str(e)}")]


def validate_analysis_parameters(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """验证分析参数"""
    article_data = arguments.get("article_data")
    if not article_data:
        raise ValueError("缺少必需参数: article_data。请先使用 crawl_weixin_article 工具爬取文章数据")
    
    if not isinstance(article_data, dict):
        raise ValueError("article_data 必须是字典格式的文章数据")
    
    # 检查文章数据的基本字段
    required_fields = ["title", "content"]
    missing_fields = [field for field in required_fields if field not in article_data]
    if missing_fields:
        logger.warning(f"文章数据缺少字段: {missing_fields}")
    
    validated = {
        "article_data": article_data,
        "analysis_type": arguments.get("analysis_type", "full")
    }
    
    logger.info(f"分析参数验证通过: analysis_type={validated['analysis_type']}, 文章标题={article_data.get('title', 'N/A')[:30]}...")
    return validated

async def analyze_article_content(arguments: Dict[str, Any]) -> List[TextContent]:
    """分析文章内容"""
    try:
        # 验证参数
        validated_args = validate_analysis_parameters(arguments)
        article_data = validated_args["article_data"]
        analysis_type = validated_args["analysis_type"]
        
    except ValueError as e:
        return [TextContent(type="text", text=f"参数错误: {str(e)}")]
    
    try:
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
            # 简单的关键词提取（可以后续集成更复杂的NLP库）
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
        
        return [TextContent(
            type="text",
            text=f"📊 文章分析结果\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        )]
        
    except Exception as e:
        logger.error(f"分析文章内容失败: {e}")
        return [TextContent(type="text", text=f"分析失败: {str(e)}")]


async def get_article_statistics(arguments: Dict[str, Any]) -> List[TextContent]:
    """获取文章统计信息"""
    article_data = arguments.get("article_data")
    
    if not article_data:
        return [TextContent(type="text", text="错误: 缺少文章数据")]
    
    try:
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
        
        return [TextContent(
            type="text",
            text=f"📈 文章统计信息\n\n{json.dumps(stats, ensure_ascii=False, indent=2)}"
        )]
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return [TextContent(type="text", text=f"统计失败: {str(e)}")]


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """列出可用的资源"""
    return [
        Resource(
            uri="weixin://articles/recent",
            name="最近爬取的文章",
            description="显示最近爬取的微信文章列表",
            mimeType="application/json"
        ),
        Resource(
            uri="weixin://config/spider",
            name="爬虫配置",
            description="当前爬虫的配置信息",
            mimeType="application/json"
        )
    ]


def find_articles_directory() -> Path:
    """智能查找文章目录，支持多个可能的路径"""
    base_path = Path(__file__).parent.parent.parent
    possible_paths = [
        base_path / "articles",
        base_path / "weixin_articles", 
        base_path / "pythonSpider" / "articles",
        Path("articles"),
        Path("weixin_articles")
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            logger.info(f"找到文章目录: {path}")
            return path
    
    logger.warning(f"未找到文章目录，尝试的路径: {[str(p) for p in possible_paths]}")
    return base_path / "articles"  # 返回默认路径

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """读取资源内容 - 支持智能路径查找"""
    try:
        if uri == "weixin://articles/recent":
            # 智能查找文章目录
            articles_dir = find_articles_directory()
            
            if articles_dir.exists():
                recent_articles = []
                for article_dir in sorted(articles_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                    if article_dir.is_dir():
                        json_file = article_dir / f"{article_dir.name}.json"
                        if json_file.exists():
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    article_data = json.load(f)
                                recent_articles.append({
                                    "title": article_data.get("title", ""),
                                    "author": article_data.get("author", ""),
                                    "crawl_time": article_data.get("crawl_time", ""),
                                    "directory": str(article_dir)
                                })
                            except Exception as e:
                                logger.error(f"读取文章文件失败 {json_file}: {e}")
                
                return json.dumps({
                    "recent_articles": recent_articles,
                    "articles_directory": str(articles_dir),
                    "total_found": len(recent_articles)
                }, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "recent_articles": [], 
                    "message": "文章目录不存在",
                    "searched_paths": [str(p) for p in [articles_dir]]
                }, ensure_ascii=False)
        
        elif uri == "weixin://config/spider":
            config = {
                "spider_status": "ready" if spider_instance else "not_initialized",
                "default_settings": {
                    "headless": True,
                    "wait_time": 10,
                    "download_images": True
                },
                "supported_features": [
                    "文章内容抓取",
                    "图片下载",
                    "多格式保存 (JSON, TXT)",
                    "内容分析",
                    "统计信息"
                ]
            }
            return json.dumps(config, ensure_ascii=False, indent=2)
        
        else:
            raise ValueError(f"未知的资源URI: {uri}")
            
    except Exception as e:
        logger.error(f"读取资源失败 {uri}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def cleanup():
    """清理资源"""
    global spider_instance
    if spider_instance:
        try:
            spider_instance.close()
            logger.info("爬虫实例已关闭")
        except Exception as e:
            logger.error(f"关闭爬虫实例失败: {e}")
        finally:
            spider_instance = None


async def main():
    """主函数"""
    try:
        # 检查爬虫模块是否可用
        if WeixinSpiderWithImages is None:
            logger.warning("爬虫模块未导入，服务器将以有限功能运行")
        else:
            logger.info("爬虫模块导入成功")
        
        # 启动MCP服务器
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP微信爬虫服务器启动")
            try:
                await server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mcp-weixin-spider",
                        server_version="0.1.0",
                        capabilities=ServerCapabilities(
                            tools={},
                            resources={}
                        )
                    )
                )
            except Exception as e:
                logger.error(f"服务器运行时错误: {e}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                raise
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise
    finally:
        await cleanup()
        logger.info("MCP微信爬虫服务器已关闭")


if __name__ == "__main__":
    asyncio.run(main())