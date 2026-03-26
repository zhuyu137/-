# 旅图live API文档
> 文档版本：v1.1
> 适用环境：开发/测试
> 最后更新：2026年

## 一、文档概述
本文档基于旅图live项目的实际代码实现，详细描述后端所有API接口的调用规范、参数说明、响应格式及错误码。项目核心能力包括：自然语言旅行需求解析（基于DeepSeek大模型）、高德地图POI搜索/路径规划、多日行程智能分组与路线生成、协作空间管理、POI详情管理，同时支持HTTP接口和WebSocket调用两种方式。

## 二、通用说明
### 2.1 基础配置
| 配置项 | 取值 | 说明 |
|--------|------|------|
| 服务地址 | `http://182.92.10.201:3000` | 服务器地址 |
| 请求方式 | POST（HTTP接口，特殊标注除外） | 大部分HTTP接口为POST请求，POI详情查询为GET |
| 数据格式 | JSON | 请求/响应均采用JSON格式 |
| 字符编码 | UTF-8 | 全局字符编码规范 |
| 核心依赖 | DeepSeek API、高德地图Web API | AI解析和地图数据依赖 |

### 2.2 通用响应格式
所有接口返回统一JSON结构，字段定义如下：

| 字段名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| code   | int  | 是   | 响应状态码（0/200=成功，非0=失败） |
| msg/message    | str  | 是   | 响应描述信息（兼容msg和message字段，新接口统一使用message） |
| data   | any  | 否   | 业务数据（成功时返回有效数据，失败时为null/空对象） |

### 2.3 通用错误码
| 错误码 | 说明 | 触发场景 |
|--------|------|----------|
| 0      | 成功 | 原有接口调用及业务处理均正常 |
| 200    | 成功 | 新增接口统一成功状态码 |
| -1     | AI解析用户需求失败 | DeepSeek接口返回非预期格式、JSON解析失败等 |
| -2     | 地图数据获取失败 | 高德POI搜索/路径规划接口调用失败、无匹配POI数据 |
| -3     | 用户输入不能为空 | HTTP接口请求中`user_input`为空字符串 |
| -4     | AI接口内部错误 | HTTP接口层捕获到未知异常 |
| -5     | 需要更多用户信息 | AI解析后发现核心字段缺失（如未指定城市/景点类型） |
| -99    | AI模块调用失败 | WebSocket调用时捕获到未知异常 |
| -100   | 行程ID无效 | WebSocket调用时`itinerary_id`为空/非字符串 |
| -101   | 用户旅行需求为空 | WebSocket调用时`user_input`为空字符串 |
| 400    | 请求参数错误 | `/get_travel_route`接口用户输入为空、新增接口参数缺失/格式错误 |
| 404    | 资源不存在 | 协作空间/POI/标记不存在 |
| 500    | 服务器内部错误 | 接口捕获到未知异常 |

## 三、HTTP接口详情

### 3.3 协作模块接口
#### 3.3.1 创建协作空间
##### 接口描述
创建旅行协作空间，用于多人共同规划行程、标记POI、添加评论等协作操作。

##### 接口信息
- URL：`/api/collaboration/create-space`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| name | str | 是 | "青岛3天游规划" | 协作空间名称 |
| description | str | 否 | "周末和朋友去青岛的行程规划" | 协作空间描述 |
| created_by | str | 是 | "user_001" | 创建者用户ID |

##### 请求示例
```json
{
  "name": "青岛3天游规划",
  "description": "周末和朋友去青岛的行程规划",
  "created_by": "user_001"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.space_id | str | 协作空间唯一ID |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "创建协作空间成功",
  "data": {
    "space_id": "space_001"
  }
}
```

#### 3.3.2 获取协作空间列表
##### 接口描述
根据用户ID查询该用户创建/参与的所有协作空间列表。

##### 接口信息
- URL：`/api/collaboration/get-spaces`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| user_id | str | 是 | "user_001" | 用户ID |

##### 请求示例
```json
{
  "user_id": "user_001"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | array[object] | 协作空间列表 |
| data[].space_id | str | 协作空间ID |
| data[].name | str | 协作空间名称 |
| data[].description | str | 协作空间描述 |
| data[].created_by | str | 创建者用户ID |
| data[].created_at | int | 创建时间戳（秒级） |
| data[].member_count | int | 成员数量 |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "获取协作空间列表成功",
  "data": [
    {
      "space_id": "space_001",
      "name": "青岛3天游规划",
      "description": "周末和朋友去青岛的行程规划",
      "created_by": "user_001",
      "created_at": 1735689600,
      "member_count": 3
    }
  ]
}
```

#### 3.3.3 获取协作空间详情
##### 接口描述
根据协作空间ID查询空间基本信息及成员列表。

