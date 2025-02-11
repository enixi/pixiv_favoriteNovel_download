import os
import time
import random
import requests
import re
import sys
import shutil

# =================== 安装依赖 ===================
def install_dependencies():
    """自动安装缺少的依赖"""
    try:
        import pip
        required_packages = ["selenium", "webdriver-manager", "beautifulsoup4", "requests"]
        for package in required_packages:
            if not package_installed(package):
                print(f"📦 正在安装依赖: {package}...")
                pip.main(['install', package])
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)

def package_installed(package_name):
    """检查 Python 包是否已安装"""
    import importlib.util
    return importlib.util.find_spec(package_name) is not None

install_dependencies()  # 运行安装

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# 依赖安装完成后，导入库
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# =================== 配置区 ===================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前文件夹
DOWNLOAD_PATH = os.path.join(CURRENT_DIR, "download_novels")  # 小说存放目录
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# 让用户输入 COOKIE
COOKIE = input("请粘贴你的 Pixiv COOKIE: ").strip()

# 自动提取 USER_ID
match = re.search(r"user_id=(\d+)", COOKIE)
if match:
    USER_ID = match.group(1)
    print(f"🔍 从 COOKIE 中提取到 USER_ID: {USER_ID}")
else:
    print("❌ 无法从 COOKIE 中获取 USER_ID，请检查你的 COOKIE。")
    sys.exit(1)

# 让用户输入起始页码
start_page = input("请输入起始页码（如 1 或 51 继续爬取）: ").strip()
start_page = int(start_page) if start_page.isdigit() else 1

BASE_URL = f"https://www.pixiv.net/users/{USER_ID}/bookmarks/novels?p={{page}}"

# 自动检测 WebDriver
def get_edge_driver_path():
    """尝试获取 Edge WebDriver 路径"""
    possible_paths = [
        shutil.which("msedgedriver"),  # 在系统环境变量中查找
        os.path.join(CURRENT_DIR, "msedgedriver.exe"),  # 当前目录
    ]
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    return None

EDGE_DRIVER_PATH = get_edge_driver_path()

if not EDGE_DRIVER_PATH:
    try:
        # 自动下载安装 WebDriver
        EDGE_DRIVER_PATH = EdgeChromiumDriverManager().install()
        print(f"✅ WebDriver 已安装: {EDGE_DRIVER_PATH}")
    except Exception as e:
        print(f"❌ 无法安装 WebDriver: {e}")
        sys.exit(1)
else:
    print(f"✅ 使用本地 WebDriver: {EDGE_DRIVER_PATH}")

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
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.pixiv.net"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.setup_session()

    def setup_session(self):
        """设置 requests 会话的 Cookie"""
        for cookie_pair in COOKIE.split(';'):
            cookie_pair = cookie_pair.strip()
            if not cookie_pair or '=' not in cookie_pair:
                continue
            name, value = cookie_pair.split('=', 1)
            self.session.cookies.set(name, value)

    def get_all_favorites_ids(self, start_page=1):
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
                sleep_time = random.uniform(1, 5)
                print(f"⏳ 等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

            sleep_time = random.uniform(2, 5)
            print(f"⏳ 等待 {sleep_time:.2f} 秒...")
            time.sleep(sleep_time)
            page += 1

        return novel_ids

    def get_favorites_ids_from_page(self, url, requested_page):
        """解析单页收藏夹，获取小说 ID，并判断是否达到最后一页"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=msAccountSSO,msWelcomePage")

        service = Service(EDGE_DRIVER_PATH)
        driver = webdriver.Edge(service=service, options=options)
        try:
            driver.get("https://www.pixiv.net")
            time.sleep(3)
            for cookie_pair in COOKIE.split(';'):
                cookie_pair = cookie_pair.strip()
                if not cookie_pair or '=' not in cookie_pair:
                    continue
                name, value = cookie_pair.split('=', 1)
                driver.add_cookie({"name": name, "value": value, "domain": ".pixiv.net"})

            driver.get(url)
            # 判断是否自动跳转回最后一页
            current_url = driver.current_url
            match_current = re.search(r'p=(\d+)', current_url)
            if match_current:
                actual_page = int(match_current.group(1))
                if actual_page < requested_page:
                    print(f"已到达最后一页：请求页 {requested_page}，当前页 {actual_page}")
                    driver.quit()
                    return set()
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/novel/show.php?id=']"))
            )
            for _ in range(random.randint(5, 10)):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 3))
            page_source = driver.page_source
        except Exception as e:
            print(f"❌ 页面加载或滚动过程中出错: {e}")
            driver.quit()
            return set()
        driver.quit()
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
        novel_url_ajax = f"{self.base_url}/ajax/novel/{novel_id}"
        response = self.session.get(novel_url_ajax, headers=self.headers)
        if response.status_code != 200:
            print(f"⚠️ 获取小说 {novel_id} 失败")
            return

        novel_data = response.json().get('body', {})
        if not novel_data:
            print(f"⚠️ 小说 {novel_id} 数据解析失败")
            return

        title = novel_data.get('title', '无标题')
        # 构造小说展示页面 URL
        novel_url_show = f"{self.base_url}/novel/show.php?id={novel_id}"
        
        # 提取元数据
        metadata = {
            "标题": novel_data.get('title', '无标题').strip(),
            "作者": novel_data.get('userName', '未知作者').strip(),
            "上传时间": novel_data.get('uploadDate', '未知日期'),
            "标签": [tag.get('tag', '') for tag in novel_data.get('tags', {}).get('tags', [])],
            "描述": novel_data.get('description', '无描述').replace("<br />", "\n").strip(),
            "小说网址": novel_url_show
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

        print(f"✅ 小说 {title} 下载完成！")

    def _format_metadata(self, metadata):
        """格式化元数据为文本块，将小说网址插入在上传时间之后"""
        metadata_lines = [
            f"标题: {metadata['标题']}",
            f"作者: {metadata['作者']}",
            f"标签: {', '.join(metadata['标签'])}",
            f"上传时间: {metadata['上传时间']}",
            f"小说网址: {metadata['小说网址']}",
            f"简介: {metadata['描述']}",
            "\n----------\n\n"
        ]
        return '\n'.join(metadata_lines)

def main():
    crawler = PixivNovelCrawler()
    crawler.get_all_favorites_ids(start_page=start_page)

if __name__ == "__main__":
    main()
