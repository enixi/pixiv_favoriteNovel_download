# 📖 Pixiv Favorite Novel Download  

这是一个用于 **批量下载 Pixiv 自己收藏夹里的小说** 的 Python 爬虫脚本。  
⚠ **注意**：请 **确保开启【全局】 VPN**，并 **安装 Microsoft Edge 浏览器**（暂不支持 Chrome/Safari）。  

---

## ✨ 功能特点  

- ✅ **自动爬取** Pixiv 收藏夹中的小说  
- ✅ **支持 Edge 浏览器**（自动适配，**无需手动配置 WebDriver**）  
- ✅ **自动解析小说信息**（标题、作者、上传时间、标签等）  
- ✅ **支持按** **单章 / 系列** **下载**  
- ✅ **仅支持 Windows**（Linux / Mac 用户需手动安装 Edge WebDriver）  

---

## 🛠️ 环境安装  

### **1️⃣ 安装 Python**  
请确保你安装了 **Python 3.8+**，如果没有，请先从 [Python 官网](https://www.python.org/) 下载并安装。  

### **2️⃣ 安装依赖**  
首次运行时，脚本会自动安装所需的 Python 依赖项。

但如果出现错误，可以手动安装：  

```bash
pip install -r requirements.txt
```

如果没有 `requirements.txt`，请执行：  

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
程序会让你选择 **下载模式**：  

```yaml
请选择下载模式 :  
模式 1: 按单章下载  
模式 2: 按系列下载  
请输入选择的下载模式（默认为 1 ）: 2
```

### **3️⃣ 输入 Pixiv COOKIE**  

你可以通过 **浏览器开发者工具** 获取：  

🔹 **Chrome / Edge**  
```
F12 → 应用 (Application) → 存储 (Storage) → Cookies
```

🔹 **Firefox**  
```
F12 → 存储 (Storage) → Cookies
```

找到 **pixiv.net 相关标头的 Cookie** 整个复制下来就可以。  
（如果不会抓 Cookie，可在网上搜索 Pixiv 获取 Cookie 的方法。通常刷新自己主页的收藏页，类型为fetch 的）。  

### **4️⃣ 输入起始页**  
程序会要求你输入 **起始页码**，例如：  

```bash
请输入爬取的起始页码（默认为 1 ）: 1
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

**示例：**  

每本小说包含 **完整信息**：  

```
标题: 小说标题  
作者: 作者名称  
上传时间: 2024-02-11  
原文网址: https://www.pixiv.net/novel/show.php?id=123456789  
标签: 科幻, 机器人, AI  
简介: 这是一篇关于未来世界的小说...
======================

小说正文...
```

如果选择 **按系列下载**，所有章节会合并成 **一个完整的 TXT 文件**。  

---

## 🛠️ 可能遇到的问题  

### **1️⃣ WebDriver 错误**  
如果程序无法找到 Edge WebDriver，可尝试：  

```bash
python -m webdriver_manager
```

或者手动下载：  
- [Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)  

### **2️⃣ 代码报错**  
如果运行时遇到 **ModuleNotFoundError**，请手动安装：  

```bash
pip install selenium webdriver-manager beautifulsoup4 requests
```

### **3️⃣ Pixiv COOKIE 过期**  
如果爬取失败，可能是 **COOKIE 失效**，请重新获取 **最新的 COOKIE** 并粘贴。  

### **4️⃣ 网络问题**  
- **确保开启全局 VPN**（否则 Pixiv 可能无法访问）。  
- **等待一段时间再试**（Pixiv 可能临时限制 IP）。  

---

## 🎉 贡献 & 反馈  
如果你发现 **Bug** 或有 **改进建议**，欢迎提交 **Issue** 或 **Pull Request**！  
如果你觉得这个项目有帮助，欢迎 **⭐ Star** 支持！  

---

🚀 **Enjoy!** 🚀

