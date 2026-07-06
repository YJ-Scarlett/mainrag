# 知问课堂 · 轻量教学智能体

这是基于原 `RAG` 项目技术思路重构的简化版教学平台，保留教师端和学生端，以及知识库、知识检索、问答对话和学情分析四项核心能力。项目不包含知识图谱及其可视化。

## 技术栈

- 前端：React + Vite + Recharts + Lucide Icons
- 后端：FastAPI + JSON 本地持久化
- 检索：中文/英文词元匹配、分块排序与来源引用
- 文档：支持 DOC、DOCX、PPT、PPTX、PDF 文本提取
- 资料预览：PDF 直接展示；Word、PowerPoint 通过本机 Office 转为 PDF，保留原文档版式、图片和表格后展示
- 上传进度：展示文件传输、文档解析、版式预览生成和知识库写入状态

## 后端结构

```text
backend/
├── app.py                       # 兼容启动入口
├── main.py                      # FastAPI 应用装配
├── core/config.py               # 路径、DeepSeek 和环境变量配置
├── schemas/                     # 登录、检索、问答请求模型
├── api/
│   ├── router.py                # API 总路由
│   └── routes/                  # 认证、知识库、检索、问答、习题、学情接口
├── services/
│   ├── document_parser.py       # PDF、Word、PowerPoint 文本解析
│   ├── document_service.py      # 文件上传与知识库管理
│   ├── retrieval_service.py     # 文本切分和相关度检索
│   ├── deepseek_service.py      # DeepSeek 大模型调用
│   ├── exam_service.py          # AI 出题、发布、判分和错题
│   └── analysis_service.py      # 个人及班级学情统计
├── storage/json_store.py        # 演示数据和 JSON 持久化
├── web/frontend.py              # 前端静态文件与页面路由托管
├── data/                        # 运行数据
└── uploads/                     # 用户上传文件
```

API 地址保持不变，前端不需要因为后端模块化而调整。

## 启动

项目的 Python 环境位于 `E:\project\atm\zhiwen`。先激活该环境：

```powershell
conda activate E:\project\atm\zhiwen
```

可通过下面的命令确认当前 Python 路径：

```powershell
python -c "import sys; print(sys.executable)"
```

正确结果应为 `E:\project\atm\zhiwen\python.exe`。

### 1. 安装并构建前端

```powershell
cd E:\project\mainrag\frontend
npm install
npm run build
```

### 2. 在启动后端的终端中设置 DeepSeek 密钥

```powershell
cd E:\project\mainrag\backend
$env:DEEPSEEK_API_KEY="在终端中粘贴你的真实密钥"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"
```

密钥只存在于当前 PowerShell 进程及其启动的后端进程中。关闭终端后会自动失效。不要把真实密钥写入 README、源码、命令脚本或聊天内容中。

### 3. 启动完整网站

```powershell
cd E:\project\mainrag\backend
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

浏览器访问 `http://localhost:8000/login`。FastAPI 会同时提供后端 API 和完整前端页面。

开发前端时也可以单独启动：

```powershell
cd E:\project\mainrag\frontend
npm install
npm run dev
```

开发模式访问 `http://localhost:5173`，请求会连接 `http://localhost:8000/api`。

## 演示账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 学生 | `student` | `123456` |
| 教师 | `teacher` | `123456` |

## 功能说明

- 教师端：教学概览、DOC/DOCX/PPT/PPTX/PDF 课程资料上传与删除、按文件和章节 AI 出题、习题发布、知识库问答验证、班级学情分析。
- 学生端：学习首页、只读课程资料库、练习中心、在线作答与自动判分、错题本、知识库问答、个人学情分析。
- 学生只能查看教师共享的知识库资料；教师可以上传、查看和删除资料。
- “查看资料”展示保留原版式的页面预览；提取的纯文本仅用于检索、问答和 AI 出题。
- 学生提交习题后，答题正确率和知识点表现会自动进入个人及班级学情统计，错误题目会自动进入错题本。
- 问答结果展示命中的资料名称、知识片段和相关度。
- 检索结果会作为上下文调用 DeepSeek；密钥只读取启动终端的进程环境，不会写入项目文件或发送给浏览器。
- 问答行为会写入 `backend/data/store.json`，并自动反映在学情统计中。
- 默认内置三份演示知识资料和一组演示学习记录，首次启动即可体验。

若部署时后端地址不是 `http://localhost:8000`，可在前端通过 `VITE_API_URL` 配置完整 API 前缀。

## 页面路由

- `/login`：登录页
- `/student/home`、`/student/knowledge`、`/student/exams`、`/student/wrongbook`、`/student/chat`、`/student/analysis`
- `/teacher/home`、`/teacher/knowledge`、`/teacher/exams`、`/teacher/chat`、`/teacher/analysis`

页面源代码位于 `frontend/src/main.jsx`，FastAPI 在生产运行时负责托管 `frontend/dist`，因此页面路由也能从后端地址直接访问。
