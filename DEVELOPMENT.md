# 本地开发

项目使用 Vue 3 + TypeScript 前端、FastAPI 本地后端和 SQLite 数据库。

## 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

API 文档：`http://127.0.0.1:8000/docs`。

## 前端

在另一个终端运行：

```powershell
cd frontend
pnpm install
pnpm dev
```

页面地址：`http://127.0.0.1:5173`。

在当前电脑上，也可以双击 `backend/start_desktop.vbs`，无窗口启动完整本地应用并自动打开浏览器。

## DeepSeek

复制 `backend/.env.example` 为 `backend/.env`，然后填写 `DEEPSEEK_API_KEY`。
密钥不会提交到 Git，也不应写在前端代码中。

也可以在软件的“设置 → AI错题解析”中填写密钥。桌面版会把配置保存在当前用户的本地应用数据目录。

## 验证

```powershell
cd backend
python -m pytest

cd frontend
pnpm build
```

## 构建Windows桌面版

先完成前端构建，然后运行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean desktop.spec
```

生成目录位于 `backend/dist/拾词学习系统/`。双击其中的 `拾词学习系统.exe` 后，程序会在后台启动服务并自动打开浏览器。
