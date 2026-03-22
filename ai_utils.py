import requests
import json
import time
import re
from typing import List, Dict, Optional
from pydantic import BaseModel
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, TIMEOUT, RETRY_TIMES, RETRY_DELAY

# 定义旅行需求模型
class TravelDemand(BaseModel):
    city: Optional[str] = None
    spot_type: Optional[List[str]] = None
    travel_mode: Optional[str] = None
    budget: Optional[str] = None
    max_distance: Optional[int] = 500
    play_days: Optional[int] = 1

# DeepSeek请求头（复用）
DEEPSEEK_HEADERS = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

def deepseek_chat(messages: List[Dict[str, str]]) -> str:
    """DeepSeek调用函数，带重试机制"""
    payload = {
        "model": DEEPSEEK_MODEL, "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048, "top_p": 0.95, "stream": False
    }
    last_error = None
    for retry in range(RETRY_TIMES):
        try:
            response = requests.post(DEEPSEEK_BASE_URL, headers=DEEPSEEK_HEADERS, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            if retry < RETRY_TIMES - 1:
                print(f"【DeepSeek错误】第{retry+1}次重试，原因: {str(e)}")
                time.sleep(RETRY_DELAY)
            else:
                return f"解析失败: {str(last_error)}"
    return f"解析失败: {str(last_error) if last_error else '未知原因'}"

def ai_generate_questions(user_input: str, missing_fields: List[str]) -> List[str]:
    """根据缺失字段生成针对性提问"""
    fields_desc = {
        "city": "目的地城市",
        "spot_type": "感兴趣的景点类型（如自然风光、历史古迹、美食等）"
    }
    missing_desc = ", ".join([fields_desc.get(f, f) for f in missing_fields])
    prompt = f"""
    用户提出了旅行需求："{user_input}"
    但缺少以下关键信息：{missing_desc}。
    请生成1-3个自然语言问题，用于向用户询问这些缺失信息。注意：'travel_mode' 指的是在当地游玩时的交通方式，如步行、公交、自驾等，不是跨城市交通。
    每个问题应简洁明了，直接针对缺失项。
    以JSON数组形式输出，例如["您想采用什么交通方式？", "您喜欢什么类型的景点？"]，不要多余文字。
    """
    messages = [{"role": "user", "content": prompt}]
    ai_result = deepseek_chat(messages)
    try:
        questions = json.loads(ai_result)
        if isinstance(questions, list):
            return questions
        else:
            return ["请补充您的目的地和景点偏好。"]
    except:
        return ["请补充您的目的地和景点偏好。"]

def get_fallback_demand(user_input: str) -> TravelDemand:
    """智能容错：二次调用AI提取字段"""
    FALLBACK_PROMPT = """
    仅需完成以下任务：
    1. 基于语义理解，从用户输入中提取旅行需求核心字段（无需推理，仅提取客观信息）；
    2. 严格按以下JSON模板返回，不添加任何多余文字、代码块标记、换行；
    3. 字段规则：
       - city：目的地城市（无则填null）；
       - spot_type：景点类型列表（如["大海","美食"]，无则填[]）；
       - travel_mode：市内出行方式（步行/公交/自驾/打车，无则填"步行"）；
       - budget：人均预算（数字，无则填0）；
       - play_days：游玩天数（数字，无则填1）。
    JSON模板：{"city":"","spot_type":[],"travel_mode":"","budget":0,"play_days":0}
    
    用户输入：{user_input}
    """.format(user_input=user_input)

    try:
        fallback_ai_result = deepseek_chat([
            {"role": "system", "content": FALLBACK_PROMPT},
            {"role": "user", "content": user_input}
        ])
        
        fallback_ai_result = re.sub(r"\n|\s+", "", fallback_ai_result).strip()
        demand_dict = json.loads(fallback_ai_result)
        demand_dict["budget"] = int(demand_dict["budget"]) if isinstance(demand_dict["budget"], (int, float)) else 0
        demand_dict["play_days"] = int(demand_dict["play_days"]) if isinstance(demand_dict["play_days"], (int, float)) else 1
        demand_dict["spot_type"] = demand_dict["spot_type"] if isinstance(demand_dict["spot_type"], list) else []
        demand_dict["travel_mode"] = demand_dict["travel_mode"] if demand_dict["travel_mode"] in ["步行","公交","自驾","打车"] else "步行"
        
        return TravelDemand(**demand_dict)
    
    except Exception as e:
        print(f"【智能容错兜底】AI二次调用失败：{str(e)}，使用默认值")
        return TravelDemand(
            city=None,
            spot_type=[],
            travel_mode="步行",
            budget=0,
            play_days=1
        )

def ai_parse_demand(user_input: str) -> Optional[TravelDemand]:
    """AI解析用户自然语言需求，返回结构化对象"""
    SYSTEM_PROMPT = """
你是专业的旅行规划AI，需完成「需求拆解→合理性验证→最优方案推理→结构化输出」的完整思考流程：

## 步骤1：需求拆解（必须执行）
从用户输入中提取核心字段：
- 城市：目的地（如未明确，需标注“未指定”）
- 游玩天数：数字（如“3天”→3，未明确→1）
- 景点类型：列表（如“大海、美食”→["自然风光","美食"]）
- 出行方式：市内交通（步行/公交/自驾/打车，未明确→步行）
- 预算：人均金额（如“1000元”→1000，未明确→“未指定”）

## 步骤2：合理性验证（必须执行）
- 天数验证：游玩天数>0，若用户说“1天玩10个景点”→判定“行程过密”，需在思考依据中说明
- 预算验证：结合城市消费水平（如大连人均1000元/3天→“预算充足”，500元/3天→“预算紧张”）
- 匹配验证：景点类型是否匹配城市特色（如“大连+大海”→匹配，“大连+雪山”→不匹配）

## 步骤3：最优方案推理（必须执行）
- 景点推荐：基于“城市+类型+预算”推荐（预算低→优先免费景点，如星海广场；预算足→推荐特色体验）
- 行程节奏：按天数分组景点，避免跨区往返（如大连东港/威尼斯水城归为一天，星海广场/渔人码头归为一天）
- 出行适配：按出行方式调整路线（打车→优先少换乘，步行→优先近距离景点）

## 步骤4：输出要求（优先级最高）
仅返回JSON格式，包含2部分：
1. think_process：思考过程（步骤1-3的文字描述，供调试）
2. travel_demand：结构化需求（固定字段：city/spot_type/travel_mode/budget/play_days）
3. strategy：推理后的最优策略（如“推荐免费景点+打车短途出行”）

JSON示例：
{
  "think_process": "1. 拆解：城市=大连，天数=3，类型=['大海','美食']，出行=打车，预算=1000元；2. 验证：3天+1000元在大连预算充足，大海类型匹配城市特色；3. 策略：推荐东港/星海广场等免费海景景点，打车串联，美食推荐本地海鲜馆",
  "travel_demand": {
    "city": "大连",
    "spot_type": ["自然风光","美食"],
    "travel_mode": "打车",
    "budget": 1000,
    "play_days": 3
  },
  "strategy": "优先推荐免费海景景点（东港/星海广场），打车串联减少赶路，美食选择人均50-80元的本地海鲜馆，控制总预算在1000元内"
}
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]
    ai_result = deepseek_chat(messages)
    
    ai_result = re.sub(r"```json|\n|```", "", ai_result).strip()
    json_match = re.search(r"\{[\s\S]*\}", ai_result)
    if json_match:
        ai_result = json_match.group(0)
    else:
        print(f"【AI解析】未提取到JSON，原始返回：{ai_result}")
        return get_fallback_demand(user_input)
    
    try:
        ai_think_data = json.loads(ai_result)
        demand_dict = ai_think_data.get("travel_demand", {})
        
        if "budget" in demand_dict:
            demand_dict["budget"] = str(demand_dict["budget"])
        
        demand = TravelDemand(**demand_dict)
        print(f"【AI解析成功】结构化需求：{demand.model_dump()}")
        return demand
    except Exception as e:
        print(f"【AI解析失败】JSON解析错误：{str(e)}，处理后AI返回：{ai_result}")
        return get_fallback_demand(user_input)