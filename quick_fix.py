#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复脚本 - 解决MCP微信爬虫常见问题

使用方法:
python quick_fix.py --check-paths
python quick_fix.py --fix-config
python quick_fix.py --test-crawl
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

def check_article_paths() -> Dict[str, Any]:
    """检查文章路径配置"""
    print("🔍 检查文章路径配置...")
    
    base_path = Path(__file__).parent
    possible_paths = [
        base_path / "articles",
        base_path / "weixin_articles",
        base_path / "pythonSpider" / "articles",
        base_path.parent / "pythonSpider" / "articles"
    ]
    
    results = {
        "existing_paths": [],
        "article_counts": {},
        "recommended_path": None
    }
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            article_dirs = [d for d in path.iterdir() if d.is_dir()]
            results["existing_paths"].append(str(path))
            results["article_counts"][str(path)] = len(article_dirs)
            
            print(f"✅ 找到路径: {path} (包含 {len(article_dirs)} 个文章目录)")
            
            # 显示最近的几篇文章
            if article_dirs:
                recent_articles = sorted(article_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                for article_dir in recent_articles:
                    print(f"   📄 {article_dir.name}")
        else:
            print(f"❌ 路径不存在: {path}")
    
    # 推荐使用的路径
    if results["existing_paths"]:
        # 选择包含最多文章的路径
        recommended = max(results["article_counts"].items(), key=lambda x: x[1])
        results["recommended_path"] = recommended[0]
        print(f"\n💡 推荐使用路径: {recommended[0]} (包含 {recommended[1]} 篇文章)")
    else:
        results["recommended_path"] = str(base_path / "articles")
        print(f"\n💡 推荐创建路径: {results['recommended_path']}")
    
    return results

def fix_mcp_config() -> bool:
    """修复MCP配置"""
    print("\n🔧 修复MCP配置...")
    
    config_file = Path(__file__).parent / "mcp_config.json"
    
    # 检查文章路径
    path_results = check_article_paths()
    recommended_path = Path(path_results["recommended_path"])
    
    # 创建推荐路径（如果不存在）
    if not recommended_path.exists():
        recommended_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {recommended_path}")
    
    # 更新配置文件
    config = {
        "mcp_servers": {
            "weixin_spider": {
                "command": "python",
                "args": ["src/mcp_weixin_spider/server.py"],
                "env": {
                    "ARTICLES_DIR": str(recommended_path.relative_to(Path(__file__).parent)),
                    "DOWNLOAD_IMAGES": "true",
                    "HEADLESS": "true",
                    "WAIT_TIME": "10"
                }
            }
        },
        "default_parameters": {
            "crawl_weixin_article": {
                "download_images": True,
                "custom_filename": None
            },
            "analyze_article_content": {
                "analysis_type": "full"
            }
        },
        "path_mappings": {
            "articles_directory": str(recommended_path.relative_to(Path(__file__).parent)),
            "legacy_paths": [
                "weixin_articles",
                "pythonSpider/articles"
            ]
        },
        "fix_info": {
            "fixed_at": str(Path(__file__).parent),
            "recommended_path": str(recommended_path),
            "existing_paths": path_results["existing_paths"]
        }
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置文件已更新: {config_file}")
        return True
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False

def test_crawl_function() -> bool:
    """测试爬取功能"""
    print("\n🧪 测试爬取功能...")
    
    try:
        # 导入爬虫模块
        import sys
        sys.path.append(str(Path(__file__).parent))
        
        from weixin_spider_simple import WeixinSpiderWithImages
        
        print("✅ 爬虫模块导入成功")
        
        # 测试参数验证
        test_url = "https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA"
        
        print(f"🔗 测试URL: {test_url[:50]}...")
        print("📋 测试参数:")
        print(f"   - download_images: True (默认值)")
        print(f"   - headless: True")
        print(f"   - wait_time: 10")
        
        # 检查ChromeDriver
        try:
            spider = WeixinSpiderWithImages(headless=True, wait_time=5, download_images=False)
            print("✅ ChromeDriver 初始化成功")
            spider.close()
            return True
        except Exception as e:
            print(f"❌ ChromeDriver 初始化失败: {e}")
            print("💡 建议: 运行 'webdriver-manager chrome --version' 重新下载驱动")
            return False
            
    except ImportError as e:
        print(f"❌ 导入爬虫模块失败: {e}")
        print("💡 建议: 检查依赖包是否安装完整")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def create_example_usage() -> None:
    """创建使用示例"""
    print("\n📝 创建使用示例...")
    
    example_file = Path(__file__).parent / "example_usage.py"
    
    example_code = '''#!/usr/bin/env python3
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
            print("\n分析结果:")
            print(json.dumps(analysis, ensure_ascii=False, indent=2))
        
        await client.disconnect()
        
    except Exception as e:
        print(f"MCP客户端示例失败: {e}")

if __name__ == "__main__":
    print("=== MCP微信爬虫使用示例 ===")
    
    print("\n1. 直接使用爬虫模块:")
    direct_crawl_example()
    
    print("\n2. 使用MCP客户端:")
    asyncio.run(mcp_client_example())
'''
    
    try:
        with open(example_file, 'w', encoding='utf-8') as f:
            f.write(example_code)
        print(f"✅ 示例文件已创建: {example_file}")
        print(f"💡 运行示例: python {example_file.name}")
    except Exception as e:
        print(f"❌ 创建示例文件失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="MCP微信爬虫快速修复工具")
    parser.add_argument("--check-paths", action="store_true", help="检查文章路径配置")
    parser.add_argument("--fix-config", action="store_true", help="修复MCP配置")
    parser.add_argument("--test-crawl", action="store_true", help="测试爬取功能")
    parser.add_argument("--create-example", action="store_true", help="创建使用示例")
    parser.add_argument("--all", action="store_true", help="执行所有修复操作")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("🚀 MCP微信爬虫快速修复工具")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    if args.check_paths or args.all:
        total_count += 1
        path_results = check_article_paths()
        if path_results["existing_paths"]:
            success_count += 1
    
    if args.fix_config or args.all:
        total_count += 1
        if fix_mcp_config():
            success_count += 1
    
    if args.test_crawl or args.all:
        total_count += 1
        if test_crawl_function():
            success_count += 1
    
    if args.create_example or args.all:
        total_count += 1
        create_example_usage()
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 修复完成: {success_count}/{total_count} 项成功")
    
    if success_count == total_count:
        print("✅ 所有问题已修复!")
        print("\n💡 接下来你可以:")
        print("   1. 使用修复后的配置重新运行智能体")
        print("   2. 运行 python example_usage.py 测试功能")
        print("   3. 查看 USAGE_GUIDE.md 了解详细使用方法")
    else:
        print("⚠️  部分问题需要手动处理")
        print("💡 请查看上面的错误信息并按提示操作")

if __name__ == "__main__":
    main()