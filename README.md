# 知问课堂 · 轻量教学智能体

这是基于原 `RAG` 项目技术思路重构的简化版教学平台，保留教师端和学生端，以及知识库、知识检索、问答对话和学情分析四项核心能力。项目不包含知识图谱及其可视化。

## 技术栈

- 前端：React + Vite + Recharts + Lucide Icons
- 后端：FastAPI + JSON 本地持久化
- 检索：BGE-M3 向量化、Chroma 向量库、中文/英文词元匹配、分块排序与来源引用
- 文档：支持 DOC、DOCX、PPT、PPTX、PDF 文本提取
- 多模态资料：支持 MP3、WAV、M4A、AAC、FLAC、OGG、WMA、MP4、MOV、AVI、MKV、WEBM、WMV、FLV，通过本地 Whisper 转写后进入知识库检索
- 资料预览：PDF 直接展示；Word、PowerPoint 通过本机 Office 转为 PDF，保留原文档版式、图片和表格后展示；音频、视频使用浏览器播放器在线播放
- 上传进度：展示文件传输、文档解析或音视频转写、版式预览生成和知识库写入状态

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
│   ├── media_parser.py          # 音频、视频转写为知识库文本
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
$env:PYTHONNOUSERSITE="1"
$env:DEEPSEEK_API_KEY="在终端中粘贴你的真实密钥"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"

# Embedding 使用本地 BGE-M3，不需要设置 embedding 密钥。
# 第一次上传或重建索引时会自动下载模型到 backend/models。
# 如需切换模型或指定设备，可选设置：
$env:LOCAL_EMBEDDING_MODEL="BAAI/bge-m3"
$env:EMBEDDING_DEVICE="cpu"

# 音视频资料使用本地 Whisper 转写，第一次使用会下载模型到 D:/huggingface_cache。
# 如需更快可改为 openai/whisper-tiny 或 openai/whisper-base；如需更高准确率可改为 openai/whisper-medium。
$env:LOCAL_SPEECH_MODEL="openai/whisper-small"
$env:SPEECH_LANGUAGE="zh"
```

密钥只存在于当前 PowerShell 进程及其启动的后端进程中。关闭终端后会自动失效。不要把真实密钥写入 README、源码、命令脚本或聊天内容中。

`PYTHONNOUSERSITE=1` 用于避免系统用户目录下的 Python 包混入当前 conda 环境。

音频和视频转写需要本机安装 `ffmpeg`。推荐安装到当前 conda 环境：

```powershell
conda activate E:\project\atm\zhiwen
conda install -c conda-forge ffmpeg
ffmpeg -version
```

`ffmpeg -version` 能正常输出版本信息后，音视频上传才能被 Whisper 正常转写。

### 3. 启动完整网站

```powershell
cd E:\project\mainrag\backend
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问 `http://localhost:8000/login`。FastAPI 会同时提供后端 API 和完整前端页面。

开发前端时也可以单独启动：

```powershell
cd E:\project\mainrag\frontend
npm install
npm run dev
```

开发模式访问 `http://localhost:5173`，请求会连接 `http://localhost:8000/api`。

### Conda 环境常见问题

如果启动时报错 `_ctypes` 加载失败：

```text
ImportError: DLL load failed while importing _ctypes: 找不到指定的模块。
```

优先尝试：

```powershell
conda activate E:\project\atm\zhiwen
$env:PYTHONNOUSERSITE="1"
conda install --override-channels -c defaults libffi --force-reinstall
python -c "import _ctypes; print('_ctypes ok')"
```

如果仍然失败，说明 `_ctypes.pyd` 需要的 `ffi.dll` 没有被正确安装，可临时复制当前环境里的 `ffi-8.dll`：

```powershell
Copy-Item E:\project\atm\zhiwen\Library\bin\ffi-8.dll E:\project\atm\zhiwen\Library\bin\ffi.dll -Force
Copy-Item E:\project\atm\zhiwen\Library\bin\ffi-8.dll E:\project\atm\zhiwen\ffi.dll -Force
python -c "import _ctypes; print('_ctypes ok')"
```

如果项目环境长期混用 `defaults`、`conda-forge` 和用户目录 Python 包，建议后续重新创建一个干净环境。

## 演示账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 学生 | `student` | `123456` |
| 教师 | `teacher` | `123456` |

## 功能说明

