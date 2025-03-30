from .model_factory import ModelFactory
from .deepseek_model import DeepseekModel
from .perspective_model import PerspectiveModel

# 注册可用的模型
ModelFactory.register_model("deepseek", DeepseekModel)
ModelFactory.register_model("perspective", PerspectiveModel)

# 导出主要类
__all__ = [
    "ModelFactory",
    "DeepseekModel",
    "PerspectiveModel"
] 