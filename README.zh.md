# AINS NILAM 自动录书工具

**[English Documentation →](README.md)**

自动向马来西亚 **AINS NILAM** 阅读记录系统（ains.moe.gov.my）批量录入书籍记录。

纯 HTTP API —— 不需要浏览器，不需要截图识别，不需要 OCR。专为 AI Agent 全自动操作设计。

---

## 这个项目做什么

AINS NILAM 是马来西亚教育部的全国阅读计划。学生需要在网站上记录自己读过的每一本书。本工具将这个过程完全自动化：

1. AI 联网搜索真实书籍信息（书名、作者、年份、页数、出版社、ISBN）
2. AI 撰写读书摘要（`rumusan`）和心得感悟（`pengajaran`），用马来语或英语
3. Python 脚本直接 POST 到 AINS API
4. 支持**双账号同时提交**

---

## 环境要求

| 要求 | 说明 |
|---|---|
| **操作系统** | 任意 —— Linux、macOS、Windows |
| **Python** | 3.7 及以上 |
| **依赖库** | 仅需 `requests`（安装：`pip install requests`） |
| **网络** | 能访问 `ains.moe.gov.my` 的 HTTPS 网络 |
| **浏览器** | **不需要** |
| **截图 / OCR** | **不需要** |
| **图形界面** | **不需要** |

```bash
pip install -r requirements.txt
```

---

## 工作原理（逆向工程 API）

AINS 网站是基于 Yii2 PHP 框架。逆向发现的接口：

| 步骤 | 接口 | 用途 |
|---|---|---|
| 1 | `GET /web/new-record-book` | 从 `<meta name="csrf-token">` 提取 CSRF token |
| 2 | `POST /reading-record/saverecord` | 以表单数据提交书籍记录 |

**成功**：HTTP 200，响应体为纯文本 `success`。
**失败**：HTTP 200，响应体为纯文本 `failed`。

### 表单字段

| 字段 | 必填 | 可选值 / 约束 |
|---|---|---|
| `_csrf` | 是 | 从 meta 标签提取 |
| `jenis_rekod` | 是 | 固定为 `book` |
| `kategori` | 是 | `fiction`（小说）或 `nonFiction`（非小说） |
| `jenis` | 是 | `physical`（实体书）或 `ebook`（电子书） |
| `bahasa` | 是 | `my`（马来语）、`en`（英语）、`others`（其他） |
| `tajuk` | 是 | 书名 |
| `tahun` | 是 | 1900–2100 |
| `penulis` | 是 | 作者名 |
| `isbn` | 否 | 可选字符串 |
| `mukasurat` | 是 | 页数（整数） |
| `penerbit` | 是 | 出版社 |
| `pautan` | 否 | 可选 URL |
| `penilaian` | 是 | 1–5 星 |
| `rumusan` | 是 | 摘要，**必须超过 100 个字符** |
| `pengajaran` | 是 | 心得感悟，**必须超过 100 个字符** |
| `kulit` | 否 | 封面图 JPG/PNG，最大 2MB |

---

## 实测服务器规则（2026年10月7-8日测试）

### 1. 三分钟冷却（每个账号独立）

提交一本书后，**必须等待 180 秒**才能向同一账号提交下一本。页面会显示：

> *"Rekod bacaan hanya boleh ditambah semula selepas tempoh 3 minit."*

如果间隔太短，API 直接返回 `failed`。

### 2. 双账号互不影响

账号 A 和账号 B 的冷却时间是独立的。**先提交 A1，紧接着提交 A2，然后一起等 3 分钟。**

```
提交 A1 → 提交 A2 → 等待 3 分钟 → 下一本
```

### 3. 每日上限：约 50 本/账号/天

**2026年10月8日实测**：成功提交了约 **49 本**后，双账号同时开始返回 `failed`。日限约为 **每天 50 本/账号**，次日自动重置。

用户之前手动记录时上限约为 30 本/天，可能系统后来调高了。

### 4. Cookie 有效期

- `PHPSESSID`：会话 Cookie
- `_csrf`：会话 Cookie
- `_identity`：86400 秒（24 小时）

如果提交开始跳转到登录页，说明 Cookie 过期了，需要用户重新提供。

---

## 配置方法

### 第一步：获取 Cookie

1. 在 Chrome 浏览器登录 `ains.moe.gov.my`（Google 登录）
2. 按 F12 → **Application** 标签 → **Cookies** → `https://ains.moe.gov.my`
3. 复制所有 Cookie，格式为分号连接的字符串：
   ```
   PHPSESSID=abc123; _csrf=def456; _identity=ghi789;
   ```
4. 第二个账号重复同样操作

### 第二步：保存 Cookie

创建 `cookies.json`：

```json
{
  "account1": { "cookie": "PHPSESSID=xxx; _csrf=yyy; _identity=zzz;" },
  "account2": { "cookie": "PHPSESSID=aaa; _csrf=bbb; _identity=ccc;" }
}
```

### 第三步：运行

```python
from submit_book import submit_to_both
import json

with open("cookies.json") as f:
    accs = json.load(f)

result = submit_to_both(
    cookie1=accs["account1"]["cookie"],
    cookie2=accs["account2"]["cookie"],
    tajuk="Laskar Pelangi",
    tahun=2005,
    penulis="Andrea Hirata",
    mukasurat=529,
    penerbit="Bentang Pustaka",
    kategori="fiction",
    bahasa="my",
    penilaian=4,
    rumusan="...（超过100个字符）...",
    pengajaran="...（超过100个字符）...",
)
print(result)
```

### 批量提交模式

参考 `batch_submit.py`。核心模式：

```python
for i, book in enumerate(books):
    submit_book(cookie1, **book)  # 账号 1
    submit_book(cookie2, **book)  # 账号 2
    if i < len(books) - 1:
        time.sleep(180)  # 等 3 分钟
```

---

## 给 AI Agent 的说明

本项目是一个自包含的 Skill。当 AI Agent 读取 `SKILL.md` 后，它将能够：

1. 理解 AINS API 接口和字段要求
2. 知道 3 分钟冷却和每天约 50 本上限
3. 联网搜索书籍元数据
4. 用马来语或英语撰写 `rumusan` 和 `pengajaran`（各超过 100 字符）
5. 调用 `submit_book.py` 提交
6. 每轮之间等待 3 分钟

不需要浏览器、不需要视觉识别、不需要 DOM 操作。

---

## 选书建议

- **优先马来语小说**（`bahasa=my`）
- **其次英语小说**（`bahasa=en`）
- **实体书**（`jenis=physical`）
- **长篇小说**（优先 300 页以上）
- **避免**：中文书籍、短篇小册子、没有页数的有声书

---

## 文件说明

| 文件 | 用途 |
|---|---|
| `SKILL.md` | AI Agent Skill 定义文件 |
| `submit_book.py` | 核心 Python 提交模块 |
| `batch_submit.py` | 批量提交示例（含3分钟冷却） |
| `cookies.json` | 用户会话 Cookie（已加入 gitignore） |
| `requirements.txt` | Python 依赖 |
| `README.md` | 英文文档 |

---

## 免责声明

本工具仅用于教育自动化目的。用户需自行确保使用符合 AINS NILAM 条款及学校要求。本项目与马来西亚教育部无任何关联。