- 教师端：教学概览、DOC/DOCX/PPT/PPTX/PDF/音频/视频课程资料上传与删除、按文件和章节 AI 出题、习题发布、知识库问答验证、班级学情分析。
- 学生端：学习首页、只读课程资料库、练习中心、在线作答与自动判分、错题本、知识库问答、个人学情分析。
- 学生只能查看教师共享的知识库资料；教师可以上传、查看和删除资料。
- “查看资料”展示保留原版式的页面预览；音视频资料可在线播放，并会转写为文本用于检索、问答和 AI 出题。
- 学生提交习题后，答题正确率和知识点表现会自动进入个人及班级学情统计，错误题目会自动进入错题本。
- 问答结果展示命中的资料名称、知识片段和相关度。
- 检索结果会作为上下文调用 DeepSeek；密钥只读取启动终端的进程环境，不会写入项目文件或发送给浏览器。
- 问答行为会写入 `backend/data/store.json`，并自动反映在学情统计中。
- 默认内置三份演示知识资料和一组演示学习记录，首次启动即可体验。

## 音视频 RAG 切片策略

音频和视频资料不会直接按文件大小切片，而是先转写成带时间戳的语音片段，再进入知识库：

```text
视频 / 音频
  ↓
本地 Whisper ASR
  ↓
带时间戳文本 segment
  ↓
轻量标点恢复
  ↓
按语义段和长度合并切片
  ↓
embedding 向量化 + start_time/end_time metadata
  ↓
Chroma 向量库
```

上传音视频后，系统会在转写文本中生成 `[[TIME:start-end]]` 标记。建立向量索引时，每个向量片段都会保存 `start_time` 和 `end_time`，问答来源会显示为类似 `00:08 - 00:15` 的时间范围。旧版已上传的音视频如果没有时间戳，点击教师端“重建向量索引”会重新转写并生成时间戳片段。

若部署时后端地址不是 `http://localhost:8000`，可在前端通过 `VITE_API_URL` 配置完整 API 前缀。

## 页面路由

- `/login`：登录页
- `/student/home`、`/student/knowledge`、`/student/exams`、`/student/wrongbook`、`/student/chat`、`/student/analysis`
- `/teacher/home`、`/teacher/knowledge`、`/teacher/exams`、`/teacher/chat`、`/teacher/analysis`

页面源代码位于 `frontend/src/main.jsx`，FastAPI 在生产运行时负责托管 `frontend/dist`，因此页面路由也能从后端地址直接访问。

## ???????

???? ChromaDB ??????????????? `backend/data/vector_store.json` ?????

?? RAG ???

```text
????????
  ?
????
  ?
?? BGE-M3 ?? embedding ??
  ?
?? ChromaDB ?????? backend/data/chroma/
  ?
???????????
  ?
ChromaDB ???????????
  ?
DeepSeek ??????????
```

???????

```powershell
cd E:\project\mainrag\backend
python -m pip install chromadb==0.5.23
```

?????? `Microsoft Visual C++ 14.0 or greater is required`??? Chroma ??? `chroma-hnswlib` ?? C++ ???????????? Microsoft C++ Build Tools ????????????? Python 3.11 ??????

???????????????????????????????????????????? ChromaDB?

`backend/data/chroma/`?`backend/data/vector_store.json`?`backend/models/`?`backend/uploads/` ????????????????????

## 拍照搜题功能

问答助手中已加入拍照搜题入口。学生可以在问答输入框左侧点击相机按钮，上传题目图片或在手机端直接调用摄像头拍照。

处理流程：

```text
题目图片
  → OCR 识别题干和选项
  → 清洗识别文本
  → 使用识别出的题目文本检索课程知识库
  → 将检索片段作为上下文调用 DeepSeek
  → 返回答案、解析和可追溯参考来源
```

后端接口：

```text
POST /api/chat/photo-search
```

该接口会接收图片文件，返回 OCR 识别文本、AI 解题结果和知识库来源，并把本次拍照搜题记录写入历史问答。

拍照搜题需要额外安装 OCR 依赖，二选一即可：

```powershell
# 推荐：中文题目识别效果更好
python -m pip install paddleocr paddlepaddle

# 或者：Tesseract 方案，需要额外安装系统版 Tesseract OCR
python -m pip install pillow pytesseract
```

如果没有安装 OCR 依赖，原有知识库问答功能不受影响；点击拍照搜题时后端会返回安装提示。

Windows CPU 环境下，PaddleOCR 3.x 可能会触发 oneDNN/PIR 兼容问题：

```text
ConvertPirAttribute2RuntimeAttribute not support ... onednn_instruction.cc
```

项目已在 `services/photo_ocr_service.py` 中默认设置：

```text
PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=0
FLAGS_use_onednn=0
FLAGS_use_mkldnn=0
```

并使用较稳定的 `PP-OCRv4` OCR 模型，避免该问题影响拍照搜题。
