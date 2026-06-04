# Day 2 学习笔记：Pydantic API 契约与 mock /chat

## 1. 今天完成了什么

Day 2 的目标是先固定 `/chat` 的请求和响应结构，而不是急着实现 RAG 检索。

今天完成了：

- 新增 `Evidence` schema
- 新增 `TraceInfo` 和 `trace_id` 生成函数
- 新增 `ChatRequest` 和 `ChatResponse`
- 在 `app/api/routes.py` 中实现 `POST /chat`
- 编写 `/chat` API 契约文档
- 编写 `/chat` 契约测试
- 用 pytest 和真实 curl 完成验收

今天的 `/chat` 仍然是 mock 模式。它不会读取文档、不会检索 evidence、不会生成真正的 RAG answer。这样做是为了先把接口结构固定下来，后续 Day 5 再把它接到 naive RAG pipeline。

## 2. 新建和修改了哪些文件

### `app/schemas/evidence.py`

这个文件定义了证据对象 `Evidence`。

代码：

```python
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=1.0)
```

通俗理解：`Evidence` 表示“这个答案依据了哪段材料”。

字段含义：

- `source`：证据来自哪个文件或数据源，比如 `return_policy.md`
- `content`：具体证据文本
- `score`：相关性分数，范围是 `0.0` 到 `1.0`

为什么现在就定义 `Evidence`？

因为企业级 RAG 不能只返回一个答案。后续我们需要知道：

- 答案依据了什么
- 证据是否相关
- 模型有没有编造
- citation correctness 和 faithfulness 怎么评估

所以 Day 2 就先把 `evidence` 字段放进响应契约里。

### `app/schemas/trace.py`

这个文件定义 trace 相关结构。

代码：

```python
from uuid import uuid4

from pydantic import BaseModel, Field


class TraceInfo(BaseModel):
    trace_id: str = Field(..., min_length=1)


def new_trace_id() -> str:
    return f"trace_{uuid4().hex}"
```

`trace_id` 的作用是给每次请求一个唯一编号。

通俗理解：如果用户说“刚才那个回答不对”，我们需要有办法定位“刚才那次请求”。`trace_id` 就是这次请求的追踪号。

现在的 trace 很简单，只是一个 UUID。以后可以继续扩展：

- 记录 retrieval latency
- 记录 intent routing
- 记录 fallback reason
- 记录 LLM 或 mock LLM 阶段耗时

### `app/schemas/chat.py`

这个文件定义 `/chat` 的请求和响应。

核心代码：

```python
class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=2, max_length=1000)
```

`ChatRequest` 是客户端发给 `/chat` 的请求结构。

字段含义：

- `user_id`：用户 ID
- `session_id`：会话 ID
- `query`：用户问题

这里对 `query` 做了长度限制：

- 最少 2 个字符
- 最多 1000 个字符

这样可以挡住空问题、太短的问题和过长输入。

继续看 validator：

```python
@field_validator("user_id", "session_id", "query", mode="before")
@classmethod
def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value
```

这段代码的作用是去掉用户输入前后的空格。

例如：

```json
{
  "query": "  退货  "
}
```

会被处理成：

```text
退货
```

再看过短 query 校验：

```python
@field_validator("query")
@classmethod
def query_must_have_enough_text(cls, value: str) -> str:
    if len(value) < 2:
        raise ValueError("query must contain at least 2 non-whitespace characters")
    return value
```

这个校验确保：

- `"   "` 会被 strip 成 `""`，然后校验失败
- `"a"` 长度只有 1，也会失败

失败时 FastAPI 会自动返回 HTTP `422`。

响应结构：

```python
class ChatResponse(BaseModel):
    answer: str
    intent: str
    evidence: list[Evidence] = Field(default_factory=list)
    fallback: bool
    fallback_reason: str | None = None
    trace_id: str
```

字段含义：

- `answer`：最终回答
- `intent`：问题意图
- `evidence`：证据列表
- `fallback`：是否进入 fallback
- `fallback_reason`：为什么 fallback
- `trace_id`：请求追踪 ID

为什么 `evidence` 用 `default_factory=list`？

因为 Python 里不推荐把空列表直接作为默认值。`default_factory=list` 表示每个响应对象都会创建自己的新列表，避免多个对象共享同一个列表。

### `app/api/routes.py`

这个文件新增了 `/chat` 路由。

新增代码：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        answer=(
            "This is a Day 2 mock response. The /chat API contract is ready, "
            "but retrieval and evidence-grounded generation are not connected yet."
        ),
        intent="mock_intent",
        evidence=[],
        fallback=True,
        fallback_reason="Day 2 mock mode: retrieval is not connected yet.",
        trace_id=new_trace_id(),
    )
