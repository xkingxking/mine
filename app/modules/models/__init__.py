from .base_model import BaseModel
from .model_factory import ModelFactory
from .deepseek_model import DeepseekModel
from .perspective_model import PerspectiveModel
from .chatgpt_model import ChatGPTModel
from .doubao_model import DoubaoModel
from .qwen_model import QwenModel
from .llama_model import LlamaModel


# 注册所有模型
ModelFactory.register_model("deepseek-v3", DeepseekModel)
ModelFactory.register_model("perspective", PerspectiveModel)
ModelFactory.register_model("chatgpt", ChatGPTModel)
ModelFactory.register_model("doubao", DoubaoModel)
ModelFactory.register_model("qwen", QwenModel)
ModelFactory.register_model("llama", LlamaModel)


# 导出主要类
__all__ = [
    "BaseModel",
    "ModelFactory",
    "DeepseekModel",
    "PerspectiveModel",
    "ChatGPTModel",
    "DoubaoModel",
    "QwenModel",
    "LlamaModel",
] 