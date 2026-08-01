# Python ValueError 与 Pydantic 校验错误处理笔记（2026-08-01）

> 来源：当日与 AI 的问答式学习 + 代码实测验证。所有结论均在本项目环境
> （Python 3.10 + Pydantic 2.13.4 + FastAPI）中实证过，非仅凭文档记忆。
> 相关 bug 修复记录见 `docs/2026-08-01-email校验错误漏出原始英文.md`。

---

## 1. ValueError 是异常类，不是字典

- `raise ValueError("xxx")` 创建的是**异常对象**（`Exception` 的子类），核心内容是 `args` 元组，
  `str(e)` 取消息。它不是 dict。
- 我们看到「字典」，是 **Pydantic/FastAPI 层**把异常转换成了错误字典 + HTTP 响应。

## 2. Pydantic 错误字典的字段（核心）

Pydantic v2 把每个校验失败转成一个**错误字典**，`ValidationError.errors()` 返回它们的列表：

| 字段 | 含义 | 实测例子 |
|------|------|---------|
| `type` | 错误类型字符串 | `value_error` / `string_too_short` / `missing` / `int_parsing` |
| `loc` | 出错位置的路径元组 | `('body', 'username')` |
| `msg` | 人类可读消息 | `Value error, 用户名至少需要2个字符` |
| `input` | 触发校验的原始输入值 | `'x'` |
| `ctx` | 附加上下文（**可选**，内容随 type 变） | `{'error': ValueError(...)}` 或 `{'reason': '...'}` |

**`input` 的注意点**：就是客户端原样提交的值，未经过任何校验/转换，可以是任意类型。
反直觉特例：`missing`（缺字段）时 `input` 不是空，而是**整个传入的数据字典**。

## 3. ctx 是可选字段，键名随错误类型变化

实测过的三种：

| type | ctx 内容 | 说明 |
|------|---------|------|
| `value_error`（用户 raise ValueError） | `{'error': ValueError('...')}` | `error` 键 → 抛出的**异常对象**本身 |
| `value_error`（EmailStr 格式错误） | `{'reason': '...'}` | `reason` 键 → **字符串**原因 |
| `missing`（字段缺失） | 无 ctx 键 | 没有额外上下文 |

`ctx.error` 就是用户 `raise` 出来的那个异常对象（`str()` 才是消息）；
`ctx.reason` 是字符串。**不能假设 ctx 必有某个键**。

## 4. 两条报错途径 → ctx 键不同的根源（重要规则）

| 抛法 | ctx | 谁决定键名 |
|------|-----|-----------|
| `raise ValueError("...")`（用户代码） | `{'error': <异常对象>}` | pydantic-core 硬编码，永远 `error`；msg 自动加 `Value error, ` 前缀 |
| `raise PydanticCustomError(type, 模板, ctx)`（内置校验器） | 就是你传的 ctx | 自己传什么键就是什么 |

- 用户 `@field_validator` 里 `raise ValueError` → 框架自动打包，键固定 `error`。
- `PydanticCustomError` 是「自带错误元数据（type/消息模板/context）的异常类」，框架原样透传。
- EmailStr 内部用的是后者：`networks.py:1322` 抛 `PydanticCustomError('value_error',
  'value is not a valid email address: {reason}', {'reason': ...})` → 所以 ctx 是 `reason`。

## 5. V1 vs V2 的邮箱错误类型差异

- **V1**：`type == 'value_error.email'`（实测 `pydantic.v1` 确认）。
- **V2**：无专属邮箱错误类型，统一落回 `value_error`，靠 `ctx['reason']` 区分。
- 结论：代码里按 `value_error.email` 匹配的分支在 V2 下是**死代码**（本项目 bug 根因）。

## 6. 邮箱错误的可靠识别锚点

EmailStr 所有失败路径（超长 `networks.py:1305`、email-validator 校验失败 `:1322`）
共用同一消息模板：`value is not a valid email address: {reason}`。

