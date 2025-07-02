#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP微信爬虫主启动脚本

提供多种启动方式：
1. MCP服务器模式
2. 客户端演示模式
3. 交互式客户端模式
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from server import main as server_main
from client import demo_usage, InteractiveClient


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="MCP微信公众号文章爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动MCP服务器
  python main.py server
  
  # 运行客户端演示
  python main.py client
  
  # 启动交互式客户端
  python main.py interactive
  
  # 显示版本信息
  python main.py --version
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["server", "client", "interactive"],
        help="运行模式：server(服务器), client(客户端演示), interactive(交互式客户端)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="MCP微信爬虫 v0.1.0"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    return parser


async def run_server(debug: bool = False):
    """运行MCP服务器"""
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 调试模式已启用")
    
    print("🚀 启动MCP微信爬虫服务器...")
    await server_main()


async def run_client_demo(debug: bool = False):
    """运行客户端演示"""
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 调试模式已启用")
    
    print("🎯 运行MCP客户端演示...")
    await demo_usage()


async def run_interactive_client(debug: bool = False):
    """运行交互式客户端"""
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 调试模式已启用")
    
    client = InteractiveClient()
    await client.start()


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        if args.mode == "server":
            asyncio.run(run_server(args.debug))
        elif args.mode == "client":
            asyncio.run(run_client_demo(args.debug))
        elif args.mode == "interactive":
            asyncio.run(run_interactive_client(args.debug))
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()