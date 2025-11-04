# Knowledge Graph Platform

知识图谱平台，包含前端和后端服务。

## 快速启动

### 后端启动

1. 进入后端目录：
```bash
cd backend
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动后端服务：
```bash
python main.py
```

后端服务将在 `http://localhost:8000` 启动

### 前端启动

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
# 或者使用 pnpm
pnpm install
```

3. 启动前端服务：
```bash
npm start
# 或者使用 pnpm
pnpm start
```

前端服务将在 `http://localhost:3000` 启动

## 访问地址

- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 注意事项

- 确保先启动后端服务，再启动前端服务
- 需要Python 3.13+和Node.js环境