可靠判定（本项目已采用）：
```python
if error_type == "value_error" and "valid email address" in message:
    return "请输入有效的邮箱地址"
```
- **不漏**：模板固定，短语必然出现（8 个场景实测全命中）；
- **不误**：其余 value_error（用户名/密码）消息是中文，不含该短语。
- 用**消息模板内容**而非 `ctx` 键名：`reason` 只是「当前依赖恰好只有 EmailStr 用它」，
  键名是约定不是契约。

## 7. 邮箱错误完整抛出链路（从最底层到响应）

```
① email_validator 库（英文原文在这）
   syntax.py:108  raise EmailSyntaxError("An email address must have an @-sign.")
   syntax.py:628  raise EmailSyntaxError("The part after the @-sign is not valid. It should have a period.")
   （EmailNotValidError 本身是 ValueError 的子类）
② pydantic 的 EmailStr 校验器
   networks.py:1320-1324  捕获后 raise PydanticCustomError('value_error',
   'value is not a valid email address: {reason}', {'reason': str(e.args[0])}) from e
③ FastAPI 路由层
   routing.py:747  raise RequestValidationError
④ 项目异常处理器（backend/app/core/exceptions.py:145）
   validation_exception_handler → format_validation_error → 返回中文 422
```

**关键点**：项目代码（`auth/schemas.py:34` 的 `email: EmailStr`）没有任何显式抛邮箱错误的代码，
整条链路由字段类型声明自动触发；对比 username/password 是项目自己写了
`@field_validator + raise ValueError`（抛错点在 `schemas.py:52-59 / 95-107`）。

**查看原始抛错点的方法**：API 层/异常处理器里拿不到原始 traceback——pydantic-core（Rust）
把异常重建为 `ValidationError`，`__cause__` 链在那里被切断。要看原始抛错点需绕过模型包装
直接调底层（`email_validator.validate_email('a@b', check_deliverability=False)` + `traceback.print_exc()`），
或直接打开源码文件看 raise 行。

## 8. FastAPI 异常处理机制（为什么「没写中间件」也能捕获）

- 捕获异常的 `ExceptionMiddleware` 是 **Starlette 内置**的，FastAPI 在
  `build_middleware_stack`（`fastapi/applications.py:1020`）自动安装，无需自己写。
- 用户只写两样东西：
  1. handler 函数（异常 → 响应 的转换）；
  2. 注册：`app.add_exception_handler(RequestValidationError, handler)`
     —— 源码本质就是 `self.exception_handlers[exc_class] = handler` 一个字典赋值
     （`starlette/applications.py:111`）。
- 运行时：异常抛出 → 中间件按异常类（沿 MRO）在注册表查 handler → 调用 →
  **handler 返回的 `JSONResponse` 就是最终发回客户端的 HTTP 响应**，没有后续处理。
- 不注册则用 FastAPI 默认处理器：422 + 原始错误对象数组（`{"detail": [{...}]}`）。

## 9. 其它当日要点

- **为什么 handler 里有循环**：`exc.errors()` 是**列表**，一个请求可同时挂多个校验错误
  （Pydantic 聚合所有错误不遇错即停），循环逐个转中文后 `"; ".join`。
- **校验错误都是 422**：`RequestValidationError` 固定 422（handler 硬编码）；
  422 专属于请求校验失败。业务 `HTTPException` 自定义（如 400）、认证失败 401、未捕获 500。
- **`_request` 下划线参数**：`_` 前缀是「故意不用」的约定（pylint 的 unused-argument 放行），
  不是语法。框架回调必须保留参数位置但名字自由；用到的参数叫 `request`、没用的叫 `_request`
  是自洽写法。FastAPI 处理器中未使用的注入参数建议一律 `_` 前缀。

## 10. 实践产出（同日）

- 修复 `backend/app/core/exceptions.py`：删除失效的 `value_error.email` 分支，
  改用消息模板匹配识别邮箱错误；docstring 同步更新。
- 回归验证：`backend/tests/test_auth.py` 20 passed，全量 `pytest tests/` 286 passed。
- 完整过程记录：`docs/2026-08-01-email校验错误漏出原始英文.md`。
