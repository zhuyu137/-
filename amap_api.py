import requests
from typing import List, Dict, Optional
from config import AMAP_BASE_URL, AMAP_TYPE_MAP

class AmapAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = AMAP_BASE_URL

    def geo_code(self, address: str, city: str) -> Optional[Dict]:
        """地理编码：地址转经纬度"""
        params = {"address": address, "city": city, "key": self.api_key, "output": "json"}
        try:
            res = requests.get(f"{self.base_url}/geocode/geo", params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data["status"] == "1" and len(data["geocodes"]) > 0:
                loc = data["geocodes"][0]["location"].split(",")
                return {"lng": loc[0], "lat": loc[1], "address": data["geocodes"][0]["formatted_address"]}
            return None
        except Exception as e:
            print(f"【高德错误】地理编码失败: {str(e)}")
            return None

    def poi_search(self, city: str, spot_type: str, radius: int = 5000, custom_poi: List[Dict] = []) -> Optional[List[Dict]]:
        """POI搜索：按城市+景点类型找推荐地点"""
        amap_type = AMAP_TYPE_MAP.get(spot_type, "110000")
        params = {
            "city": city, "types": amap_type, "radius": radius,
            "key": self.api_key, "output": "json", "page_size": 10
        }
        try:
            res = requests.get(f"{self.base_url}/place/text", params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            poi_list = []
            # 1. 添加高德搜索的POI
            if data["status"] == "1" and len(data["pois"]) > 0:
                for poi in data["pois"]:
                    poi_list.append({
                        "name": poi["name"], "address": poi["address"],
                        "lng": poi["location"].split(",")[0], "lat": poi["location"].split(",")[1],
                        "type": poi["type"], "distance": 0
                    })
            # 2. 添加用户自定义POI
            for custom in custom_poi:
                if "name" in custom and "lng" in custom and "lat" in custom:
                    poi_list.append({
                        "name": custom["name"],
                        "address": custom.get("address", f"{city}自定义景点"),
                        "lng": custom["lng"],
                        "lat": custom["lat"],
                        "type": spot_type,
                        "distance": 0
                    })
            return poi_list if poi_list else None
        except Exception as e:
            print(f"【高德错误】POI搜索失败: {str(e)}")
            return None

    def poi_around_search(self, center_lng: str, center_lat: str, spot_type: str, radius: int = 5000) -> Optional[List[Dict]]:
        """周边搜索：基于中心点搜索同类型POI"""
        amap_type = AMAP_TYPE_MAP.get(spot_type, "110000")
        params = {
            "location": f"{center_lng},{center_lat}",
            "keywords": "",
            "types": amap_type,
            "radius": radius,
            "sortrule": "distance",
            "key": self.api_key,
            "output": "json",
            "page_size": 10
        }
        try:
            res = requests.get(f"{self.base_url}/place/around", params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            poi_list = []
            if data["status"] == "1" and len(data["pois"]) > 0:
                for poi in data["pois"]:
                    poi_list.append({
                        "name": poi["name"],
                        "address": poi["address"],
                        "lng": poi["location"].split(",")[0],
                        "lat": poi["location"].split(",")[1],
                        "type": poi["type"],
                        "distance": int(poi.get("distance", 0)) if poi.get("distance") else 0,
                        "source": "amap_around"
                    })
            return poi_list if poi_list else None
        except Exception as e:
            print(f"【高德错误】周边搜索失败: {str(e)}")
            return None

    def direction_plan(self, origin: str, destination: str, travel_mode: str = "walk") -> Optional[Dict]:
        """路径规划：起点→终点（经纬度）"""
        from config import TRAVEL_MODE_MAP
        amap_mode = TRAVEL_MODE_MAP.get(travel_mode, "walk")
        params = {
            "origin": origin, "destination": destination,
            "type": amap_mode, "key": self.api_key, "output": "json"
        }
        try:
            res = requests.get(f"{self.base_url}/direction/{amap_mode}", params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data["status"] == "1":
                route = data["route"]["paths"][0]
                return {
                    "distance": f"{int(route['distance'])/1000}km",
                    "duration": f"{int(route['duration'])/60}min",
                    "steps": route["steps"]
                }
            return None
        except Exception as e:
            print(f"【高德错误】路径规划失败: {str(e)}")
            return None