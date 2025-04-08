from flask import Flask
from flask_cors import CORS
from app.core.config import settings

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 导入并注册 API 路由
from app.api.api import app as api_app
app.register_blueprint(api_app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 