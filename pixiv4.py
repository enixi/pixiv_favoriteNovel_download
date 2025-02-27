import os
import subprocess
import time
import random
import re
import sys
import json
import shutil
import tempfile
import importlib.util

# =================== 配置区 ===================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前文件夹
DOWNLOAD_PATH = os.path.join(CURRENT_DIR, "download_novels")  # 小说存放目录
CONFIG_PATH = os.path.join(CURRENT_DIR, "config.json") # 配置文件地址

DRIVER_PATH = '' # WebDriver 路径
browser_type = 2   # 1 为 edge , 2 为 chrome 

# 为应对pixiv反爬措施，每章下载前的等待时间区间
min_sleep_time , max_sleep_time = 1.5,2.5  


# 依赖库（模块名: PyPI包名）
required_modules = {
    'selenium': 'selenium',
    'webdriver_manager': 'webdriver-manager',
    'bs4': 'beautifulsoup4',
    'fake_useragent': 'fake-useragent',
    'requests': 'requests'
}

# =================== 安装依赖 ===================
def install_dependencies():
    """自动安装缺少的依赖"""
    try:
        for module_name, package_name in required_modules.items():
            if not package_installed(module_name):
                print(f"📦 正在安装依赖: {package_name}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)

def package_installed(package_name):
    """检查 Python 包是否已安装（按模块名检查）"""
    return importlib.util.find_spec(package_name) is not None

install_dependencies()  # 运行安装

# 依赖安装完成后，导入库
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

from webdriver_manager.chrome import ChromeDriverManager  
from selenium.webdriver.chrome.service import Service as ChromeService  
from selenium.webdriver.chrome.options import Options as ChromeOptions

def load_config():
    """从 config.json 读取保存的 WebDriver 路径和浏览器类型"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                saved_path = config.get("driver_path", "")
                saved_browser = config.get("browser_type", browser_type)
                if os.path.exists(saved_path):
                    return saved_path, saved_browser
    except json.JSONDecodeError:
        print(f"⚠️ 配置文件格式错误，将重新生成")
    except Exception as e:
        print(f"⚠️ 读取配置文件失败: {e}")
    return None

def save_config(driver_path, browser_type):
    """将 WebDriver 路径和浏览器类型写入 config.json"""
    try:
        config = {
            "driver_path": driver_path,
            "browser_type": browser_type
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        print(f"📁 配置已保存到: {CONFIG_PATH}")
    except Exception as e:
        print(f"⚠️ 保存配置文件失败: {e}")

def get_driver_path(saved_path):
    """检测本地可能的 WebDriver 路径"""
    possible_paths = [
        saved_path,  # 优先级1：配置文件中的路径
        shutil.which("chromedriver") if browser_type == 2 else shutil.which("msedgedriver"),  # 优先级2：环境变量
        os.path.join(CURRENT_DIR, "chromedriver.exe" if browser_type == 2 else "msedgedriver.exe"),  # 优先级3：当前目录
    ]
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    return None

def check_DRIVER_PATH(DRIVER_PATH):
    try:
        if browser_type == 2 and not DRIVER_PATH:
            DRIVER_PATH = ChromeDriverManager().install()
        elif browser_type == 1 and not DRIVER_PATH:
            DRIVER_PATH = EdgeChromiumDriverManager().install()
        print(f"✅ WebDriver 已安装: {DRIVER_PATH}")
        return DRIVER_PATH
    except Exception as e:
            print(f"❌ 无法安装 WebDriver: {e}")
            sys.exit(1)
    
# 辅助函数：清理文件名中的非法字符以及多余空白
def safe_filename(name):
    """
    替换掉 Windows 文件名中不允许的字符（\ / : * ? " < > |）为下划线，
    合并多余空格和下划线，并去除首尾空格和下划线。
    """
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'_+', '_', name)
    return name.strip(" _")

# =============================================

class PixivNovelCrawler:
    def __init__(self,COOKIE):
        self.cookie=COOKIE
        self.session = requests.Session()
        self.mode=1 # 1 为 单章 , 2 为 系列
        self.browser_type = 1 # 1 为 edge , 2 为 chrome 
        self.base_url = "https://www.pixiv.net"
        self.ua = UserAgent(fallback='Mozilla/5.0')
        self.headers = {'User-Agent': self.ua.random}
        self.base_headers={'User-Agent': 'Mozilla/5.0'}
        self.setup_session()
        # 记录已下载的系列，避免重复下载
        self.downloaded_series = set()

    def setmode(self,mode):
        self.mode=mode
    
    def set_browser_type(self,browser_type):
        self.browser_type=browser_type
    
    def setup_session(self):
        """设置 requests 会话的 Cookie"""
        for cookie_pair in self.cookie.split(';'):
            cookie_pair = cookie_pair.strip()
            if not cookie_pair or '=' not in cookie_pair:
                continue
            name, value = cookie_pair.split('=', 1)
            self.session.cookies.set(name, value)

    def get_all_favorites_ids(self, BASE_URL,start_page=1):
        """
        从指定页码开始爬取收藏夹中的小说 ID，并下载小说。
        如果返回空集合，则认为已到达最后一页，终止翻页下载。
        """
        novel_ids = set()
        page = start_page

        while True:
            url = BASE_URL.format(page=page)
            print(f"\n📄 正在爬取第 {page} 页: {url}")

            try:
                new_ids = self.get_favorites_ids_from_page(url, requested_page=page)
                if not new_ids:
                    print(f"✅ 第 {page} 页没有发现新的小说或已到达最后一页，爬取结束！")
                    break
            except Exception as e:
                print(f"⚠️ 爬取第 {page} 页时发生错误: {e}")
                break

            # 如果本页所有小说均已下载，则认为到达最后一页
            diff_ids = new_ids - novel_ids
            if not diff_ids:
                print(f"✅ 第 {page} 页所有小说均已下载，爬取结束！")
                break
            
            novel_ids.update(diff_ids)
            print(f"🔎 当前已发现 {len(novel_ids)} 本小说")

            for novel_id in diff_ids:
                self.crawl_novel(novel_id)
                sleep_time = random.uniform(min_sleep_time, max_sleep_time)
                print(f"⏳ 等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

            sleep_time = random.uniform(min_sleep_time, max_sleep_time)
            print(f"⏳ 等待 {sleep_time:.2f} 秒...")
            time.sleep(sleep_time)
            page += 1

        return novel_ids
    def _generate_random_headers(self):
        """生成包含随机 User-Agent 的 headers"""
        try:
            # 生成随机 User-Agent
            user_agent = self.ua.random
        except Exception as e:
            print(f"生成 User-Agent 失败: {e}, 使用默认值")
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        # 合并基础 headers 和随机 User-Agent
        headers = {**self.base_headers, "User-Agent": user_agent}
        return headers
    

    def get_favorites_ids_from_page(self, url, requested_page):
        """解析单页收藏夹，获取小说 ID，并判断是否达到最后一页"""
        if self.browser_type == 2:
            options = ChromeOptions()
            driver_path = DRIVER_PATH
            service = ChromeService(driver_path)
        else:
            options = Options()
            driver_path = DRIVER_PATH
            service = Service(driver_path)
        
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--log-level=3")  # 0: 默认, 1: 警告, 2: 信息, 3: 错误


        # 生成唯一的临时用户目录，避免多个 WebDriver 占用
        temp_user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={temp_user_data_dir}")

        service = Service(DRIVER_PATH)

        try:
            driver = webdriver.Chrome(service=service, options=options) if self.browser_type == "chrome" \
                else webdriver.Edge(service=service, options=options)
            driver.get("https://www.pixiv.net")
            time.sleep(2)
            
            for cookie_pair in self.cookie.split(';'):
                cookie_pair = cookie_pair.strip()
                if not cookie_pair or '=' not in cookie_pair:
                    continue
                name, value = cookie_pair.split('=', 1)
                driver.add_cookie({"name": name, "value": value, "domain": ".pixiv.net"})

            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/novel/show.php?id=']"))
            )

            for _ in range(random.randint(4, 5)):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1.5, 3))

            page_source = driver.page_source

        except Exception as e:
            print(f"❌ 页面加载或滚动过程中出错: {e}")
            return set()
        
        finally:
            driver.quit()  # 关闭 WebDriver，避免进程残留
            shutil.rmtree(temp_user_data_dir, ignore_errors=True)  # 删除临时用户目录

        soup = BeautifulSoup(page_source, 'html.parser')

        ids = set()
        for a in soup.find_all('a', href=True):
            if "/novel/show.php?id=" in a['href']:
                match = re.search(r'id=(\d+)', a['href'])
                if match:
                    ids.add(match.group(1))

        page_param = url.split('=')[-1]
        print(f"📖 第 {page_param} 页找到 {len(ids)} 本小说")
        return ids

    def crawl_novel(self, novel_id):
        """下载单篇小说"""
        self.headers = self._generate_random_headers()
        novel_url = f"{self.base_url}/ajax/novel/{novel_id}"
        response = self.session.get(novel_url, headers=self.headers)
        if response.status_code != 200:
            print(f"⚠️ 获取小说 {novel_id} 失败")
            return

        novel_data = response.json().get('body', {})
        if not novel_data:
            print(f"⚠️ 小说 {novel_id} 数据解析失败")
            return
        
        # 检查文章是否属于某个系列
        if self.mode==2:
            series_nav_data = novel_data.get('seriesNavData') or {}
            series_id = series_nav_data.get('seriesId')
        else: 
            series_id=''
        
        if series_id:
            self.crawl_series(series_id)
            return  # 不继续处理单篇
        
        # 提取元数据
        metadata = {
            "标题": novel_data.get('title', '无标题').strip(),
            "作者": novel_data.get('userName', '未知作者').strip(),
            "上传时间": novel_data.get('uploadDate', '未知日期'),
            "标签": [tag.get('tag', '') for tag in novel_data.get('tags', {}).get('tags', [])],
            "描述": novel_data.get('description', '无描述').replace("<br />", "\n").strip(),
            "原文网址": f"{self.base_url}/novel/show.php?id={novel_id}"
        }
        content = novel_data.get('content', '')

        # 生成安全文件名（对作者和标题都进行清理）
        safe_author = safe_filename(metadata["作者"])
        safe_title = safe_filename(metadata["标题"])
        file_name = os.path.join(DOWNLOAD_PATH, f"[{safe_author}]{safe_title}.txt")
        
        metadata_str = self._format_metadata(metadata)
        full_content = f"{metadata_str}{content}"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"✅ 小说 {safe_title} 下载完成！")



    def _format_metadata(self, metadata):
        """格式化元数据为文本块"""
        metadata_lines = [
            f"标题: {metadata['标题']}",
            f"作者: {metadata['作者']}",
            f"标签: {', '.join(metadata['标签'])}",
            f"上传时间: {metadata['上传时间']}",
            f"原文网址: {metadata['原文网址']}",
            f"简介:\n{metadata['描述']}".rstrip(),
            "\n" + "="*20 + "\n\n"
        ]
        return '\n'.join(metadata_lines)

    def crawl_series(self, series_id):
        """系列处理方法"""
        # 如果系列已下载，则跳过
        if series_id in self.downloaded_series:
            print(f"✅ 系列 {series_id} 已下载，跳过...")
            return  # 避免重复下载同一系列
        
        self.downloaded_series.add(series_id)  # 标记已下载
        
        # 获取系列元数据
        time.sleep(random.uniform(min_sleep_time, max_sleep_time))  # 降低请求频率
        series_info = self._get_series_info(series_id)
        if not series_info or not series_info['chapters']:
            return

        # 收集章节内容
        chap_num=1
        for chap in series_info['chapters']:
            print(f"⏳ 已下载系列 {chap_num}/{series_info['total']} 章", end="\r")
            chap['content'] = self._get_chapter_text(chap['id'])
            chap_num+=1
            time.sleep(random.uniform(min_sleep_time, max_sleep_time))
            
        # 合并保存
        self._save_combined_series(series_info)

    def _get_series_info(self, series_id):
        self.headers = self._generate_random_headers()
        """获取系列基础元数据"""
        info_url = f"{self.base_url}/ajax/novel/series/{series_id}"
        try:
            response = self.session.get(info_url, headers=self.headers)
            if response.status_code != 200:
                return None
            data = response.json().get('body', {})
            
            series_info = {
                'title': data.get('title', '无标题').strip(),
                'author': data.get('userName', '未知作者').strip(),
                'url':f"{self.base_url}/novel/series/{series_id}",
                'desc': data.get('caption', '无简介').replace("<br />", "\n").strip(),
                'total': data.get('total', 0),
                'tags': data.get('tags', []),
                'chapters': []
            }
        except Exception as e:
            print(f"⚠️ 获取系列信息失败: {e}")
            return None
        
        print(f"📚 检测到系列 {series_info['title']} ，开始处理")
        # 分页获取章节元数据
        self.headers = self._generate_random_headers()
        limit = 30  # Pixiv 每页固定返回30条
        last_order = 0
        while last_order < series_info['total']:
            content_url = f"{self.base_url}/ajax/novel/series_content/{series_id}"
            params = {
                'limit': limit,
                'last_order': last_order,
                'order_by': 'asc'
            }
            try:
                content_res = self.session.get(content_url, params=params, headers=self.headers)
                content_data = content_res.json().get('body', {}).get('page', {}).get('seriesContents', [])
                
                # 解析章节数据
                for item in content_data:
                    series_info['chapters'].append({
                        'id': item['id'],
                        'title': item['title'],
                        'comment': item['commentHtml'].replace("<br />", "\n"),
                        'order': int(item['series']['contentOrder']),
                        'content':''
                    })
                
                last_order += len(content_data)
                time.sleep(random.uniform(min_sleep_time, max_sleep_time))  # 降低请求频率
                
                # Pixiv 实际可能返回少于limit的情况
                if len(content_data) < limit:
                    break
                    
            except Exception as e:
                print(f"⚠️ 获取章节列表失败: {e}")
                break    
        # 按order排序章节
        series_info['chapters'].sort(key=lambda x: x['order'])
        return series_info            

    def _get_chapter_text(self, novel_id):
        """获取章节正文"""
        self.headers = self._generate_random_headers()
        url = f"{self.base_url}/ajax/novel/{novel_id}"
        try:
            response = self.session.get(url, headers=self.headers)
            return response.json().get('body', {}).get('content', '')
        except:
            return "【章节内容加载失败】"

    def _save_combined_series(self, series_info):
        """合并保存文件"""
        # 生成文件名
        safe_author = safe_filename(series_info['author'])
        safe_title = safe_filename(series_info['title'])
        filename = f"[{safe_author}]{safe_title}.txt"
        filepath = os.path.join(DOWNLOAD_PATH, filename)
        
        if series_info['total']>1:
            series_title=f"标题：{series_info['title']} (1~{series_info['total']})"

        else:
            series_title=f"标题：{series_info['title']}"

        # 构建文件头
        header = [
            series_title,
            f"作者：{series_info['author']}",
            f"标签：{', '.join(series_info['tags'])}",
            f"原文网址: {series_info['url']}",
            f"简介：\n{series_info['desc']}".rstrip(),
        ]

        # 按章节顺序写入
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header))
            for chap in series_info['chapters']:
                if chap['comment']!='':
                    comment=f"作者的话：\n\n" + "-"*10 + f"\n\n{chap['comment']}".rstrip() + f'\n\n'+"-"*10+f'\n'
                else:
                    comment=''
                chapter_content = [
                    "\n\n" + "="*20 + "\n",
                    f"{chap['title']}".rstrip()+f'\n',
                    comment,
                    chap['content'].rstrip()+f'\n'
                ]
                f.write('\n'.join(chapter_content))

        print(f"✅ 已保存系列 {series_info['title']} ，共 {series_info['total']} 章")


def main():
    global DOWNLOAD_PATH,CONFIG_PATH,DRIVER_PATH,browser_type
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    
    # 获取 web_driver 
    if os.path.exists(CONFIG_PATH):
        saved_path,browser_type=load_config()
    else:
        print(f"\n检测到此次为初次运行，请选择拥有的浏览器 : \n类型 1: edge\n类型 2: chrome")
        browser_type=input("请输入浏览器类型（默认为 1 ） ").strip()
        browser_type = int(browser_type) if browser_type.isdigit() else 1
        saved_path=''
    
    DRIVER_PATH = get_driver_path(saved_path)
    DRIVER_PATH = check_DRIVER_PATH(DRIVER_PATH)
    save_config(DRIVER_PATH, browser_type)
        
    # 选择模式
    print(f"\n请选择下载模式 : \n模式 1: 按单章下载\n模式 2: 按系列下载")
    mode=input("请输入选择的下载模式（默认为 1 ） ").strip()
    mode = int(mode) if mode.isdigit() else 1

    
    # 让用户输入 COOKIE
    COOKIE = input("请粘贴你的 Pixiv COOKIE: ").strip()

    # 自动提取 USER_ID
    match = re.search(r"user_id=(\d+)", COOKIE)
    if match:
        USER_ID = match.group(1)
        print(f"🔍 从 COOKIE 中提取到 USER_ID: {USER_ID}")
    else:
        print(f"❌ 无法从 COOKIE 中获取 USER_ID，请检查你的 COOKIE。")
        sys.exit(1)
    

    # 让用户输入起始页码
    start_page = input("请输入爬取的起始页码（默认为 1 ）: ").strip()
    start_page = int(start_page) if start_page.isdigit() else 1

    BASE_URL = f"https://www.pixiv.net/users/{USER_ID}/bookmarks/novels?p={{page}}"
    crawler = PixivNovelCrawler(COOKIE)
    crawler.setmode(mode)
    crawler.set_browser_type(browser_type)
    crawler.get_all_favorites_ids(BASE_URL,start_page)

if __name__ == "__main__":
    main()