```

这段代码的重点：

- `request: ChatRequest` 告诉 FastAPI：请求体必须符合 `ChatRequest`
- `response_model=ChatResponse` 告诉 FastAPI：响应必须符合 `ChatResponse`
- `trace_id=new_trace_id()` 为每次请求生成追踪号

为什么 Day 2 设置 `fallback=True`？

因为现在还没有真正的 retrieval，也没有 evidence。如果我们返回 `fallback=False`，就好像系统已经正常检索并回答了，这不诚实。

所以 Day 2 的 mock response 明确告诉用户：

```text
retrieval is not connected yet
```

这符合项目原则：不要编造 evidence，不要假装已经完成 RAG。

### `docs/contracts/query_api.md`

这个文件记录 API 契约。

它写清楚了：

- `GET /health`
- `POST /chat`
- request JSON 示例
- response JSON 示例
- 每个字段的含义
- validation 行为
- Day 2 当前边界

为什么要写 API 契约文档？

因为后续 Day 3、Day 4、Day 5 都会逐步实现 loader、retriever 和 RAG pipeline，但 `/chat` 的响应结构不应该被推翻重写。

先写契约，相当于先把“接口地基”固定住。

### `tests/test_chat_contract.py`

这个文件测试 `/chat` 契约。

测试 1：合法请求返回稳定结构

```python
def test_chat_returns_stable_mock_contract() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u1",
            "session_id": "s1",
            "query": "退货政策是什么？",
        },
    )
```

它验证：

- HTTP 状态码是 200
- 返回字段正好包含 `answer`、`intent`、`evidence`、`fallback`、`fallback_reason`、`trace_id`
- `intent` 是 `mock_intent`
- `evidence` 是空列表
- `fallback` 是 true
- `trace_id` 以 `trace_` 开头

测试 2：前后空格会被 strip

```python
def test_chat_strips_whitespace_from_query() -> None:
```

这个测试保证 `"  退货  "` 不会因为前后空格导致错误。

测试 3：空 query 被拒绝

```python
def test_chat_rejects_empty_query() -> None:
```

输入 `"   "`，预期返回 422。

测试 4：过短 query 被拒绝

```python
def test_chat_rejects_too_short_query() -> None:
```

输入 `"a"`，预期返回 422。

## 3. 今天没有做什么

Day 2 明确没有做：

- 没有读取电商 policy 文档
- 没有 chunking
- 没有 embedding
- 没有 vector store
- 没有 retriever
- 没有 prompt builder
- 没有 answer generator
- 没有让 `/chat` 返回真实 evidence

这些是后续 Day 3 到 Day 5 的内容。

## 4. 怎么验收的

### 只跑 Day 2 测试

```powershell
python -m pytest tests/test_chat_contract.py -q
```

结果：

```text
4 passed
```

### 跑 Day 1 + Day 2 测试

```powershell
python -m pytest tests/test_health.py tests/test_chat_contract.py -q
```

结果：

```text
5 passed
```

### 跑当前全部测试

```powershell
python -m pytest -q
```

结果：

```text
5 passed
```

### 启动服务

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 手动请求 `/chat`

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

返回：

```json
{
  "answer": "This is a Day 2 mock response. The /chat API contract is ready, but retrieval and evidence-grounded generation are not connected yet.",
  "intent": "mock_intent",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "Day 2 mock mode: retrieval is not connected yet.",
  "trace_id": "trace_f3b64c12449d4c20a3c43fe9cdabddfe"
}
```

### 手动验证非法 query

```powershell
curl.exe -s -o NUL -w '%{http_code}' -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"   "}'
```

返回：

```text
422
```

说明空 query 被正确拒绝。

## 5. 遇到了什么问题

### 问题：PowerShell 里的 curl JSON 引号转义

第一次手动请求 `/chat` 时，我用了比较脆弱的转义方式，导致 FastAPI 收到的 JSON 是坏的。

错误返回：

```json
{
  "detail": [
    {
      "type": "json_invalid",
      "loc": ["body", 1],
      "msg": "JSON decode error"
    }
  ]
}
```

这不是代码 bug，而是命令行里的 JSON 引号写法有问题。

解决方式：

在 PowerShell 里使用单引号包住 JSON：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

这个问题也记录到了：

```text
.learnings/ERRORS.md
```

## 6. 今天的设计取舍

### 先固定接口，再实现能力

Day 2 的重点是 API 契约。即使现在还没有 RAG，响应里也先保留：

- `answer`
- `intent`
- `evidence`
- `fallback`
- `fallback_reason`
- `trace_id`

这样后续接检索、评估、fallback、tracing 时不用推翻接口。

### mock 不假装真实

Day 2 的 `/chat` 返回：

```json
"fallback": true
```

原因是现在没有 evidence。如果 mock 阶段假装 `fallback=false`，会让人误以为系统已经完成了正常 RAG 回答。

### schema 与 route 分离

请求/响应结构放在 `app/schemas/`，路由放在 `app/api/routes.py`。

这样后续 pipeline 可以复用 `ChatRequest`、`ChatResponse`，不会让 API 层和数据结构混在一起。

## 7. 当前状态

当前项目已经具备：

- `GET /health`
- `POST /chat`
- `ChatRequest`
- `ChatResponse`
- `Evidence`
- `TraceInfo`
- `/chat` mock response
- 输入校验
- API 契约文档
- `/chat` 契约测试

当前项目还不具备：

- policy 文档数据
- document loader
- chunking
- retrieval
- evidence-grounded answer
- RAG pipeline

这些会从 Day 3 开始继续补。

## 8. 今日三句面试表达

- 我没有让 `/chat` 只返回纯文本，而是从第一版开始返回结构化响应。
- `evidence`、`fallback` 和 `trace_id` 是后续做质量评估、错误分析和性能追踪的基础字段。
- 先定 API 契约可以减少后续反复改接口造成的技术债。
