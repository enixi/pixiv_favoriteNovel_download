# 📖 Pixiv Favorite Novel Download

这是一个用于 **批量下载 Pixiv 收藏小说** 的 Python 爬虫脚本。
注：请先确保开启了全局vpn，下载了edge浏览器。

---
## ✨ 功能特点
✅ **自动爬取** Pixiv 收藏夹中的小说  
✅ **支持无头浏览器** Edge 自动适配 (safari/chrome暂时不支持) 

✅ **自动解析小说信息**（标题、作者、上传时间、标签等）  
✅ **仅支持 Windows**  

---
## 🛠️ 环境安装
### **1️⃣ 安装 Python**
请确保你安装了 **Python 3.8+**，如果没有，请先从 [Python 官网](https://www.python.org/) 下载并安装。

### **2️⃣ 安装依赖**
首次运行时，脚本会自动安装所需的 Python 依赖项：
```bash
pip install -r requirements.txt
```
如果没有 `requirements.txt`，可以手动安装：
```bash
pip install selenium webdriver-manager beautifulsoup4 requests
```

---
## 🚀 使用方法
### **1️⃣ 下载并运行脚本**
```bash
git clone https://github.com/enixi/pixiv_favoriteNovel_download.git
cd pixiv_favoriteNovel_download
python pixiv4.py
```

### **2️⃣ 选择下载模式**

程序会要求你输入 **下载模式**，例如：
```
请选择下载模式 : 
模式 1: 按单章下载
模式 2: 按系列下载
请输入选择的下载模式（默认为 1 ）: 2
```

单章下载模式中，会下载收藏夹中每篇文章本身

系列下载模式中，若收藏夹中某篇文章属于一个系列，则会将该系列整合为一个文件进行下载

### **3️⃣ 输入 Pixiv COOKIE**
第一次运行时，你需要 **手动粘贴你的 Pixiv COOKIE**。

你可以通过浏览器 **开发者工具** 获取：
- **Chrome / Edge:** `F12 -> 应用 -> 存储 -> Cookies`
- **Firefox:** `F12 -> 存储 -> Cookies`

或者通过 **浏览器插件** 获取
- **Chrome / Edge:** `安装 cookie-editor 插件 -> 点击 Export 并选择 Header String`

（搞不定也可以网上找cookie的教程，一般是抓取到有pixiv.net的标头就可以，类型比如是fetch。)

### **4️⃣ 选择起始页**
程序会要求你输入 **起始页码**，例如：
```
请输入爬取的起始页码（默认为 1 ）: 5
```

---
## 📂 输出文件
所有下载的小说将存放在 **`download_novels`** 文件夹，格式如下：
```
📂 download_novels
 ├── [作者名]小说标题.txt
 ├── [作者名]另一部小说.txt
 ├── ...
```

每本小说包含 **完整信息**：
```
标题: 小说标题
作者: 作者名称
上传时间: 2024-02-11
小说网址: https://www.pixiv.net/novel/show.php?id=123456789
标签: 科幻, 机器人, AI
简介: 
这是一篇关于未来世界的小说...

====================

小说内容......
```

**系列** 小说包含的 **完整信息** 格式如下：

```
标题: 系列标题 (系列篇数，如1~12)
作者: 作者名称
标签: 科幻, 机器人, AI
小说网址: https://www.pixiv.net/novel/show.php?id=123456789
简介: 
这是一篇关于未来世界的小说...

====================

作者的话：

----------

系列中单篇文章的作者简介

----------

小说内容......
```


---
## 🛠️ 可能遇到的问题
### **1️⃣ WebDriver 错误**
如果程序无法找到浏览器驱动，尝试：
```bash
python -m webdriver_manager
```
或者手动下载：
- [Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
- [Chrome WebDriver](https://chromedriver.chromium.org/downloads)

### **2️⃣ 代码报错**
如果运行时遇到 **ModuleNotFoundError**，请手动安装：
```bash
pip install selenium webdriver-manager beautifulsoup4 requests
```

### **3️⃣ Pixiv COOKIE 过期**
如果下载失败，可能是 **COOKIE 失效**，请重新获取 **最新的 COOKIE** 并粘贴。

---

## 🎉 贡献 & 反馈
如果你发现任何 **Bug** 或有改进建议，欢迎提交 **Issue** 或 **Pull Request**！  

---

🚀 **Enjoy!** 🚀
