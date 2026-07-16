# AI Provider 协议与资源生命周期治理设计

## 背景

全局后端学习型治理已经完成 Judge0、认证、通用挑战和 Arena 两个批次。第四阶段开始治理 AI、配额与缓存。当前 `backend/app/services/ai.py` 同时包含教学提示、OpenAI-compatible HTTP 协议、重试、SSE 解析、共享连接池和业务 facade；`OpenAIProvider` 使用类级 `httpx.AsyncClient`，应用 shutdown 没有显式关闭它。同步与流式调用也各自维护一套裸异常和响应解析规则。

本批次只建立可靠的 AI Provider 外部边界。Hint 扣费、缓存、退款和并发购买编排留给 4B；它们应依赖本批次稳定的 provider 端口，而不是继续依赖 HTTP 细节。

## 目标

1. 将 OpenAI-compatible HTTP 请求、重试和响应解析从教学业务服务中分离。
2. 让网络、HTTP、协议和配置失败具有 FastAPI-independent 的类型化语义。
3. 让同步与流式请求只有一个重试所有者，并明确流式内容开始后的不可重试边界。
4. 让 HTTP client 可注入、可测试，并在应用 shutdown 时可靠关闭。
5. 保持现有 AI Router 状态码、响应字段、提示文本、模型参数和公开 `AIService` 教学方法不变。

## 方案比较

### 方案 A：只在现有 `ai.py` 内提取 helper

改动小，但 `AIService`、provider、HTTP client 和协议解析仍在同一模块，类级 client 生命周期也没有清晰所有者。它不能成为后续 hint 编排的稳定端口。

### 方案 B：Provider 协议包加 service-owned client（采用）

建立 `app.services.ai_provider` 包，分别承载端口、错误、OpenAI-compatible client 和 provider adapter。`AIService` 保留业务 facade，并拥有一个可复用的 HTTP client；reconfigure 只替换轻量 provider adapter，shutdown 关闭共享 client。该方案不需要数据库或公开 API 变化，也与已验证的 Judge0 client/facade 模式一致。

### 方案 C：同时重写 hint 扣费、缓存和 provider

一次覆盖范围最广，但会把外部协议、SSE、数据库短事务和补偿逻辑绑在同一审查面，无法可靠定位回归。分布式 hint 幂等还需要独立持久化设计，不适合与 provider 拆分同批完成。

## 模块边界

### `app.services.ai_provider.errors`

提供纯领域异常，不导入 FastAPI：

- `AIProviderError`：所有预期 provider 失败的基类。
- `AIProviderConfigurationError`：provider 未配置或 provider 名称不受支持。
- `AIProviderNetworkError`：连接、超时或网络错误在重试耗尽后失败。
- `AIProviderHTTPError`：上游返回非成功 HTTP；保留 `status_code` 和截断后的安全响应摘要。
- `AIProviderProtocolError`：成功 HTTP 的 JSON/SSE 结构不符合协议；流式解析时记录 `content_started`。
- `AIProviderStreamError`：流已建立后读取中断；保留是否已经产生内容的语义供 4B 补偿使用。

异常消息不包含 API key、Authorization header 或完整上游响应。

### `app.services.ai_provider.base`

定义 `AIProvider` 抽象端口：

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_explanation(self, prompt: str) -> str: ...

    @abstractmethod
    async def review_code(self, code: str, language: str) -> str: ...

    @abstractmethod
    def stream_generate(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]: ...
