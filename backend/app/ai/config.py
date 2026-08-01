"""AI 提供商配置模型。

定义了 ``AIProviderConfig`` —— 一个 Pydantic v2 模型，集中描述连接 AI
大语言模型所需的全部参数。该配置在应用启动时由 ``core.lifespan`` 从环境
变量读取并注入到 ``AIService.configure()``，之后全局共享。

配置项说明：
- ``provider``：标识使用哪个 AI 服务商（deepseek / openai / siliconflow）。
- ``api_key``：调用 AI API 所需的 Bearer Token。
- ``model``：模型名称，如 ``deepseek-chat``。
- ``temperature``：采样温度，控制生成文本的随机性（0=确定性，1=高随机）。
- ``base_url``：AI API 的根地址，可替换为自部署或兼容服务。
- ``local_base_url`` / ``is_local_first``：预留的本地优先模式字段，
  当前版本未启用，保留以供未来本地模型推理扩展。
"""

from pydantic import BaseModel
from typing import Optional


class AIProviderConfig(BaseModel):
    """AI 提供商配置

    用 Pydantic BaseModel 承载所有 AI 调用参数，便于类型校验和序列化。
    该实例在应用启动时创建一次，之后作为只读配置传入 provider client。

    Attributes:
        provider: AI 服务商标识，当前支持 ``"deepseek"`` / ``"openai"``
            / ``"siliconflow"``，三者均兼容 OpenAI Chat Completions API。
        api_key: 用于鉴权的 API 密钥，会在 HTTP 请求头中以
            ``Authorization: Bearer <api_key>`` 形式发送。
        model: 调用的模型名称，不同提供商有不同的可用模型列表。
        temperature: 采样温度，值越高生成内容越发散，值越低越确定。
            教育场景默认 0.7，兼顾稳定性和多样性。
        base_url: AI API 根地址。若为 ``None`` 则回退到 DeepSeek 默认地址。
        local_base_url: 本地推理服务地址（预留字段，当前未启用）。
        is_local_first: 是否优先使用本地模型（预留字段，当前未启用）。
    """

    provider: str = "deepseek"            # 默认提供商：deepseek / openai / siliconflow（均兼容 OpenAI Chat Completions API）
    api_key: str = ""                     # 鉴权密钥，启动时由 lifespan 从环境变量读取并注入
    model: str = "deepseek-v4-flash"      # 默认模型名，不同提供商可用的模型列表不同
    temperature: float = 0.7              # 采样温度：值越低输出越确定，教育场景取 0.7 平衡稳定与多样性
    base_url: Optional[str] = None        # API 根地址，为 None 时回退到提供商默认地址
    local_base_url: Optional[str] = None  # 本地服务地址（自动检测）
    is_local_first: bool = False  # 本地优先模式
