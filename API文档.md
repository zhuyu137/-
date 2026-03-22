# 旅行规划AI项目API文档
> 文档版本：v1.0
> 适用环境：开发/测试
> 最后更新：2026年

## 一、文档概述
本文档基于旅行规划AI项目的实际代码实现，详细描述后端所有API接口的调用规范、参数说明、响应格式及错误码。项目核心能力包括：自然语言旅行需求解析（基于DeepSeek大模型）、高德地图POI搜索/路径规划、多日行程智能分组与路线生成，同时支持HTTP接口和WebSocket调用两种方式。

## 二、通用说明
### 2.1 基础配置
| 配置项 | 取值 | 说明 |
|--------|------|------|
| 服务地址 | `http://10.33.31.149:5000` | 本地开发环境默认地址 |
| 请求方式 | POST（HTTP接口） | 所有HTTP接口均为POST请求 |
| 数据格式 | JSON | 请求/响应均采用JSON格式 |
| 字符编码 | UTF-8 | 全局字符编码规范 |
| 核心依赖 | DeepSeek API、高德地图Web API | AI解析和地图数据依赖 |

### 2.2 通用响应格式
所有接口返回统一JSON结构，字段定义如下：

| 字段名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| code   | int  | 是   | 响应状态码（0=成功，非0=失败） |
| msg    | str  | 是   | 响应描述信息 |
| data   | any  | 否   | 业务数据（成功时返回有效数据，失败时为null/空对象） |

### 2.3 通用错误码
| 错误码 | 说明 | 触发场景 |
|--------|------|----------|
| 0      | 成功 | 接口调用及业务处理均正常 |
| -1     | AI解析用户需求失败 | DeepSeek接口返回非预期格式、JSON解析失败等 |
| -2     | 地图数据获取失败 | 高德POI搜索/路径规划接口调用失败、无匹配POI数据 |
| -3     | 用户输入不能为空 | HTTP接口请求中`user_input`为空字符串 |
| -4     | AI接口内部错误 | HTTP接口层捕获到未知异常 |
| -5     | 需要更多用户信息 | AI解析后发现核心字段缺失（如未指定城市/景点类型） |
| -99    | AI模块调用失败 | WebSocket调用时捕获到未知异常 |
| -100   | 行程ID无效 | WebSocket调用时`itinerary_id`为空/非字符串 |
| -101   | 用户旅行需求为空 | WebSocket调用时`user_input`为空字符串 |
| 400    | 请求参数错误 | `/get_travel_route`接口用户输入为空 |
| 500    | 服务器内部错误 | `/get_travel_route`接口捕获到未知异常 |

## 三、HTTP接口详情
### 3.1 AI+高德联动核心接口
#### 接口描述
解析用户自然语言旅行需求，调用高德API获取POI数据，基于K-means聚类分组POI并生成多日行程规划（项目核心接口）。

#### 接口信息
- URL：`/api/ai/travel/linkage`
- 请求方式：POST
- 权限：公开

#### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| user_input | str | 是 | "周末去青岛玩3天，偏爱大海、美食，打车出行，人均预算1000元" | 用户自然语言旅行需求 |

#### 请求示例
```json
{
  "user_input": "周末去青岛玩3天，偏爱大海、美食，打车出行，人均预算1000元"
}
```

#### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码 |
| msg | str | 响应描述 |
| data | object | 业务数据容器 |
| data.travel_demand | object | AI解析后的结构化旅行需求 |
| data.travel_demand.city | str | 目的地城市 |
| data.travel_demand.spot_type | array[str] | 景点类型列表（如["自然风光","美食"]） |
| data.travel_demand.travel_mode | str | 市内出行方式（步行/公交/自驾/打车） |
| data.travel_demand.budget | str | 人均预算 |
| data.travel_demand.play_days | int | 游玩天数 |
| data.amap_data | object | 高德地图数据容器（预留字段） |
| data.daily_itinerary | array[object] | 多日行程规划列表 |
| data.daily_itinerary[].day | int | 天数（第N天） |
| data.daily_itinerary[].itinerary | object | 单日行程详情 |
| data.daily_itinerary[].itinerary.poi_list | array[object] | 当日POI列表（含名称、经纬度、地址等） |
| data.daily_itinerary[].itinerary.routes | array[object] | 当日路线规划（含每段行程的距离/时长/步骤） |
| data.daily_itinerary[].itinerary.total_distance | float | 当日总距离（km） |
| data.daily_itinerary[].itinerary.total_duration | float | 当日总时长（min） |

