#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫 - 参考pythonSpider实现的完整版本
支持文章内容抓取、图片下载、多种格式保存
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import os
import logging
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
import hashlib
from pathlib import Path
import sys
import shutil
import subprocess
import base64
from urllib.parse import unquote

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeixinSpiderWithImages:
    def __init__(self, headless=True, wait_time=10, download_images=True):
        """
        初始化爬虫
        :param headless: 是否使用无头模式
        :param wait_time: 页面等待时间
        :param download_images: 是否下载图片
        """
        self.driver = None
        self.wait_time = wait_time
        self.download_images = download_images
        self.session = requests.Session()
        self.setup_session()
        self.setup_driver(headless)
        
    def setup_session(self):
        """设置requests会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def find_chromedriver_path(self):
        """查找系统中的ChromeDriver路径"""
        # 常见的ChromeDriver路径
        possible_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/opt/homebrew/bin/chromedriver',
            shutil.which('chromedriver'),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"找到ChromeDriver: {path}")
                return path
        
        # 尝试通过brew安装
        try:
            result = subprocess.run(['brew', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("检测到Homebrew，尝试安装ChromeDriver...")
                subprocess.run(['brew', 'install', 'chromedriver'], check=True)
                chromedriver_path = shutil.which('chromedriver')
                if chromedriver_path:
                    return chromedriver_path
        except Exception as e:
            logger.warning(f"通过Homebrew安装ChromeDriver失败: {e}")
        
        return None
        
    def setup_driver(self, headless=True):
        """设置Chrome浏览器驱动"""
        try:
            logger.info("正在设置Chrome浏览器驱动...")
            
            options = Options()
            
            if headless:
                options.add_argument('--headless')  # 使用传统headless模式
                logger.info("使用无头模式")
            
            # 基本设置 - 针对版本兼容性和渲染器连接问题优化
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-logging')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-hang-monitor')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-prompt-on-repost')
            options.add_argument('--disable-sync')
            options.add_argument('--no-first-run')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-component-update')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 解决渲染器连接问题的关键参数
            options.add_argument('--single-process')  # 使用单进程模式
            options.add_argument('--disable-gpu-sandbox')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--remote-debugging-port=0')  # 禁用远程调试端口
            options.add_argument('--disable-dev-tools')
            
            # 内存和性能优化
            options.add_argument('--memory-pressure-off')
            options.add_argument('--max_old_space_size=4096')
            
            # 设置用户代理 - 更新到最新版本
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
            
            # 排除自动化标识
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 设置prefs以避免各种弹窗
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 2,
                    "media_stream": 2,
                },
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2 if not self.download_images else 1
            }
            options.add_experimental_option("prefs", prefs)
            
            # 优先尝试使用系统ChromeDriver
            try:
                logger.info("尝试使用系统ChromeDriver...")
                # 检查ChromeDriver路径
                chromedriver_path = shutil.which('chromedriver')
                if chromedriver_path:
                    logger.info(f"找到ChromeDriver路径: {chromedriver_path}")
                    service = Service(chromedriver_path)
                    self.driver = webdriver.Chrome(service=service, options=options)
                    logger.info("使用系统ChromeDriver成功初始化")
                else:
                    raise Exception("未找到系统ChromeDriver")
            except Exception as system_error:
                logger.warning(f"系统ChromeDriver失败: {system_error}")
                try:
                    logger.info("使用webdriver-manager自动下载兼容的ChromeDriver...")
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    logger.info("使用webdriver-manager成功初始化ChromeDriver")
                except Exception as wdm_error:
                    logger.error(f"webdriver-manager失败: {wdm_error}")
                    # 最后尝试不指定service
                    try:
                        logger.info("尝试使用默认ChromeDriver配置...")
                        self.driver = webdriver.Chrome(options=options)
                        logger.info("使用默认配置成功初始化ChromeDriver")
                    except Exception as default_error:
                        logger.error(f"默认配置也失败: {default_error}")
                        raise RuntimeError(f"所有ChromeDriver初始化方法都失败: {default_error}")
            
            # 执行脚本隐藏webdriver属性
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']})")
            except Exception as script_error:
                logger.warning(f"执行隐藏脚本失败: {script_error}")
            
            # 设置窗口大小
            try:
                self.driver.set_window_size(1920, 1080)
            except Exception as window_error:
                logger.warning(f"设置窗口大小失败: {window_error}")
            
            logger.info("Chrome浏览器驱动设置完成")
            
        except Exception as e:
            logger.error(f"设置浏览器驱动失败: {str(e)}")
            # 提供备用方案
            self.driver = None
            raise RuntimeError(f"无法初始化Chrome浏览器驱动: {e}")
    
    def crawl_article_by_url(self, url, retry_times=3):
        """通过URL抓取文章内容，支持重试"""
        if not self.driver:
            raise RuntimeError("浏览器驱动未初始化")
            
        for attempt in range(retry_times):
            try:
                logger.info(f"第 {attempt + 1} 次尝试访问文章: {url}")
                
                # 访问页面
                self.driver.get(url)
                
                # 等待页面加载
                wait = WebDriverWait(self.driver, self.wait_time)
                
                # 等待文章标题加载
                try:
                    title_element = wait.until(
                        EC.presence_of_element_located((By.ID, "activity-name"))
                    )
                except:
                    # 尝试其他可能的标题元素
                    title_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .rich_media_title, #js_title"))
                    )
                
                # 滚动页面确保内容完全加载
                self._scroll_page()
                
                # 提取文章信息
                article_data = self._extract_article_content()
                
                if article_data and article_data.get('title'):
                    logger.info(f"成功抓取文章: {article_data['title']}")
                    return article_data
                else:
                    logger.warning(f"第 {attempt + 1} 次尝试未能获取完整文章内容")
                    
            except Exception as e:
                logger.error(f"第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt == retry_times - 1:
                    raise
                time.sleep(2)
        
        raise Exception("所有重试都失败了")
    
    def _scroll_page(self):
        """滚动页面以加载所有内容"""
        try:
            # 获取页面高度
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 等待新内容加载
                time.sleep(2)
                
                # 计算新的页面高度
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
            # 滚动回顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"滚动页面时出错: {e}")
    
    def _extract_article_content(self):
        """提取文章内容"""
        try:
            article_data = {}
            
            # 获取文章标题 - 尝试多种选择器
            title_selectors = [
                "#activity-name",
                ".rich_media_title",
                "#js_title",
                "h1",
                "[class*='title']"
            ]
            
            title = self._get_text_by_selectors(title_selectors, "未知标题")
            article_data['title'] = title.strip()
            logger.info(f"提取到标题: {title}")
            
            # 获取作者信息
            author_selectors = [
                "#js_name",
                ".rich_media_meta_text",
                "[class*='author']",
                "[id*='author']"
            ]
            author = self._get_text_by_selectors(author_selectors, "未知作者")
            article_data['author'] = author.strip()
            
            # 获取发布时间
            time_selectors = [
                "#publish_time",
                ".rich_media_meta_text",
                "[class*='time']",
                "[id*='time']"
            ]
            publish_time = self._get_text_by_selectors(time_selectors, "未知时间")
            article_data['publish_time'] = publish_time.strip()
            
            # 获取文章正文内容
            content_selectors = [
                "#js_content",
                ".rich_media_content",
                "[class*='content']",
                "article"
            ]
            
            content_element = self._get_element_by_selectors(content_selectors)
            
            if content_element:
                # 获取HTML内容
                content_html = content_element.get_attribute('innerHTML')
                article_data['content_html'] = content_html
                
                # 提取图片信息
                if self.download_images:
                    images_info = self._extract_images_from_content(content_element)
                    article_data['images'] = images_info
                    logger.info(f"发现 {len(images_info)} 张图片")
                
                # 使用BeautifulSoup解析HTML，提取纯文本
                soup = BeautifulSoup(content_html, 'html.parser')
                
                # 移除脚本和样式标签
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content_text = soup.get_text(separator='\n', strip=True)
                article_data['content_text'] = content_text
                
                logger.info(f"提取到内容长度: {len(content_text)} 字符")
            else:
                logger.warning("未能找到文章正文内容")
                article_data['content_html'] = ""
                article_data['content_text'] = ""
                article_data['images'] = []
            
            # 获取当前URL
            article_data['url'] = self.driver.current_url
            article_data['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return article_data
            
        except Exception as e:
            logger.error(f"提取文章内容失败: {str(e)}")
            return None
    
    def _extract_images_from_content(self, content_element):
        """从内容中提取图片信息"""
        images_info = []
        
        try:
            # 查找所有图片元素
            img_elements = content_element.find_elements(By.TAG_NAME, "img")
            
            for i, img in enumerate(img_elements):
                try:
                    # 获取图片URL - 优先使用data-src（微信文章的真实图片链接）
                    img_url = img.get_attribute('data-src') or img.get_attribute('src')
                    
                    if not img_url:
                        continue
                    
                    # 处理相对URL
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(self.driver.current_url, img_url)
                    
                    # 获取图片其他属性
                    alt_text = img.get_attribute('alt') or f"图片_{i+1}"
                    title_text = img.get_attribute('title') or ""
                    
                    image_info = {
                        'index': i + 1,
                        'url': img_url,
                        'alt': alt_text,
                        'title': title_text,
                        'filename': None,  # 将在下载时设置
                        'local_path': None,  # 将在下载时设置
                        'download_success': False
                    }
                    
                    images_info.append(image_info)
                    
                except Exception as e:
                    logger.warning(f"处理第 {i+1} 张图片时出错: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"提取图片信息失败: {str(e)}")
        
        return images_info
    
    def _get_text_by_selectors(self, selectors, default=""):
        """通过多个选择器尝试获取文本"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except:
                continue
        return default
    
    def _get_element_by_selectors(self, selectors):
        """通过多个选择器尝试获取元素"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue
        return None
    
    def _download_image(self, img_url, save_dir, filename_prefix="img"):
        """下载单张图片并转换为PNG格式"""
        try:
            # 处理 data: URL (内联图片)
            if img_url.startswith('data:'):
                return self._save_data_url_image_as_png(img_url, save_dir, filename_prefix)
            
            # 发送请求下载图片
            response = self.session.get(img_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 生成PNG文件名（使用前缀，确保唯一性）
            filename = f"{filename_prefix}.png"
            filepath = os.path.join(save_dir, filename)
            
            # 先保存原始文件到临时位置
            temp_filepath = filepath + ".temp"
            with open(temp_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 转换为PNG格式
            try:
                from PIL import Image
                # 打开图片并转换为PNG
                with Image.open(temp_filepath) as img:
                    # 如果是RGBA模式，保持透明度；否则转换为RGB
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')
                    img.save(filepath, 'PNG')
                
                # 删除临时文件
                os.remove(temp_filepath)
                
                logger.info(f"图片下载并转换为PNG成功: {filename}")
                return filename, filepath
                
            except Exception as convert_error:
                # 如果转换失败，保留原始文件但重命名为PNG
                logger.warning(f"图片转换失败，保存原始文件: {str(convert_error)}")
                os.rename(temp_filepath, filepath)
                return filename, filepath
            
        except Exception as e:
            logger.error(f"下载图片失败 {img_url}: {str(e)}")
            return None, None
    
    def _save_data_url_image_as_png(self, data_url, save_dir, filename_prefix="img"):
        """保存 data: URL 格式的内联图片并转换为PNG"""
        try:
            # 解析 data URL
            if not data_url.startswith('data:'):
                return None, None
            
            # 移除 'data:' 前缀
            data_part = data_url[5:]
            
            # 分离媒体类型和数据
            if ',' not in data_part:
                return None, None
            
            header, data = data_part.split(',', 1)
            
            # 解析媒体类型和编码
            if ';base64' in header:
                # Base64 编码的数据
                media_type = header.replace(';base64', '')
                try:
                    image_data = base64.b64decode(data)
                except Exception:
                    logger.warning(f"Base64解码失败: {data_url[:100]}...")
                    return None, None
            else:
                # URL编码的数据 (如SVG)
                media_type = header
                try:
                    image_data = unquote(data).encode('utf-8')
                except Exception:
                    logger.warning(f"URL解码失败: {data_url[:100]}...")
                    return None, None
            
            # 生成PNG文件名
            filename = f"{filename_prefix}.png"
            filepath = os.path.join(save_dir, filename)
            
            # 处理不同格式
            try:
                from PIL import Image
                import io
                
                # 从字节数据创建图片
                img = Image.open(io.BytesIO(image_data))
                
                # 转换为PNG格式
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                img.save(filepath, 'PNG')
                logger.info(f"内联图片转换为PNG成功: {filename}")
                
            except Exception:
                # 如果转换失败，直接保存原始数据
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                logger.info(f"内联图片保存为PNG文件名: {filename}")
            
            return filename, filepath
            
        except Exception as e:
            logger.error(f"保存内联图片失败: {str(e)}")
            return None, None
    
    def _download_all_images(self, images_info, save_dir):
        """下载所有图片"""
        if not images_info:
            return
        
        # 创建图片保存目录
        images_dir = os.path.join(save_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        logger.info(f"开始下载 {len(images_info)} 张图片...")
        
        for img_info in images_info:
            try:
                filename, filepath = self._download_image(
                    img_info['url'], 
                    images_dir, 
                    f"img_{img_info['index']:03d}"
                )
                
                if filename and filepath:
                    img_info['filename'] = filename
                    img_info['local_path'] = filepath
                    img_info['download_success'] = True
                else:
                    img_info['download_success'] = False
                
                # 添加延时避免请求过快
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"下载图片 {img_info['url']} 时出错: {str(e)}")
                img_info['download_success'] = False
        
        success_count = sum(1 for img in images_info if img['download_success'])
        logger.info(f"图片下载完成: {success_count}/{len(images_info)} 张成功")
    
    def save_article_to_file(self, article_data, custom_filename=None):
        """保存文章到文件"""
        if not article_data:
            logger.warning("没有文章数据可保存")
            return False
        
        try:
            # 创建保存目录
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles")
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成安全的文件名
            if custom_filename:
                safe_filename = custom_filename
            else:
                title = article_data.get('title', '未知标题')
                # 移除文件名中的非法字符
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                safe_title = safe_title[:50]  # 限制长度
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{safe_title}_{timestamp}"
            
            # 创建文章专用目录
            article_dir = os.path.join(save_dir, safe_filename)
            os.makedirs(article_dir, exist_ok=True)
            
            # 下载图片
            if self.download_images and article_data.get('images'):
                self._download_all_images(article_data['images'], article_dir)
            
            # 保存JSON格式
            json_filepath = os.path.join(article_dir, f"{safe_filename}.json")
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON文件已保存: {json_filepath}")
            
            # 保存TXT格式
            txt_filepath = os.path.join(article_dir, f"{safe_filename}.txt")
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"标题: {article_data.get('title', '')}\n")
                f.write(f"作者: {article_data.get('author', '')}\n")
                f.write(f"发布时间: {article_data.get('publish_time', '')}\n")
                f.write(f"抓取时间: {article_data.get('crawl_time', '')}\n")
                f.write(f"链接: {article_data.get('url', '')}\n")
                f.write("\n" + "="*80 + "\n\n")
                f.write(article_data.get('content_text', ''))
                
                # 添加图片信息
                if article_data.get('images'):
                    f.write("\n\n" + "="*80 + "\n")
                    f.write("图片信息:\n")
                    for img in article_data['images']:
                        f.write(f"\n图片 {img['index']}: {img['alt']}\n")
                        f.write(f"原始URL: {img['url']}\n")
                        if img['download_success']:
                            f.write(f"本地文件: {img['filename']}\n")
                        else:
                            f.write("下载失败\n")
            
            logger.info(f"TXT文件已保存: {txt_filepath}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return False
    
    def close(self):
        """关闭浏览器和会话"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {str(e)}")
        
        if self.session:
            try:
                self.session.close()
                logger.info("网络会话已关闭")
            except Exception as e:
                logger.error(f"关闭网络会话时出错: {str(e)}")
    
    def __del__(self):
        """析构函数 - 不自动关闭驱动，避免意外关闭"""
        # 注释掉自动关闭，避免在不合适的时机关闭驱动
        # self.close()
        pass

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = {
        'selenium': 'selenium',
        'beautifulsoup4': 'bs4',
        'requests': 'requests',
        'webdriver_manager': 'webdriver_manager',
        'Pillow': 'PIL'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"✅ {package_name} 已安装")
        except ImportError:
            missing_packages.append(package_name)
            logger.error(f"❌ {package_name} 未安装")
    
    if missing_packages:
        logger.error(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install selenium beautifulsoup4 requests webdriver-manager Pillow")
        return False
    
    logger.info("✅ 所有依赖包都已安装")
    return True


def test_spider_with_images():
    """测试爬虫功能（包含图片下载）"""
    # 测试URL列表
    test_urls = [
        "https://mp.weixin.qq.com/s/KJl2oTMaKRra2l0PV7IIiA",  # 目标文章
        # 可以添加更多测试URL
    ]
    
    spider = None
    
    try:
        logger.info("开始测试微信公众号爬虫（包含图片下载）...")
        
        # 创建爬虫实例
        spider = WeixinSpiderWithImages(headless=False, wait_time=10, download_images=True)
        
        for i, url in enumerate(test_urls, 1):
            logger.info(f"\n=== 测试第 {i} 个URL ===")
            logger.info(f"URL: {url}")
            
            # 抓取文章
            article_data = spider.crawl_article_by_url(url)
            
            if article_data:
                logger.info("✅ 抓取成功")
                logger.info(f"标题: {article_data.get('title', 'N/A')}")
                logger.info(f"作者: {article_data.get('author', 'N/A')}")
                logger.info(f"发布时间: {article_data.get('publish_time', 'N/A')}")
                logger.info(f"内容长度: {len(article_data.get('content_text', ''))} 字符")
                logger.info(f"图片数量: {len(article_data.get('images', []))} 张")
                
                # 显示图片信息
                images = article_data.get('images', [])
                if images:
                    logger.info("\n📷 图片信息:")
                    for img in images:
                        logger.info(f"  图片 {img['index']}: {img['alt']}")
                        logger.info(f"    URL: {img['url'][:80]}...")
                
                # 保存文章
                if spider.save_article_to_file(article_data, f"test_with_images_{i}"):
                    logger.info("✅ 文章和图片保存成功")
                    
                    # 统计下载成功的图片
                    if images:
                        success_count = sum(1 for img in images if img.get('download_success', False))
                        logger.info(f"📊 图片下载统计: {success_count}/{len(images)} 张成功")
                else:
                    logger.error("❌ 文章保存失败")
            else:
                logger.error("❌ 抓取失败")
            
            # 如果有多个URL，添加延时
            if i < len(test_urls):
                logger.info("等待5秒后继续下一个测试...")
                time.sleep(5)
        
        logger.info("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
    finally:
        if spider:
            spider.close()


def main():
    """主函数"""
    logger.info("=== 微信公众号爬虫测试程序（支持图片下载）===")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 运行测试
    test_spider_with_images()


if __name__ == "__main__":
    main()