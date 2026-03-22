from typing import Dict
import time
import json
import traceback
from ai_utils import ai_parse_demand, ai_generate_questions
from amap_api import AmapAPI
from travel_utils import group_poi_by_days, generate_daily_route
from config import AMAP_WEB_KEY

def ai_amap_linkage(user_input: str) -> Dict:
    """复用核心联动逻辑（与routes.py保持一致）"""
    from ai_utils import ai_parse_demand, ai_generate_questions, TravelDemand
    # 1. AI解析用户需求
    demand = ai_parse_demand(user_input)
    if not demand:
        return {"code": -1, "msg": "AI解析用户需求失败", "data": None}
    
    # 检查缺失字段
    missing = []
    if not demand.city:
        missing.append("city")
    if not demand.spot_type or len(demand.spot_type) == 0:
        missing.append("spot_type")
    if not demand.travel_mode:
        missing.append("travel_mode")  
    if missing:
        questions = ai_generate_questions(user_input, missing)
        return {
            "code": -5,
            "msg": "need_more_info",
            "data": {
                "questions": questions,
                "hint": "请回答以上问题以便为您规划行程"
            }
        }
    
    # 2. 初始化高德API
    amap = AmapAPI(AMAP_WEB_KEY)
    amap_data = {"poi_list": [], "daily_itinerary": []}
    
    # 3. 获取POI并生成行程
    try:
        core_poi_all = []
        for st in demand.spot_type:
            core_poi = amap.poi_search(city=demand.city, spot_type=st, radius=10000)
            if core_poi:
                core_poi_all.extend(core_poi)
        if not core_poi_all:
            return {"code": -2, "msg": "未找到相关景点", "data": None}
        
        grouped_poi = group_poi_by_days(core_poi_all, demand.play_days)
        daily_itinerary = []
        for day_idx, day_poi in enumerate(grouped_poi, 1):
            day_route = generate_daily_route(amap, day_poi, demand.travel_mode)
            daily_itinerary.append({"day": day_idx, "itinerary": day_route})
        
    except Exception as e:
        print(f"【联动错误】高德数据获取失败: {str(e)}")
        return {"code": -2, "msg": "地图数据获取失败", "data": None}

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "travel_demand": demand.model_dump(),
            "amap_data": amap_data,
            "daily_itinerary": daily_itinerary
        }
    }

def ws_ai_call(user_input: str, itinerary_id: str) -> Dict:
    """
    WebSocket专属AI调用入口
    :param user_input: 用户旅行需求（自然语言）
    :param itinerary_id: 行程唯一ID
    :return: WebSocket响应格式
    """
    # 参数校验
    if not itinerary_id or not isinstance(itinerary_id, str):
        return {
            "msg_type": "ai_travel_result",
            "code": -100, 
            "msg": "行程ID不能为空且必须为字符串",
            "payload": {},
            "itinerary_id": itinerary_id or "invalid_id",
            "timestamp": int(time.time())
        }
    if not user_input or user_input.strip() == "":
        return {
            "msg_type": "ai_travel_result",
            "code": -101,
            "msg": "用户旅行需求不能为空",
            "payload": {},
            "itinerary_id": itinerary_id,
            "timestamp": int(time.time())
        }

    try:
        core_result = ai_amap_linkage(user_input)
        ws_result = {
            "msg_type": "ai_travel_result",
            "code": core_result["code"],
            "msg": core_result["msg"],
            "payload": core_result["data"] if core_result["data"] else {},
            "itinerary_id": itinerary_id,
            "timestamp": int(time.time())
        }
        print(f"【WS-AI调用成功】行程ID：{itinerary_id}，用户输入：{user_input[:20]}...")
        return ws_result
    except Exception as e:
        error_stack = traceback.format_exc()
        print(f"【WS-AI调用失败】行程ID：{itinerary_id}，错误栈：{error_stack}")
        return {
            "msg_type": "ai_travel_result",
            "code": -99,
            "msg": f"AI模块调用失败：{str(e)}",
            "payload": {},
            "itinerary_id": itinerary_id,
            "timestamp": int(time.time())
        }