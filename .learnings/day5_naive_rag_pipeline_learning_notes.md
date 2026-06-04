# Day 5 学习笔记：Retrieve -> Prompt -> Answer 最小闭环

## 1. 今天完成了什么

Day 5 的目标是把 `/chat` 从 Day 2 的 mock response 接到 naive RAG pipeline。

前几天已经完成了：

- Day 1：FastAPI 工程骨架和 `/health`
- Day 2：`/chat` API 契约
- Day 3：policy 文档和 document loader
- Day 4：chunking、keyword fallback index、retriever

今天把这些能力串起来：

```text
query -> retrieve -> build_prompt -> generate_answer -> ChatResponse
```

最终效果：

- 用户问退货政策，系统能返回 evidence-backed answer
- 用户问无关问题，系统 fallback，不硬编
- `/chat` 返回结构仍然保持 Day 2 的契约字段

## 2. 新增和修改了哪些文件

### `app/pipeline/prompt_builder.py`

这个文件负责构造 prompt。

核心函数：

```python
def build_prompt(query: str, evidence: list[Evidence]) -> str:
```

它把两部分放进 prompt：

- 用户问题
- 检索到的 evidence

核心思想：

```text
Answer only from the provided evidence.
```

也就是说，prompt 明确要求回答只能基于证据。

如果 evidence 为空，就会写：

```text
(no evidence)
```

注意：`prompt_builder` 不调用 retriever，也不加载数据。

它只做一件事：把 query 和 evidence 组织成 prompt 文本。

### `app/pipeline/answer_generator.py`

这个文件负责生成回答。

核心函数：

```python
def generate_answer(prompt: str, evidence: list[Evidence]) -> str:
```

当前 Week 1 不是接真实 LLM，而是一个 rule-based answer generator。

如果没有 evidence：

```python
return "I cannot answer from the current evidence."
```

如果有 evidence，它会把前两条 evidence 组织成答案：

```python
return f"根据当前检索到的证据（{sources}）：{evidence_summary}"
```

为什么这样保守？

因为 Day 5 的原则是：answer 只能来自 evidence。

它不会自己发明“耳机一定可以退货”这样的结论，而是把检索到的政策文本组织出来。

### `app/pipeline/rag_pipeline.py`

这个文件是 Day 5 的核心，把多个步骤串成一个 pipeline。

核心类：

```python
class RagPipeline:
```

主要方法：

```python
def run_chat(self, query: str, user_id: str, session_id: str, top_k: int = 3) -> ChatResponse:
```

执行流程：

1. 生成 `trace_id`
2. 调用 retriever 检索 evidence
3. 用最低分数阈值过滤 evidence
4. 如果 evidence 为空，返回 fallback response
5. 如果 evidence 存在，构造 prompt
6. 基于 evidence 生成 answer
7. 返回 `ChatResponse`

fallback 代码：

```python
if not evidence:
    return ChatResponse(
        answer="我没有在当前知识库中找到足够可靠的证据来回答这个问题。",
        intent="unknown",
        evidence=[],
        fallback=True,
        fallback_reason="No retrieval evidence met the minimum score threshold.",
        trace_id=trace_id,
    )
```

这段非常重要。

它体现了 RAG 的基本底线：没有证据，就不要硬答。

成功路径：

```python
prompt = build_prompt(query=query, evidence=evidence)
answer = generate_answer(prompt=prompt, evidence=evidence)
```

然后返回：

```python
ChatResponse(
    answer=answer,
    intent="policy_question",
    evidence=evidence,
    fallback=False,
    fallback_reason=None,
    trace_id=trace_id,
)
```

### `app/api/routes.py`

Day 2 的 `/chat` 是 mock response。

Day 5 把它改成调用 pipeline：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    pipeline = get_chat_pipeline()
    return pipeline.run_chat(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
    )
```

这里 `get_chat_pipeline()` 使用了缓存：

```python
@lru_cache
def get_chat_pipeline() -> RagPipeline:
    documents = load_ecommerce_documents()
    return RagPipeline.from_documents(documents, chunk_size=220, overlap=20)