```

端口不暴露 `httpx.Response`，业务消费者只处理文本块或类型化失败。

### `app.services.ai_provider.client`

`OpenAICompatibleClient` 是唯一 HTTP 协议所有者：

- 构造参数包含 `base_url`、不可变 provider 配置、可选注入的 `httpx.AsyncClient` 和可注入 sleep 函数。
- 未注入 client 时惰性创建，并记录 `_owns_client=True`；注入 client 永不由该实例关闭。
- 非流式 `complete(messages)` 返回字符串。
- 流式 `stream(messages)` 返回文本块 async generator，并保证 response 在所有退出路径关闭。
- URL 统一为规范化的 `<base_url>/chat/completions`，避免重复或缺失 `/`。
- 每个逻辑请求在第一次 await 前快照 URL、headers 和 payload；Admin reconfigure 只影响之后的新请求，不改变同一请求的重试目标。

### `app.services.ai_provider.openai`

`OpenAICompatibleProvider` 只负责教学消息组装：

- `generate_explanation` 使用现有编程教师 system prompt。
- `review_code` 使用现有代码审查 system prompt 和用户模板。
- `stream_generate` 原样委托 client。

Provider 不持有数据库、FastAPI request 或全局 settings。

### `app.services.ai.AIService`

`AIService` 继续拥有现有业务方法和兼容属性：

- `configure(config)` 保持同步，使用 factory 创建 provider adapter。
- service 复用一个 internally-owned `httpx.AsyncClient`；配置变化不创建新的连接池。
- 测试可在构造 `AIService(http_client=...)` 时注入 client，service 不关闭外部 client。
- `_require_provider()` 取代重复 `assert self._provider is not None`。每个公开教学方法先保留现有“未配置”友好返回；通过 guard 后若状态仍不一致，才抛 `AIProviderConfigurationError`。
- `aclose()` 只关闭 service 自己创建的 client，且可重复调用。
- `OpenAIProvider` 兼容导出在本批保留为 `OpenAICompatibleProvider` 的别名，防止现有内部测试或导入在同批突然破坏；文档标记它为过渡别名。

## 重试与失败契约

重试总次数固定为 3 次，退避为 1 秒、2 秒。测试注入无等待 sleep。

| 失败 | 非流式 | 流式连接/握手 | 已开始读取流 |
|---|---|---|---|
| connect/timeout | 最多 3 次 | 最多 3 次 | 不重试 |
| HTTP 5xx | 最多 3 次 | 最多 3 次 | 不适用 |
| HTTP 4xx | 不重试 | 不重试 | 不适用 |
| JSON/SSE 协议错误 | 不重试 | 不重试 | 不重试 |
| 读取中断 | 不适用 | 不适用 | 不重试并关闭 response |

HTTP 5xx 最终抛 `AIProviderHTTPError`，网络耗尽抛 `AIProviderNetworkError`，协议不完整抛 `AIProviderProtocolError`。Provider client 不把失败转换成 HTTP 状态码；现有 Router 仍维持当前通用 500 或 SSE fallback，4B 再为 hint 显式映射补偿语义。

## 响应解析

非流式成功响应必须满足：

```text
choices -> 非空 list -> choices[0].message.content -> str
```

缺字段、错误类型、空 choices 或不可解析 JSON 均为 `AIProviderProtocolError`。

SSE 只处理 `data: ` 行：

- `[DONE]` 正常结束。
- 连接在 `[DONE]` 前结束视为 `AIProviderStreamError`，并记录是否已经产生内容。
- 空 keepalive 行忽略。
- 每个 JSON data item 必须包含 `choices[0].delta`；`content` 缺失视为空块，结构错误视为协议失败。
- response 在正常结束、consumer 提前关闭、解析失败和读取异常时都必须 `aclose()`。

## 应用生命周期

`configure_ai_service(settings)` 保持同步配置职责。FastAPI lifespan 使用：

```python
configure_ai_service(settings)
try:
    yield
finally:
    await ai_service.aclose()
```

Admin 配置更新继续同步调用 `ai_service.configure(fresh_config)`。因为 provider adapter 共享 service-owned client，reconfigure 不泄漏旧连接池，也不要求 Router 管理资源。

## 兼容约束

- 保持 `/api/ai/choice-explanation`、`/code-review`、`/chat`、`/choice-analysis`、配置和状态路由现有状态码与响应字段。
- 保持所有现有 system/user prompt、temperature、model、base URL 默认值和 Authorization 形式。
- 保持 stream 输出文本块，不在本批修改 SSE Router framing。
- 不修改 hint 成本、Core 账本、缓存模型、退款、Admin quota、embedding、前端或数据库。
- 不把外部 provider 原始响应正文或密钥写入异常/日志；只保留最多 500 字符的安全摘要。

## 测试策略

新增 provider client 的 `httpx.MockTransport` 测试：

1. 非流式请求的 URL、headers、model、messages、temperature 与内容提取。
2. 连接错误和 5xx 恰好重试 3 次，退避为 `[1, 2]`。
3. 4xx、协议错误不重试且抛正确类型。
4. 流式握手 5xx 可重试；首个成功 response 后读取失败不重启逻辑流。
5. 正常、协议失败、consumer 提前关闭都关闭 response。
6. injected client 不被关闭；owned client 在 `aclose()` 后关闭且重复关闭安全。
7. `AIService` configure、未配置错误、reconfigure 连接复用和 lifespan shutdown。
8. 现有 AI Router 与 mastery/hint policy 回归保持通过。

最终门槛包括完整后端测试零跳过、Pyright、FastAPI/Next.js 实际启动和受影响 AI 路由请求、CodeGraph 同步与 Rule 10 自审。

## 分批后续

4B 将在本批端口之上治理 challenge hint：cache-first、短事务扣费、生成锁、缓存保存、失败退款和 SSE typed event。多 worker 的严格购买幂等需要持久化 reservation/状态设计；由于项目当前没有可执行 Alembic 版本链，它不会用临时 sentinel 或长时间数据库锁伪装解决。

之后的 4C 再推广到 embedding、mastery quiz、tag extraction、notes refinement 和 Admin quota，避免一次性修改所有 AI 消费者。

## 风险与证据边界

- MockTransport 能证明协议和重试，不证明真实 provider 可用；live 验证只要求无密钥配置下服务启动与 Router 契约正常。
- shutdown 测试证明 client 所有权，不证明进程强制终止时的网络行为。
- 本批不解决 hint 多 worker 双重扣费；该风险必须保留到 4B/持久化迁移设计，不能在完成记录中声明已解决。