##### 接口信息
- URL：`/api/collaboration/get-space`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |

##### 请求示例
```json
{
  "space_id": "space_001"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.space_info | object | 空间基本信息 |
| data.space_info.space_id | str | 协作空间ID |
| data.space_info.name | str | 空间名称 |
| data.space_info.description | str | 空间描述 |
| data.space_info.created_by | str | 创建者ID |
| data.space_info.created_at | int | 创建时间戳 |
| data.members | array[object] | 成员列表 |
| data.members[].user_id | str | 成员用户ID |
| data.members[].name | str | 成员昵称 |
| data.members[].join_at | int | 加入时间戳 |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "获取协作空间详情成功",
  "data": {
    "space_info": {
      "space_id": "space_001",
      "name": "青岛3天游规划",
      "description": "周末和朋友去青岛的行程规划",
      "created_by": "user_001",
      "created_at": 1735689600
    },
    "members": [
      {
        "user_id": "user_001",
        "name": "张三",
        "join_at": 1735689600
      },
      {
        "user_id": "user_002",
        "name": "李四",
        "join_at": 1735689700
      }
    ]
  }
}
```

#### 3.3.4 添加成员到空间
##### 接口描述
向指定协作空间添加成员。

##### 接口信息
- URL：`/api/collaboration/add-member`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |
| user_id | str | 是 | "user_002" | 待添加成员的用户ID |
| name | str | 是 | "李四" | 成员昵称 |

##### 请求示例
```json
{
  "space_id": "space_001",
  "user_id": "user_002",
  "name": "李四"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | null | 无业务数据 |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "添加成员成功",
  "data": null
}
```

#### 3.3.5 添加地图标记
##### 接口描述
在协作空间内添加POI地图标记，用于多人标注感兴趣的地点。

##### 接口信息
- URL：`/api/collaboration/add-marker`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |
| user_id | str | 是 | "user_001" | 标记创建者ID |
| user_name | str | 是 | "张三" | 标记创建者昵称 |
| name | str | 是 | "五四广场" | 标记名称 |
| address | str | 是 | "山东省青岛市市南区东海西路3号" | 标记地址 |
| latitude | float | 是 | 36.06712 | 纬度 |
| longitude | float | 是 | 120.33934 | 经度 |
| type | str | 是 | "自然风光" | 标记类型（参考高德POI类型映射） |
| rating | float | 否 | 4.8 | 评分（1-5分） |

##### 请求示例
```json
{
  "space_id": "space_001",
  "user_id": "user_001",
  "user_name": "张三",
  "name": "五四广场",
  "address": "山东省青岛市市南区东海西路3号",
  "latitude": 36.06712,
  "longitude": 120.33934,
  "type": "自然风光",
  "rating": 4.8
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.marker_id | str | 标记唯一ID |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "添加地图标记成功",
  "data": {
    "marker_id": "marker_001"
  }
}
```

#### 3.3.6 获取空间标记列表
##### 接口描述
查询指定协作空间内的所有地图标记。

##### 接口信息
- URL：`/api/collaboration/get-markers`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |

##### 请求示例
```json
{
  "space_id": "space_001"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | array[object] | 标记数组 |
| data[].marker_id | str | 标记ID |
| data[].space_id | str | 协作空间ID |
| data[].user_id | str | 创建者ID |
| data[].user_name | str | 创建者昵称 |
| data[].name | str | 标记名称 |
| data[].address | str | 标记地址 |
| data[].latitude | float | 纬度 |
| data[].longitude | float | 经度 |
| data[].type | str | 标记类型 |
| data[].rating | float | 评分 |
| data[].like_count | int | 点赞数 |
| data[].is_liked | bool | 当前用户是否点赞（可选） |
| data[].created_at | int | 创建时间戳 |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "获取空间标记列表成功",
  "data": [
    {
      "marker_id": "marker_001",
      "space_id": "space_001",
      "user_id": "user_001",
      "user_name": "张三",
      "name": "五四广场",
      "address": "山东省青岛市市南区东海西路3号",
      "latitude": 36.06712,
      "longitude": 120.33934,
      "type": "自然风光",
      "rating": 4.8,
      "like_count": 2,
      "is_liked": true,
      "created_at": 1735689800
    }
  ]
}
```

#### 3.3.7 点赞/取消点赞标记
##### 接口描述
对协作空间内的地图标记进行点赞或取消点赞操作（切换状态）。

##### 接口信息
- URL：`/api/collaboration/like-marker`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| marker_id | str | 是 | "marker_001" | 标记ID |
| user_id | str | 是 | "user_002" | 操作用户ID |

