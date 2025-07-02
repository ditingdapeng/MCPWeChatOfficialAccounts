#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP微信爬虫模块入口点

支持以下启动方式：
1. python3 -m mcp_weixin_spider.server  # 启动MCP服务器
2. python3 -m mcp_weixin_spider         # 默认启动MCP服务器
3. python3 -m mcp_weixin_spider.client  # 启动客户端演示
"""

import sys
import asyncio
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """模块主入口点"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "client":
            # 启动客户端演示
            from client import demo_usage
            asyncio.run(demo_usage())
        elif mode == "server":
            # 启动MCP服务器
            from server import main as server_main
            asyncio.run(server_main())
        elif mode == "interactive":
            # 启动交互式客户端
            from client import InteractiveClient
            client = InteractiveClient()
            asyncio.run(client.run())
        else:
            print(f"未知模式: {mode}")
            print("可用模式: server, client, interactive")
            sys.exit(1)
    else:
        # 默认启动MCP服务器
        print("🚀 启动MCP微信爬虫服务器 (默认模式)")
        print("💡 提示: 使用 python3 -m mcp_weixin_spider client 启动客户端演示")
        from server import main as server_main
        asyncio.run(server_main())

if __name__ == "__main__":
    main()