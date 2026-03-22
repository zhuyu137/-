# 密钥配置
DEEPSEEK_API_KEY = "sk-e494b0844362415abd0d92f547900e74"
AMAP_WEB_KEY = "6286beb032c6105d5cc0ce09fade8849"

# API基础URL
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
AMAP_BASE_URL = "https://restapi.amap.com/v3"

# 网络配置
TIMEOUT = 60
RETRY_TIMES = 3
RETRY_DELAY = 2

# 高德POI类型映射（通用配置）
AMAP_TYPE_MAP = {
    "自然风光": "110000", 
    "历史古迹": "110000",
    "美食": "050000", 
    "非遗体验": "140000", 
    "网红打卡": "060000"
}

# 出行方式映射
TRAVEL_MODE_MAP = {
    "步行": "walk", 
    "公交": "bus", 
    "自驾": "drive", 
    "打车": "drive"
}

# 速度估算（km/h）
SPEED_MAP = {"步行": 5, "公交": 15, "自驾": 30, "打车": 30}