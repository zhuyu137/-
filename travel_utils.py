import math
import random
from typing import List, Dict
from itertools import permutations
from config import SPEED_MAP
from amap_api import AmapAPI

def calculate_distance(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """计算两个经纬度之间的直线距离（米）"""
    # 经纬度转弧度
    lng1, lat1, lng2, lat2 = map(math.radians, [float(lng1), float(lat1), float(lng2), float(lat2)])
    # 地球半径（米）
    R = 6371000
    # 哈辛公式计算直线距离
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

def group_poi_by_days(poi_list: List[Dict], play_days: int) -> List[List[Dict]]:
    """基于K-means聚类将POI分成 play_days 组（每组对应一天）"""
    print(f"【POI分组-入参】POI总数：{len(poi_list)}，游玩天数：{play_days}")
    if not poi_list or play_days <= 0:
        return []
    if len(poi_list) <= play_days:
        return [[poi] for poi in poi_list]

    points = [(float(p['lng']), float(p['lat'])) for p in poi_list]
    
    # 简单K-means实现
    def kmeans(points, k, max_iter=10):
        centers = random.sample(points, k)
        for _ in range(max_iter):
            clusters = [[] for _ in range(k)]
            for p in points:
                dists = [math.hypot(p[0]-c[0], p[1]-c[1]) for c in centers]
                idx = dists.index(min(dists))
                clusters[idx].append(p)
            new_centers = []
            for c in clusters:
                if c:
                    avg_x = sum(pt[0] for pt in c) / len(c)
                    avg_y = sum(pt[1] for pt in c) / len(c)
                    new_centers.append((avg_x, avg_y))
                else:
                    new_centers.append(random.choice(points))
            if new_centers == centers:
                break
            centers = new_centers
        return clusters, centers
    
    clusters, _ = kmeans(points, play_days)
    poi_groups = [[] for _ in range(play_days)]     
    for i, p in enumerate(points):
        for idx, cluster in enumerate(clusters):
            if p in cluster:
                poi_groups[idx].append(poi_list[i])
                break
    # 过滤空组
    poi_groups = [g for g in poi_groups if g]
    print(f"【POI分组-成功】实际分组数：{len(poi_groups)}，各组POI数：{[len(g) for g in poi_groups]}")
    return poi_groups

def generate_daily_route(amap: AmapAPI, day_poi: List[Dict], travel_mode: str) -> Dict:
    """生成单日最优路线（枚举所有顺序，取总距离最短）"""
    if len(day_poi) < 1:
        return {"poi_list": [], "routes": [], "total_distance": 0.0, "total_duration": 0.0}
    if len(day_poi) == 1:
        return {
            "poi_list": day_poi,
            "routes": [],
            "total_distance": 0.0,
            "total_duration": 0.0
        }
    
    # 预处理：构建距离矩阵
    n = len(day_poi)
    dist_matrix = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            d = calculate_distance(
                float(day_poi[i]['lng']), float(day_poi[i]['lat']),
                float(day_poi[j]['lng']), float(day_poi[j]['lat'])
            )
            dist_matrix[i][j] = dist_matrix[j][i] = d
    
    # 枚举所有排列，找总距离最短的顺序
    best_order = None
    best_dist = float('inf')
    for perm in permutations(range(n)):
        total = sum(dist_matrix[perm[k]][perm[k+1]] for k in range(n-1))
        if total < best_dist:
            best_dist = total
            best_order = perm
    
    # 重排POI
    sorted_poi = [day_poi[i] for i in best_order]
    # 调用高德路径规划生成路线
    routes = []
    total_distance = 0.0
    total_duration = 0.0
    speed = SPEED_MAP.get(travel_mode, 5)
    
    for i in range(len(sorted_poi)-1):
        origin = f"{sorted_poi[i]['lng']},{sorted_poi[i]['lat']}"
        dest = f"{sorted_poi[i+1]['lng']},{sorted_poi[i+1]['lat']}"
        straight_dist = calculate_distance(
            float(sorted_poi[i]['lng']), float(sorted_poi[i]['lat']),
            float(sorted_poi[i+1]['lng']), float(sorted_poi[i+1]['lat'])
        ) / 1000 
        
        try:
            route = amap.direction_plan(origin, dest, travel_mode=travel_mode)
            print(f"【高德路线规划】起点：{sorted_poi[i]['name']}，终点：{sorted_poi[i+1]['name']}，接口返回：{route}")
            if route and "steps" in route:
               print(f"  → 具体出行指引：")
               for idx, step in enumerate(route["steps"], 1):
                   instruction = step.get("instruction") or step.get("desc") or "无指引"
                   print(f"    步骤{idx}：{instruction}")
            
            if route:
                dist_km = float(route["distance"].replace("km", ""))
                dur_min = float(route["duration"].replace("min", ""))
                routes.append({
                    "from": sorted_poi[i]["name"],
                    "to": sorted_poi[i+1]["name"],
                    "route": {
                        "distance": f"{dist_km:.1f}km",
                        "duration": f"{dur_min:.0f}min",
                        "steps": route["steps"]
                    }
                })
                total_distance += dist_km
                total_duration += dur_min
            else:
                # 无数据时估算
                est_dist_km = round(straight_dist * 1.3, 1)
                est_dur_min = round(est_dist_km / speed * 60)
                routes.append({
                    "from": sorted_poi[i]["name"],
                    "to": sorted_poi[i+1]["name"],
                    "route": {
                        "distance": f"{est_dist_km}km",
                        "duration": f"{est_dur_min}min",
                        "steps": [{"instruction": f"沿常规路线前往，约{est_dist_km}公里"}]
                    }
                })
                total_distance += est_dist_km
                total_duration += est_dur_min
        except Exception as e:
            print(f"【高德路线规划异常】起点：{sorted_poi[i]['name']}，终点：{sorted_poi[i+1]['name']}，原因：{str(e)}")
            est_dist_km = round(straight_dist * 1.3, 1)
            est_dur_min = round(est_dist_km / speed * 60)
            routes.append({
                "from": sorted_poi[i]["name"],
                "to": sorted_poi[i+1]["name"],
                "route": {
                    "distance": f"{est_dist_km}km",
                    "duration": f"{est_dur_min}min",
                    "steps": [{"instruction": "路线数据暂缺，按常规路线规划"}]
                }
            })
            total_distance += est_dist_km
            total_duration += est_dur_min
    
    return {
        "poi_list": sorted_poi,
        "routes": routes,
        "total_distance": round(total_distance, 1),
        "total_duration": round(total_duration, 0)
    }