##### 请求示例
```json
{
  "marker_id": "marker_001",
  "user_id": "user_002"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述（点赞成功/取消点赞成功） |
| data | object | 业务数据 |
| data.is_liked | bool | 操作后的点赞状态（true=已点赞，false=未点赞） |
| data.like_count | int | 最新点赞数 |

##### 成功响应示例（点赞）
```json
{
  "code": 200,
  "message": "点赞成功",
  "data": {
    "is_liked": true,
    "like_count": 3
  }
}
```

##### 成功响应示例（取消点赞）
```json
{
  "code": 200,
  "message": "取消点赞成功",
  "data": {
    "is_liked": false,
    "like_count": 2
  }
}
```

#### 3.3.8 添加评论
##### 接口描述
对协作空间内的地图标记添加评论。

##### 接口信息
- URL：`/api/collaboration/add-comment`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| marker_id | str | 是 | "marker_001" | 标记ID |
| user_id | str | 是 | "user_002" | 评论者ID |
| user_name | str | 是 | "李四" | 评论者昵称 |
| content | str | 是 | "这里的夜景超美，推荐晚上来！" | 评论内容 |

##### 请求示例
```json
{
  "marker_id": "marker_001",
  "user_id": "user_002",
  "user_name": "李四",
  "content": "这里的夜景超美，推荐晚上来！"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.comment_id | str | 评论唯一ID |
| data.created_at | int | 评论创建时间戳 |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "添加评论成功",
  "data": {
    "comment_id": "comment_001",
    "created_at": 1735689900
  }
}
```

#### 3.3.9 AI分析群体兴趣
##### 接口描述
基于协作空间内的标记、点赞、评论等数据，通过AI分析群体的旅行兴趣偏好。

##### 接口信息
- URL：`/api/collaboration/analyze-interest`
- 请求方式：POST
- 权限：公开
- 备注：需传入space_id（补充参数，原需求未明确，默认必填）

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |

##### 请求示例
```json
{
  "space_id": "space_001"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.interest_tags | array[str] | 兴趣标签列表（如["自然风光","夜景","美食"]） |
| data.preference_types | object | 偏好类型分析 |
| data.preference_types.spot_type | array[str] | 偏好景点类型（按权重排序） |
| data.preference_types.rating_range | str | 偏好评分范围（如"4.5分以上"） |
| data.preference_types.location_area | array[str] | 偏好区域（如["市南区","市北区"]） |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "AI分析群体兴趣成功",
  "data": {
    "interest_tags": ["自然风光", "夜景", "美食"],
    "preference_types": {
      "spot_type": ["自然风光", "美食", "人文古迹"],
      "rating_range": "4.5分以上",
      "location_area": ["市南区", "市北区"]
    }
  }
}
```

#### 3.3.10 生成行程草案
##### 接口描述
基于协作空间的群体兴趣分析结果，生成多版行程草案供选择。

##### 接口信息
- URL：`/api/collaboration/generate-drafts`
- 请求方式：POST
- 权限：公开
- 备注：需传入space_id（补充参数，原需求未明确，默认必填）

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |

##### 请求示例
```json
{
  "space_id": "space_001"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | array[object] | 行程草案列表 |
| data[].draft_id | str | 草案ID |
| data[].name | str | 草案名称 |
| data[].description | str | 草案描述 |
| data[].daily_itinerary | array[object] | 多日行程规划（同3.1接口的data.daily_itinerary） |
| data[].preference_match | float | 偏好匹配度（0-100%） |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "生成行程草案成功",
  "data": [
    {
      "draft_id": "draft_001",
      "name": "青岛经典3日游（自然风光+美食版）",
      "description": "基于群体兴趣生成的经典行程，覆盖热门自然风光和美食打卡地",
      "daily_itinerary": [...],
      "preference_match": 95.0
    },
    {
      "draft_id": "draft_002",
      "name": "青岛慢生活3日游（小众打卡版）",
      "description": "侧重小众景点和本地生活体验的行程",
      "daily_itinerary": [...],
      "preference_match": 88.0
    }
  ]
}
```

#### 3.3.11 保存行程方案
##### 接口描述
将选定的行程草案保存为正式的行程方案，关联到协作空间。

##### 接口信息
- URL：`/api/collaboration/save-plan`
- 请求方式：POST
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 |
|--------|------|------|--------|------|
| space_id | str | 是 | "space_001" | 协作空间ID |
| name | str | 是 | "青岛3天游最终方案" | 行程方案名称 |
| description | str | 否 | "最终确定的青岛行程，包含所有成员感兴趣的地点" | 行程方案描述 |
| type | str | 是 | "group" | 方案类型（group=群体方案，personal=个人方案） |

##### 请求示例
```json
{
  "space_id": "space_001",
  "name": "青岛3天游最终方案",
  "description": "最终确定的青岛行程，包含所有成员感兴趣的地点",
  "type": "group"
}
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.draft_id | str | 行程方案唯一ID（原需求字段名，实际应为plan_id，兼容保留） |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "保存行程方案成功",
  "data": {
    "draft_id": "plan_001"
  }
}
```

### 3.4 POI详情模块接口
#### 3.4.1 获取POI详情
##### 接口描述
根据POI ID查询景点/地点的详细信息。

##### 接口信息
- URL：`/api/poi/detail`
- 请求方式：GET
- 权限：公开

##### 请求参数
| 参数名 | 类型 | 必选 | 示例值 | 说明 | 传递方式 |
|--------|------|------|--------|------|----------|
| poi_id | str | 是 | "poi_001" | POI唯一ID | Query参数 |

##### 请求示例
```
GET /api/poi/detail?poi_id=poi_001 HTTP/1.1
Host: 182.92.10.201:3000
Content-Type: application/json
```

##### 响应参数
| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | int | 响应状态码（200=成功） |
| message | str | 响应描述 |
| data | object | 业务数据 |
| data.name | str | POI名称 |
| data.address | str | 地址 |
| data.latitude | float | 纬度 |
| data.longitude | float | 经度 |
| data.type | str | 类型（参考高德POI类型映射） |
| data.description | str | 详细描述 |
| data.open_time | str | 开放时间（如"09:00-18:00"） |
| data.price | str | 价格（如"免费"、"50元/人"） |
| data.contact | str | 联系方式（电话/微信等） |
| data.images | array[str] | 图片URL数组 |
| data.video | str | 视频URL（可选） |
| data.score | float | 评分（1-5分） |
| data.comments | array[object] | 评论列表 |
| data.comments[].comment_id | str | 评论ID |
| data.comments[].user_id | str | 评论者ID |
| data.comments[].user_name | str | 评论者昵称 |
| data.comments[].content | str | 评论内容 |
| data.comments[].score | float | 评论者评分 |
| data.comments[].created_at | int | 评论时间戳 |

##### 成功响应示例
```json
{
  "code": 200,
  "message": "获取POI详情成功",
  "data": {
    "name": "五四广场",
    "address": "山东省青岛市市南区东海西路3号",
    "latitude": 36.06712,
    "longitude": 120.33934,
    "type": "自然风光",
    "description": "五四广场因纪念五四运动而得名，是青岛的地标性建筑之一，夜景尤为著名",
    "open_time": "全天开放",
    "price": "免费",
    "contact": "0532-12345678",
    "images": [
      "https://example.com/images/wusiguangchang_1.jpg",
      "https://example.com/images/wusiguangchang_2.jpg"
    ],
    "video": "https://example.com/videos/wusiguangchang.mp4",
    "score": 4.8,
    "comments": [
      {
        "comment_id": "comment_001",
        "user_id": "user_001",
        "user_name": "张三",
        "content": "青岛必打卡的地标，晚上的灯光秀超赞！",
        "score": 5.0,
        "created_at": 1735689900
      }
    ]
  }
}
```



### 3.5 原有模块接口
#### 3.5.1 用户模块
- 注册：`POST /api/user/register`
- 登录：`POST /api/user/login`
- 修改信息：`POST /api/user/update`
- 个人资料：`POST /api/user/profile`
- 上传头像：`POST /api/user/upload-avatar`
- 统计：`POST /api/user/statistic`

#### 3.5.2 聊天模块
- 发送消息：`POST /api/chat/send`
- 消息列表：`POST /api/chat/list`
- 单条消息：`POST /api/chat/get`
- 删除消息：`POST /api/chat/delete`
- 会话历史：`POST /api/chat/history`

#### 3.5.3 行程模块
- 添加行程：`POST /api/itinerary/add`
- 生成行程：`POST /api/itinerary/generate`
- 行程历史：`POST /api/itinerary/history`
- 删除行程：`POST /api/itinerary/delete`

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

### 6.4 测试POI模块接口（示例）
```python
import requests

# 获取POI详情
get_poi_url = "http://182.92.10.201:3000/api/poi/detail"
params = {"poi_id": "poi_001"}
response = requests.get(get_poi_url, params=params)
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
```

### 6.5 注意事项
1. 高德API调用有频率限制，生产环境建议添加缓存机制；
2. DeepSeek API需保证密钥有效且余额充足，否则AI解析功能失效；
3. 行程分组采用K-means聚类，可通过调整`max_iter`参数优化分组效果；
4. 路径规划优先使用高德接口数据，接口异常时自动采用直线距离估算；
5. 协作空间的标记/评论/点赞数据建议添加缓存，提升查询性能；
6. POI数据支持手动添加和高德API获取双来源，需保证数据格式统一；
7. WebSocket连接需处理断线重连，会话级数据建议关联用户ID持久化。