```

为什么要缓存？

因为如果每次请求都重新加载文档、切 chunk、建 index，就会浪费时间。

Week 1 数据很小，即使不缓存也能跑，但从工程习惯上讲，缓存默认 pipeline 更合理。

边界说明：

- API route 负责接收请求和调用 pipeline
- `RagPipeline` 负责 RAG 流程
- ecommerce adapter 负责加载电商文档
- retriever 负责检索 evidence
- answer generator 负责基于 evidence 组织回答

### `tests/test_rag_pipeline.py`

这个文件测试 Day 5 的闭环。

#### 测试 1：退货问题返回 evidence-grounded answer

```python
def test_rag_pipeline_returns_evidence_grounded_policy_answer() -> None:
```

它验证：

- `fallback` 是 false
- `intent` 是 `policy_question`
- evidence 不为空
- 第一条 evidence 来自 `return_policy.md`
- answer 中包含 `退货`
- trace_id 以 `trace_` 开头

#### 测试 2：无关问题 fallback

```python
def test_rag_pipeline_fallbacks_when_no_evidence_matches() -> None:
```

query：

```text
量子咖啡会员积分怎么兑换？
```

这个问题和电商售后 policy 文档无关，所以应该 fallback。

#### 测试 3：prompt 包含 query 和 evidence

```python
def test_prompt_builder_includes_query_and_evidence() -> None:
```

这个测试保证 prompt builder 没有漏掉用户问题或证据。

#### 测试 4：没有 evidence 不回答

```python
def test_answer_generator_does_not_answer_without_evidence() -> None:
```

这验证了 answer generator 的底线。

#### 测试 5：真实 `/chat` endpoint 使用 RAG pipeline

```python
def test_chat_endpoint_uses_rag_pipeline() -> None:
```

这不是只测 pipeline 内部函数，而是用 FastAPI TestClient 打 `/chat`。

它验证 `/chat` 已经不是 Day 2 mock。

### `tests/test_chat_contract.py`

这个文件也做了必要更新。

Day 2 时它断言：

- `intent == "mock_intent"`
- `evidence == []`
- `fallback is True`

Day 5 后这些断言已经过时，因为 `/chat` 现在接入了 RAG pipeline。

所以它被改成只验证稳定契约：

- 字段完整
- `answer` 存在
- `intent` 是 string
- `evidence` 是 list
- `fallback` 是 bool
- `trace_id` 以 `trace_` 开头

这就是“契约测试”和“具体行为测试”的区别：

- 契约测试：字段形状不能破
- 行为测试：某个 query 应该检索到某类 evidence

### `docs/failure_cases.md`

这个文件记录 RAG v0 的已知局限。

记录了 3 类问题：

1. keyword mismatch
2. weak semantic understanding
3. template-like answers

为什么要写 failure cases？

因为 Week 1 的目标不是粉饰 demo，而是让项目可解释、可 review、可继续迭代。

一个真实的 RAG 项目必须知道自己哪里会失败。

### `docs/contracts/query_api.md`

这个文件从 Day 2 mock 文档更新为 Day 5 naive RAG v0 文档。

主要变化：

- response example 从 mock 改成 evidence-backed response
- `intent` 从 `mock_intent` 改成 Week 1 简单标签
- `evidence` 不再固定为空
- 当前边界改为 naive RAG v0

## 3. 今天没有做什么

Day 5 没有做：

- 没有接真实 LLM
- 没有接真实 embedding API
- 没有做 SQL tool
- 没有做订单个性化判断
- 没有做 rerank
- 没有做复杂 intent router
- 没有做 production tracing

当前仍然是 naive RAG v0。

## 4. 怎么验收的

### Day 5 专项测试

```powershell
python -m pytest tests/test_rag_pipeline.py -q
```

结果：

```text
5 passed
```

### `/chat` 契约测试

```powershell
python -m pytest tests/test_chat_contract.py -q
```

结果：

```text
4 passed
```

### 全量测试

```powershell
python -m pytest -q
```

结果：

```text
21 passed
```

### 手动 HTTP 验收：成功 query

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"耳机可以退货吗？"}'
```

结果包含：

```json
{
  "intent": "policy_question",
  "fallback": false,
  "evidence": [
    {
      "source": "return_policy.md"
    }
  ],
  "trace_id": "trace_..."
}
```

### 手动 HTTP 验收：fallback query

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"量子咖啡会员积分怎么兑换？"}'
```

结果包含：

```json
{
  "intent": "unknown",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "No retrieval evidence met the minimum score threshold."
}
```

## 5. 遇到了什么问题

今天没有遇到阻塞性代码问题。

有一个设计层面的注意点：

Day 5 改了 `/chat` 的行为，所以 Day 2 的旧测试不能继续要求 mock response。否则测试会变成阻碍真实功能演进的“过期断言”。

解决方式：

- `tests/test_chat_contract.py` 保留字段契约检查
- `tests/test_rag_pipeline.py` 检查 Day 5 的具体 RAG 行为

这样测试职责更清楚。

## 6. 今天的设计取舍

### answer generator 很保守

当前 answer 只是组织 evidence。

它不是成熟客服回复，也不会判断具体订单是否一定能退。

这是为了避免没有结构化订单信息时过度承诺。

### fallback 优先于硬编

如果 evidence 为空或低于阈值，就 fallback。

这比“看起来什么都能回答”更像一个可控的工程系统。

### pipeline 保持通用

`RagPipeline` 接收 documents/retriever，不写死退货、物流、保修规则。

电商 demo 的文档加载在 API wiring 层完成。

## 7. 当前状态

当前项目已经具备：

- `/health`
- `/chat`
- Chat API contract
- ecommerce policy docs
- document loader
- chunker
- keyword fallback retriever
- prompt builder
- rule-based answer generator
- naive RAG pipeline
- evidence list
- fallback
- trace_id

当前项目还不具备：

- SQL + RAG 混合问答
- 订单/商品精确事实查询
- 真实 embedding
- 真实 LLM
- rerank
- evaluation cases
- performance tracing

## 8. 今日三句面试表达

- 我跑通了 naive RAG v0：用户问题、文档检索、prompt 构造、回答生成和 evidence 返回。
- 回答带 evidence 是为了后续评估 citation correctness 和 answer faithfulness。
- 当检索不到证据时，系统会 fallback，而不是让模型凭空编造。
