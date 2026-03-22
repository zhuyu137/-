from typing import Dict
from flask import request, jsonify
from ai_utils import ai_parse_demand, ai_generate_questions, TravelDemand
from amap_api import AmapAPI
from travel_utils import group_poi_by_days, generate_daily_route
from config import AMAP_WEB_KEY

def register_routes(app):
    """注册所有Flask路由"""
    
    def ai_amap_linkage(user_input: str) -> Dict:
        """核心联动函数：AI解析 + 高德POI + 行程规划"""
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
            # 3.1 搜索城市核心POI
            core_poi_all = []
            for st in demand.spot_type:
                core_poi = amap.poi_search(city=demand.city, spot_type=st, radius=10000)
                if core_poi:
                    core_poi_all.extend(core_poi)
            if not core_poi_all:
                return {"code": -2, "msg": "未找到相关景点", "data": None}
            
            # 3.2 按天数分组POI
            grouped_poi = group_poi_by_days(core_poi_all, demand.play_days)
            
            # 3.3 生成每日路线
            daily_itinerary = []
            for day_idx, day_poi in enumerate(grouped_poi, 1):
                day_route = generate_daily_route(amap, day_poi, demand.travel_mode)
                daily_itinerary.append({"day": day_idx, "itinerary": day_route})
            
            # 打印行程指引汇总
            print("\n===== 完整行程出行指引汇总 =====")
            for day in daily_itinerary:
                print(f"\n【第{day['day']}天】")
                for route in day["itinerary"]["routes"]:
                    print(f"从 {route['from']} → {route['to']}：")
                    for idx, step in enumerate(route["route"]["steps"], 1):
                        instruction = step.get("instruction") or step.get("desc") or "无指引"
                        print(f"  步骤{idx}：{instruction}")
        
        except Exception as e:
            print(f"【联动错误】高德数据获取失败: {str(e)}")
            return {"code": -2, "msg": "地图数据获取失败", "data": None}

        # 4. 返回结果
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "travel_demand": demand.model_dump(),
                "amap_data": amap_data,
                "daily_itinerary": daily_itinerary
            }
        }

    # 后端AI联动接口
    @app.route("/api/ai/travel/linkage", methods=["POST"])
    def travel_linkage_api():
        try:
            req_data = request.get_json()
            user_input = req_data.get("user_input", "")
            if not user_input or user_input.strip() == "":
                return jsonify({"code": -3, "msg": "用户输入不能为空", "data": None})
            result = ai_amap_linkage(user_input)
            return jsonify(result)
        except Exception as e:
            print(f"【接口错误】后端调用失败: {str(e)}")
            return jsonify({"code": -4, "msg": "AI接口内部错误", "data": None})

    # 行程路线获取接口
    @app.route("/get_travel_route", methods=["POST"])
    def get_travel_route():
        try: 
            user_input = request.json.get("user_input")
            if not user_input or user_input.strip() == "": 
                return jsonify({"code": 400, "msg": "用户输入不能为空", "data": None})
            linkage_result = ai_amap_linkage(user_input)
            daily_itinerary = linkage_result["data"].get("daily_itinerary", []) if linkage_result["data"] else []
            return jsonify({
                "code": 200 if linkage_result["code"] == 0 else linkage_result["code"],
                "msg": linkage_result["msg"],
                "data": daily_itinerary
            })
        except Exception as e:
            print(f"【/get_travel_route接口错误】{str(e)}")
            return jsonify({"code": 500, "msg": f"服务器错误：{str(e)}", "data": None})