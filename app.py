from flask import Flask
from routes import register_routes
from ws_handler import ws_ai_call
import json

# 初始化Flask应用
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# 注册所有路由
register_routes(app)

if __name__ == "__main__":
    # 测试WebSocket调用
    user_input = "周末和搭子去青岛玩3天，偏爱大海、美食，预算人均1000元，怎么舒服怎么出行，我们坐高铁去大连，在当地打车游玩。"
    result = ws_ai_call(user_input, "test_001")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 启动Flask服务
    # app.run(host="0.0.0.0", port=5000, debug=True)