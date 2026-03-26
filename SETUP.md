# 项目环境配置指南

## 后端环境配置

### 使用Anaconda创建环境

1. 确保已安装Anaconda或Miniconda

2. 在项目根目录下执行以下命令：

```bash
# 创建虚拟环境
conda env create -f environment.yml

# 激活虚拟环境
conda activate travel-ai
```

### 环境变量配置

1. 创建`.env`文件（可选）：

```bash
# 高德地图Web API密钥
AMAP_WEB_KEY=your_amap_web_key

# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 启动后端服务

```bash
cd ai-part
python app.py
```

服务将运行在 http://127.0.0.1:5002

## 前端环境配置

### 安装依赖

```bash
cd travel-app
npm install
```

### 启动开发服务器

```bash
# Web端
npm run web

# iOS模拟器
npm run ios

# Android模拟器
npm run android
```

Web端访问地址：http://localhost:8084

## 项目结构

```
travel-app/          # React Native前端项目
ai-part/            # Flask后端项目
environment.yml     # Conda环境配置文件
```

## 注意事项

1. 确保后端服务先启动，前端才能正常访问AI功能
2. 高德地图Android API密钥已在app.json中配置
3. 所有API服务地址已在services/api.ts中配置
