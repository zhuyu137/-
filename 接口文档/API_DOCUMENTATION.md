# 旅图Live API接口文档

## 项目概述

旅图Live是一个基于AI和高德地图API的智能旅行规划系统，提供自然语言解析、景点推荐和行程规划功能。

## 接口列表

### 1. AI联动接口

**接口地址**: `/api/ai/travel/linkage`

**请求方法**: `POST`

**功能描述**: 解析用户自然语言旅行需求，结合高德地图API获取景点信息并生成完整行程

**请求参数**:
```json
{
  "user_input": "周末去青岛玩3天，偏爱大海、美食"
}
```

**响应格式**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "travel_demand": {
      "city": "青岛",
      "spot_type": ["自然风光", "美食"],
      "travel_mode": "步行",
      "play_days": 3
    },
    "daily_itinerary": [
      {
        "day": 1,
        "itinerary": {
          "poi_list": [...],
          "routes": [...],
          "total_distance": 5000,
          "total_duration": 3600
        }
      }
    ]
  }
}
```

**错误响应**:
- `code: -1`: AI解析失败或缺少必要字段
- `code: -2`: 地图数据获取失败

### 2. 路线规划接口

**接口地址**: `/api/navigation/route`

**请求方法**: `POST`

**功能描述**: 基于高德地图API规划两点之间的导航路线，支持多种交通方式

**请求参数**:
```json
{
  "origin": "120.382665,36.066938",
  "destination": "120.4074,39.9042",
  "mode": "自驾"
}
```

**参数说明**:
- `origin`: 起点坐标，格式为"经度,纬度"
- `destination`: 终点坐标，格式为"经度,纬度"
- `mode`: 交通方式，支持"自驾"、"步行"、"公交"等

**响应格式**:
```json
{
  "code": 200,
  "msg": "成功",
  "data": {
    "origin": "起点信息",
    "destination": "终点信息",
    "routes": [...],
    "distance": 10000,
    "duration": 7200
  }
}
```

**错误响应**:
- `code: -1`: 参数缺失或路线规划失败

### 3. 获取旅游路线接口

**接口地址**: `/get_travel_route`

**请求方法**: `POST`

**功能描述**: 与AI联动接口功能相同，提供行程规划服务

**请求参数**:
```json
{
  "user_input": "周末去青岛玩3天，偏爱大海、美食"
}
```

**响应格式**:
同AI联动接口

### 4. WebSocket AI调用接口

**函数名**: `ws_ai_call`

**功能描述**: WebSocket专属的AI调用入口，处理用户旅行需求并返回行程规划结果

**参数**:
- `user_input`: 用户旅行需求（自然语言）
- `itinerary_id`: 行程唯一ID

**返回格式**:
```json
{
  "msg_type": "ai_travel_result",
  "code": 0,
  "msg": "success",
  "payload": {
    "travel_demand": {...},
    "daily_itinerary": [...]
  },
  "itinerary_id": "itinerary_001",
  "timestamp": 1711324800
}
```

**错误码**:
- `code: -99`: AI模块调用失败
- `code: -100`: 行程ID参数错误
- `code: -101`: 用户旅行需求为空

## 数据结构

### TravelDemand 数据结构
```python
class TravelDemand:
    city: str                      # 城市
    play_days: int                 # 游玩天数
    spot_type: List[str]           # 景点类型列表
    travel_mode: str               # 出行方式
    budget: float                  # 预算（元）
    scene: str                     # 旅行场景
```

### POI数据结构
```json
{
  "name": "景点名称",
  "address": "详细地址",
  "lng": "经度",
  "lat": "纬度",
  "type": "景点类型编码",
  "distance": 1000                # 距离（米）
}
```

### 路线数据结构
```json
{
  "start": {"name": "起点名称", "lng": "经度", "lat": "纬度"},
  "end": {"name": "终点名称", "lng": "经度", "lat": "纬度"},
  "distance": 1000,               # 距离（米）
  "duration": 600,                # 预计时间（秒）
  "steps": [                      # 路线步骤
    {"instruction": "步行100米", "distance": 100}
  ]
}
```

## 使用示例

### AI联动接口示例

**请求**:
```bash
curl -X POST http://localhost:5002/api/ai/travel/linkage \
  -H "Content-Type: application/json" \
  -d '{"user_input": "周末去青岛玩3天，偏爱大海、美食"}'
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "travel_demand": {
      "city": "青岛",
      "spot_type": ["自然风光", "美食"],
      "travel_mode": "步行",
      "play_days": 3
    },
    "daily_itinerary": [
      {
        "day": 1,
        "itinerary": {
          "poi_list": [
            {
              "name": "栈桥",
              "address": "山东省青岛市市南区太平路12号",
              "lng": "120.382665",
              "lat": "36.066938",
              "type": "110000"
            }
          ],
          "routes": [],
          "total_distance": 0,
          "total_duration": 0
        }
      }
    ]
  }
}
```

## 技术栈

- **后端框架**: Flask
- **AI服务**: DeepSeek API
- **地图服务**: 高德地图API
- **部署**: Docker

## 部署说明

1. 安装依赖: `pip install -r requirements.txt`
2. 配置高德地图API密钥（在config.py中设置）
3. 启动服务: `python app.py`
4. 服务默认运行在: http://0.0.0.0:5002

## 缓存机制

- 导航路线结果缓存1小时
- 使用内存缓存提升性能

## 错误处理

所有接口统一返回JSON格式，包含以下字段：
- `code`: 状态码（0表示成功，负数表示错误）
- `msg`: 状态消息
- `data`: 返回数据（成功时）或空（失败时）

## 版本信息

当前版本: v1.0.0