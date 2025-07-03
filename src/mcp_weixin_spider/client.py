#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP微信爬虫客户端 - 标准实现

基于MCP标准实现的客户端，包含：
1. Connect-to-server初始化
2. MCP服务器的session管理
3. 实现调用MCP方法处理交互
4. 实现循环提问和最后退出后关闭session
5. 运行该客户端的相关代码
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 导入MCP客户端相关模块
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPWeixinClient:
    """
    MCP微信爬虫客户端类
    
    实现标准的MCP客户端功能：
    - 连接到MCP服务器
    - 管理客户端会话
    - 调用MCP工具
    - 处理用户交互
    """
    
    def __init__(self, server_script_path: str):
        """
        初始化MCP客户端
        
        Args:
            server_script_path: MCP服务器脚本路径
        """
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.server_params: Optional[StdioServerParameters] = None
        self.available_tools: List[Dict[str, Any]] = []
        
    async def connect_to_server(self) -> bool:
        """
        连接到MCP服务器并初始化会话
        
        Returns:
            连接是否成功
        """
        try:
            logger.info(f"正在连接到MCP服务器: {self.server_script_path}")
            
            # 创建服务器参数
            self.server_params = StdioServerParameters(
                command="python",
                args=[self.server_script_path]
            )
            
            # 使用stdio_client连接服务器
            async with stdio_client(self.server_params) as (read, write):
                # 创建客户端会话
                async with ClientSession(read, write) as session:
                    self.session = session
                    
                    # 初始化会话
                    await self._initialize_session()
                    
                    logger.info("成功连接到MCP服务器")
                    return True
                    
        except Exception as e:
            logger.error(f"连接MCP服务器失败: {e}")
            return False
    
    async def _initialize_session(self):
        """
        初始化MCP会话
        
        包括：
        - 初始化协议
        - 获取可用工具列表
        - 获取可用资源列表
        """
        try:
            # 初始化协议
            init_result = await self.session.initialize()
            logger.info(f"协议初始化成功: {init_result}")
            
            # 获取可用工具
            tools_result = await self.session.list_tools()
            self.available_tools = tools_result.tools
            logger.info(f"获取到 {len(self.available_tools)} 个可用工具")
            
            # 打印可用工具信息
            for tool in self.available_tools:
                logger.info(f"工具: {tool.name} - {tool.description}")
                
        except Exception as e:
            logger.error(f"初始化会话失败: {e}")
            raise
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的MCP工具
        
        Returns:
            工具列表
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            result = await self.session.list_tools()
            tools_info = []
            
            for tool in result.tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                tools_info.append(tool_info)
            
            return tools_info
            
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具调用结果
        """
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        try:
            logger.info(f"调用工具: {tool_name}，参数: {arguments}")
            
            # 调用工具
            result = await self.session.call_tool(tool_name, arguments)
            
            # 处理结果
            if result.isError:
                error_msg = f"工具调用失败: {result.content}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg
                }
            else:
                logger.info(f"工具调用成功: {tool_name}")
                return {
                    "status": "success",
                    "result": result.content
                }
                
        except Exception as e:
            error_msg = f"调用工具 {tool_name} 时出错: {e}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def crawl_article(self, url: str, download_images: bool = True, custom_filename: str = None) -> Dict[str, Any]:
        """
        爬取微信文章
        
        Args:
            url: 文章URL
            download_images: 是否下载图片
            custom_filename: 自定义文件名
        
        Returns:
            爬取结果
        """
        arguments = {
            "url": url,
            "download_images": download_images
        }
        
        if custom_filename:
            arguments["custom_filename"] = custom_filename
        
        return await self.call_tool("crawl_weixin_article", arguments)
    
    async def analyze_article(self, article_data: Dict[str, Any], analysis_type: str = "full") -> Dict[str, Any]:
        """
        分析文章内容
        
        Args:
            article_data: 文章数据
            analysis_type: 分析类型
        
        Returns:
            分析结果
        """
        arguments = {
            "article_data": article_data,
            "analysis_type": analysis_type
        }
        
        return await self.call_tool("analyze_article_content", arguments)
    
    async def get_statistics(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取文章统计信息
        
        Args:
            article_data: 文章数据
        
        Returns:
            统计信息
        """
        arguments = {
            "article_data": article_data
        }
        
        return await self.call_tool("get_article_statistics", arguments)
    
    async def interactive_session(self):
        """
        交互式会话
        
        实现循环提问和处理用户输入
        """
        print("\n=== MCP微信爬虫客户端 ===")
        print("输入 'help' 查看帮助信息")
        print("输入 'quit' 或 'exit' 退出程序")
        print("="*40)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n请输入命令: ").strip()
                
                if not user_input:
                    continue
                
                # 处理退出命令
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("正在退出...")
                    break
                
                # 处理帮助命令
                elif user_input.lower() in ['help', 'h']:
                    await self._show_help()
                
                # 处理工具列表命令
                elif user_input.lower() in ['tools', 'list']:
                    await self._show_tools()
                
                # 处理爬取命令
                elif user_input.lower().startswith('crawl '):
                    url = user_input[6:].strip()
                    if url:
                        await self._handle_crawl_command(url)
                    else:
                        print("请提供文章URL")
                
                # 处理未知命令
                else:
                    print(f"未知命令: {user_input}")
                    print("输入 'help' 查看帮助信息")
                    
            except KeyboardInterrupt:
                print("\n收到中断信号，正在退出...")
                break
            except Exception as e:
                logger.error(f"处理用户输入时出错: {e}")
                print(f"出错: {e}")
    
    async def _show_help(self):
        """显示帮助信息"""
        help_text = """
可用命令：
  help, h          - 显示此帮助信息
  tools, list      - 显示可用工具列表
  crawl <URL>      - 爬取指定URL的微信文章
  quit, exit, q    - 退出程序

示例：
  crawl https://mp.weixin.qq.com/s/example
"""
        print(help_text)
    
    async def _show_tools(self):
        """显示可用工具"""
        try:
            tools = await self.list_available_tools()
            print("\n可用工具：")
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool['name']}")
                print(f"   描述: {tool['description']}")
                print()
        except Exception as e:
            print(f"获取工具列表失败: {e}")
    
    async def _handle_crawl_command(self, url: str):
        """处理爬取命令"""
        try:
            print(f"正在爬取文章: {url}")
            result = await self.crawl_article(url)
            
            if result["status"] == "success":
                print("爬取成功！")
                # 解析结果
                if isinstance(result["result"], list) and result["result"]:
                    content = result["result"][0].get("content", "")
                    if content:
                        try:
                            article_info = json.loads(content)
                            if "article" in article_info:
                                article = article_info["article"]
                                print(f"标题: {article.get('title', 'N/A')}")
                                print(f"作者: {article.get('author', 'N/A')}")
                                print(f"发布时间: {article.get('publish_time', 'N/A')}")
                                print(f"内容长度: {article.get('content_length', 0)} 字符")
                                print(f"图片数量: {article.get('images_count', 0)}")
                        except json.JSONDecodeError:
                            print("结果解析失败")
            else:
                print(f"爬取失败: {result.get('message', '未知错误')}")
                
        except Exception as e:
            print(f"爬取过程中出错: {e}")
    
    async def close_session(self):
        """
        关闭会话和连接
        """
        try:
            if self.session:
                # 注意：在实际的stdio_client上下文中，session会自动关闭
                logger.info("会话已关闭")
                self.session = None
        except Exception as e:
            logger.error(f"关闭会话时出错: {e}")


async def run_client(server_script_path: str):
    """
    运行MCP客户端
    
    Args:
        server_script_path: 服务器脚本路径
    """
    client = MCPWeixinClient(server_script_path)
    
    try:
        # 连接到服务器
        logger.info("正在启动MCP客户端...")
        
        # 创建服务器参数
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )
        
        # 使用stdio_client连接服务器
        async with stdio_client(server_params) as (read, write):
            # 创建客户端会话
            async with ClientSession(read, write) as session:
                client.session = session
                
                # 初始化会话
                await client._initialize_session()
                
                # 开始交互式会话
                await client.interactive_session()
                
    except Exception as e:
        logger.error(f"客户端运行出错: {e}")
    finally:
        # 关闭会话
        await client.close_session()
        logger.info("MCP客户端已退出")


def main():
    """
    主函数
    """
    # 默认服务器脚本路径
    server_script = "server.py"
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        server_script = sys.argv[1]
    
    # 检查服务器脚本是否存在
    if not Path(server_script).exists():
        print(f"错误: 服务器脚本 '{server_script}' 不存在")
        print("用法: python client_standard.py [server_script_path]")
        sys.exit(1)
    
    try:
        # 运行客户端
        asyncio.run(run_client(server_script))
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()