#### 成功响应示例
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "travel_demand": {
      "city": "青岛",
      "spot_type": ["自然风光", "美食"],
      "travel_mode": "打车",
      "budget": "1000",
      "max_distance": 500,
      "play_days": 3
    },
    "amap_data": {
      "poi_list": [],
      "daily_itinerary": []
    },
    "daily_itinerary": [
      {
        "day": 1,
        "itinerary": {
          "poi_list": [
            {
              "name": "五四广场",
              "address": "山东省青岛市市南区东海西路3号",
              "lng": "120.33934",
              "lat": "36.06712",
              "type": "110000",
              "distance": 0
            },
            {
              "name": "青岛啤酒博物馆",
              "address": "山东省青岛市市北区登州路56号",
              "lng": "120.31287",
              "lat": "36.08765",
              "type": "050000",
              "distance": 0
            }
          ],
          "routes": [
            {
              "from": "五四广场",
              "to": "青岛啤酒博物馆",
              "route": {
                "distance": "5.2km",
                "duration": "15min",
                "steps": [
                  {
                    "instruction": "从五四广场出发，沿东海西路向西行驶，转入山东路向北，最终到达青岛啤酒博物馆"
                  }
                ]
              }
            }
          ],
          "total_distance": 5.2,
          "total_duration": 15.0
        }
      },
      {
        "day": 2,
        "itinerary": {
          "poi_list": [...],
          "routes": [...],
          "total_distance": 8.5,
          "total_duration": 25.0
        }
      },
      {
        "day": 3,
        "itinerary": {
          "poi_list": [...],
          "routes": [...],
          "total_distance": 6.8,
          "total_duration": 20.0
        }
      }
    ]
  }
}
```

#### 缺失信息响应示例
```json
{
  "code": -5,
  "msg": "need_more_info",
  "data": {
    "questions": [
      "请问您的目的地城市是哪里？",
      "您喜欢什么类型的景点（如自然风光、美食等）？"
    ],
    "hint": "请回答以上问题以便为您规划行程"
  }
}
```

### 3.2 行程路线简化获取接口
#### 接口描述
简化版接口，仅返回多日行程规划数据（无结构化需求解析结果）。

#### 接口信息
- URL：`/get_travel_route`
- 请求方式：POST
- 权限：公开

#### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| user_input | str | 是 | "周末去青岛玩3天，偏爱大海、美食，打车出行" | 用户自然语言旅行需求 |

#### 请求示例
```json
{
  "user_input": "周末去青岛玩3天，偏爱大海、美食，打车出行"
}
```

#### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功，其他=失败） |
| msg | str | 响应描述 |
| data | array[object] | 多日行程规划列表（同3.1接口的`data.daily_itinerary`） |

#### 成功响应示例
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "day": 1,
      "itinerary": {
        "poi_list": [...],
        "routes": [...],
        "total_distance": 5.2,
        "total_duration": 15.0
      }
    },
    {
      "day": 2,
      "itinerary": {
        "poi_list": [...],
        "routes": [...],
        "total_distance": 8.5,
        "total_duration": 25.0
      }
    },
    {
      "day": 3,
      "itinerary": {
        "poi_list": [...],
        "routes": [...],
        "total_distance": 6.8,
        "total_duration": 20.0
      }
    }
  ]
}
```

#### 失败响应示例
```json
{
  "code": 400,
  "msg": "用户输入不能为空",
  "data": null
}
```

## 四、WebSocket调用接口
### 4.1 接口描述
专为WebSocket通信设计的AI调用入口，支持带行程ID的会话级调用，返回格式适配WebSocket消息推送。

### 4.2 核心函数（服务端）
```python
def ws_ai_call(user_input: str, itinerary_id: str) -> Dict:
    """
    WebSocket专属AI调用入口
    :param user_input: 用户旅行需求（自然语言）
    :param itinerary_id: 行程唯一ID
    :return: WebSocket响应格式字典
    """
```

### 4.3 入参说明
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| user_input | str | 是 | "周末去青岛玩3天，偏爱大海、美食" | 用户自然语言旅行需求 |
| itinerary_id | str | 是 | "test_001" | 行程唯一标识（用于会话追踪） |

### 4.4 响应格式
| 字段名 | 类型 | 说明 |
|--------|------|------|
| msg_type | str | 消息类型（固定为"ai_travel_result"） |
| code | int | 响应状态码（同通用错误码） |
| msg | str | 响应描述 |
| payload | object | 业务数据（同HTTP接口的`data`字段） |
| itinerary_id | str | 入参传入的行程ID |
| timestamp | int | 响应时间戳（秒级） |

### 4.5 响应示例
```json
{
  "msg_type": "ai_travel_result",
  "code": 0,
  "msg": "success",
  "payload": {
    "travel_demand": {
      "city": "青岛",
      "spot_type": ["自然风光", "美食"],
      "travel_mode": "打车",
      "budget": "1000",
      "play_days": 3
    },
    "daily_itinerary": [...]
  },
  "itinerary_id": "test_001",
  "timestamp": 1735689600
}
```

## 五、核心依赖与配置
### 5.1 密钥配置（config.py）
| 配置项 | 示例值 | 说明 |
|--------|--------|------|
| DEEPSEEK_API_KEY | "sk-e494b0844362415abd0d92f547900e74" | DeepSeek大模型API密钥 |
| AMAP_WEB_KEY | "6286beb032c6105d5cc0ce09fade8849" | 高德地图Web API密钥 |

### 5.2 类型映射配置
#### 高德POI类型映射
| 业务类型 | 高德编码 | 说明 |
|----------|----------|------|
| 自然风光 | 110000 | 自然景观类POI |
| 历史古迹 | 110000 | 历史文化类POI |
| 美食     | 050000 | 餐饮类POI |
| 非遗体验 | 140000 | 非遗相关POI |
| 网红打卡 | 060000 | 网红打卡地POI |

#### 出行方式映射
| 业务方式 | 高德接口类型 | 速度估算（km/h） |
|----------|--------------|------------------|
| 步行     | walk         | 5                |
| 公交     | bus          | 15               |
| 自驾     | drive        | 30               |
| 打车     | drive        | 30               |

## 六、开发与测试
### 6.1 本地启动
```python
# 运行app.py启动Flask服务
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### 6.2 测试WebSocket调用
```python
# 在app.py中执行测试代码
user_input = "周末和搭子去青岛玩3天，偏爱大海、美食，预算人均1000元，打车游玩。"
result = ws_ai_call(user_input, "test_001")
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 6.3 注意事项
1. 高德API调用有频率限制，生产环境建议添加缓存机制；
2. DeepSeek API需保证密钥有效且余额充足，否则AI解析功能失效；
3. 行程分组采用K-means聚类，可通过调整`max_iter`参数优化分组效果；
4. 路径规划优先使用高德接口数据，接口异常时自动采用直线距离估算。