#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP微信公众号文章爬虫客户端示例

演示如何使用MCP客户端与微信爬虫服务器进行交互
"""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeixinSpiderClient:
    """微信爬虫MCP客户端"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._server_params: Optional[StdioServerParameters] = None
        self._context_manager = None
    
    async def connect(self, server_script_path: str):
        """连接到MCP服务器"""
        try:
            # 创建服务器参数
            self._server_params = StdioServerParameters(
                command="python",
                args=[server_script_path]
            )
            
            # 启动服务器进程并建立连接
            self._context_manager = stdio_client(self._server_params)
            read, write = await self._context_manager.__aenter__()
            
            # 创建会话
            self.session = ClientSession(read, write)
            logger.info("已连接到MCP微信爬虫服务器")
            
            # 初始化会话
            await self.session.initialize()
            logger.info("MCP会话初始化完成")
            
        except Exception as e:
            logger.error(f"连接服务器失败: {e}")
            if self._context_manager:
                try:
                    await self._context_manager.__aexit__(None, None, None)
                except:
                    pass
            raise
    
    async def disconnect(self):
        """断开连接"""
        if self.session:
            try:
                # ClientSession没有close方法，直接设置为None
                logger.info("已断开MCP服务器连接")
            except Exception as e:
                logger.error(f"断开连接失败: {e}")
            finally:
                self.session = None
        
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"关闭服务器进程失败: {e}")
            finally:
                self._context_manager = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            tools = await self.session.list_tools()
            return [tool.model_dump() for tool in tools]
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            raise
    
    async def crawl_article(self, url: str, download_images: bool = True, custom_filename: Optional[str] = None) -> Dict[str, Any]:
        """爬取微信文章"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            result = await self.session.call_tool(
                "crawl_weixin_article",
                {
                    "url": url,
                    "download_images": download_images,
                    "custom_filename": custom_filename
                }
            )
            
            # 解析结果
            if result and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                try:
                    # 尝试从文本中提取JSON
                    if "✅ 文章爬取成功" in content:
                        json_start = content.find("{") 
                        if json_start != -1:
                            json_content = content[json_start:]
                            return json.loads(json_content)
                    return {"status": "success", "message": content}
                except json.JSONDecodeError:
                    return {"status": "success", "message": content}
            else:
                return {"status": "error", "message": "未收到响应"}
                
        except Exception as e:
            logger.error(f"爬取文章失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_article(self, article_data: Dict[str, Any], analysis_type: str = "full") -> Dict[str, Any]:
        """分析文章内容"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            result = await self.session.call_tool(
                "analyze_article_content",
                {
                    "article_data": article_data,
                    "analysis_type": analysis_type
                }
            )
            
            if result and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                try:
                    # 尝试从文本中提取JSON
                    if "📊 文章分析结果" in content:
                        json_start = content.find("{")
                        if json_start != -1:
                            json_content = content[json_start:]
                            return json.loads(json_content)
                    return {"status": "success", "message": content}
                except json.JSONDecodeError:
                    return {"status": "success", "message": content}
            else:
                return {"status": "error", "message": "未收到响应"}
                
        except Exception as e:
            logger.error(f"分析文章失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_statistics(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取文章统计信息"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            result = await self.session.call_tool(
                "get_article_statistics",
                {
                    "article_data": article_data
                }
            )
            
            if result and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                try:
                    # 尝试从文本中提取JSON
                    if "📈 文章统计信息" in content:
                        json_start = content.find("{")
                        if json_start != -1:
                            json_content = content[json_start:]
                            return json.loads(json_content)
                    return {"status": "success", "message": content}
                except json.JSONDecodeError:
                    return {"status": "success", "message": content}
            else:
                return {"status": "error", "message": "未收到响应"}
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """获取可用资源列表"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            resources = await self.session.list_resources()
            return [resource.model_dump() for resource in resources]
        except Exception as e:
            logger.error(f"获取资源列表失败: {e}")
            raise
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源内容"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            content = await self.session.read_resource(uri)
            return json.loads(content)
        except Exception as e:
            logger.error(f"读取资源失败 {uri}: {e}")
            raise


async def demo_usage():
    """演示客户端使用方法"""
    client = WeixinSpiderClient()
    
    try:
        # 连接到服务器（需要指定服务器脚本路径）
        server_script = "/Users/dapeng/Code/study/MCP-Study/mcp-weixin/MCPWeiXin/src/mcp_weixin_spider/server.py"
        await client.connect(server_script)
        
        # 获取可用工具
        print("\n=== 可用工具 ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        
        # 获取可用资源
        print("\n=== 可用资源 ===")
        resources = await client.list_resources()
        for resource in resources:
            print(f"- {resource['name']}: {resource['description']}")
        
        # 示例：爬取文章（需要提供真实的微信文章URL）
        # test_url = "https://mp.weixin.qq.com/s/example"
        # print(f"\n=== 爬取文章: {test_url} ===")
        # result = await client.crawl_article(test_url)
        # print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 读取最近文章资源
        print("\n=== 最近文章 ===")
        try:
            recent_articles = await client.read_resource("weixin://articles/recent")
            print(json.dumps(recent_articles, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"读取最近文章失败: {e}")
        
        # 读取爬虫配置
        print("\n=== 爬虫配置 ===")
        try:
            config = await client.read_resource("weixin://config/spider")
            print(json.dumps(config, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"读取配置失败: {e}")
        
    except Exception as e:
        logger.error(f"演示过程中出错: {e}")
    finally:
        await client.disconnect()


class InteractiveClient:
    """交互式客户端"""
    
    def __init__(self):
        self.client = WeixinSpiderClient()
        self.connected = False
    
    async def start(self):
        """启动交互式客户端"""
        print("🕷️ MCP微信爬虫客户端")
        print("输入 'help' 查看可用命令，输入 'quit' 退出")
        
        try:
            # 连接服务器
            server_script = "/Users/dapeng/Code/study/MCP-Study/mcp-weixin/MCPWeiXin/src/mcp_weixin_spider/server.py"
            await self.client.connect(server_script)
            self.connected = True
            print("✅ 已连接到MCP服务器")
            
            # 交互循环
            while True:
                try:
                    command = input("\n> ").strip()
                    if not command:
                        continue
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    elif command.lower() == 'help':
                        await self.show_help()
                    elif command.lower() == 'tools':
                        await self.list_tools()
                    elif command.lower() == 'resources':
                        await self.list_resources()
                    elif command.startswith('crawl '):
                        url = command[6:].strip()
                        await self.crawl_article(url)
                    elif command.startswith('recent'):
                        await self.show_recent_articles()
                    elif command.startswith('config'):
                        await self.show_config()
                    else:
                        print("❌ 未知命令，输入 'help' 查看帮助")
                        
                except KeyboardInterrupt:
                    print("\n收到中断信号...")
                    break
                except Exception as e:
                    print(f"❌ 执行命令时出错: {e}")
        
        except Exception as e:
            print(f"❌ 启动客户端失败: {e}")
        finally:
            if self.connected:
                await self.client.disconnect()
                print("👋 已断开连接")
    
    async def show_help(self):
        """显示帮助信息"""
        help_text = """
📖 可用命令：
  help          - 显示此帮助信息
  tools         - 列出可用工具
  resources     - 列出可用资源
  crawl <url>   - 爬取指定URL的微信文章
  recent        - 显示最近爬取的文章
  config        - 显示爬虫配置
  quit/exit/q   - 退出客户端

📝 示例：
  crawl https://mp.weixin.qq.com/s/example
        """
        print(help_text)
    
    async def list_tools(self):
        """列出可用工具"""
        try:
            tools = await self.client.list_tools()
            print("\n🔧 可用工具：")
            for tool in tools:
                print(f"  • {tool['name']}: {tool['description']}")
        except Exception as e:
            print(f"❌ 获取工具列表失败: {e}")
    
    async def list_resources(self):
        """列出可用资源"""
        try:
            resources = await self.client.list_resources()
            print("\n📚 可用资源：")
            for resource in resources:
                print(f"  • {resource['name']}: {resource['description']}")
        except Exception as e:
            print(f"❌ 获取资源列表失败: {e}")
    
    async def crawl_article(self, url: str):
        """爬取文章"""
        if not url:
            print("❌ 请提供文章URL")
            return
        
        print(f"🕷️ 开始爬取: {url}")
        try:
            result = await self.client.crawl_article(url)
            print("\n📄 爬取结果：")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
    
    async def show_recent_articles(self):
        """显示最近文章"""
        try:
            recent = await self.client.read_resource("weixin://articles/recent")
            print("\n📰 最近爬取的文章：")
            print(json.dumps(recent, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 获取最近文章失败: {e}")
    
    async def show_config(self):
        """显示配置"""
        try:
            config = await self.client.read_resource("weixin://config/spider")
            print("\n⚙️ 爬虫配置：")
            print(json.dumps(config, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 获取配置失败: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # 交互式模式
        client = InteractiveClient()
        asyncio.run(client.start())
    else:
        # 演示模式
        asyncio.run(demo_usage())