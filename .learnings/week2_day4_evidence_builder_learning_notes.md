# Week2 Day 4 学习笔记：Evidence Builder 与 Citation 约束

## 1. 今天完成了什么

Week2 Day4 的目标是：统一 structured evidence 和 document evidence，让 `/chat` 返回的证据更可追溯，并让 prompt/answer 更明确地遵守 evidence-first。

今天完成了：

- 完善 `Evidence` schema
- 新增 `app/pipeline/evidence_builder.py`
- structured tool result 转成 structured evidence
- retrieved document evidence 转成 document evidence
- `/chat` 的 structured/document/hybrid 三条路径都接入 evidence builder
- prompt builder 注入 evidence_id、evidence_type、source、metadata、content
- answer generator 继续保持“无证据不回答”
- structured evidence 的 `content` 改成可解析 dict
- 新增 `tests/test_evidence_builder.py`
- 更新 API 文档、README、failure cases
- 记录一次随机 evidence_id 破坏 determinism 的错误
- 新增本学习笔记

## 2. 为什么需要 Evidence Builder

Day2 后，系统有两类证据来源：

```text
structured tools -> 订单/退款/商品数据
document retriever -> 退货/物流/保修文档
```

如果它们各自用不同格式返回，后面会很难做：

- citation correctness
- fallback 判断
- evaluation
- trace/debug
- hybrid answer

所以 Day4 新增 evidence builder，让它统一输出：

```text
list[Evidence]
```

不管来源是工具还是文档，最后都进入同一种 evidence list。

## 3. Evidence schema 发生了什么变化

以前 Evidence 只有：

```python
source: str
content: str
score: float
metadata: dict
```

Day4 后变成：

```python
evidence_id: str
evidence_type: "structured" | "document"
source: str
content: str | dict
score: float | None
metadata: dict
```

### `evidence_id`

用于标识一条证据。

Day4 里 document evidence 的 ID 会根据：

```text
evidence_type + source + content
```

稳定生成。

为什么要稳定？

因为如果每次检索同一段内容都生成随机 ID，测试和评估会很难比较结果。

今天就遇到了这个问题：随机 `evidence_id` 破坏了 `test_keyword_fallback_is_deterministic`。

### `evidence_type`

用于区分证据类型：

```text
structured
document
```

比如订单状态：

```json
{
  "evidence_type": "structured",
  "source": "structured:orders:ORD-1001"
}
```

退货政策：

```json
{
  "evidence_type": "document",
  "source": "return_policy.md"
}
```

### `content`

`content` 现在可以是：

```text
str
dict
```

文档证据仍然是字符串。

结构化证据是 dict，例如：

```json
{
  "order_id": "ORD-1001",
  "status": "delivered",
  "status_label": "已签收",
  "product_id": "P-HEADPHONE-01"
}
```

这比把结构化数据塞成 JSON 字符串更好，因为后续 evaluation 可以直接读取字段。

## 4. 新增的 `evidence_builder.py`

核心函数是：

```python
build_evidence(tool_results=None, retrieved_evidence=None) -> list[Evidence]
```

它做两件事：

### 1. ToolResult -> structured Evidence

输入：

```text
get_order_status("ORD-1001") -> ToolResult
```

输出：

```json
{
  "evidence_type": "structured",
  "source": "structured:orders:ORD-1001",
  "content": {
    "order_id": "ORD-1001",
    "status": "delivered"
  },
  "metadata": {
    "tool_name": "get_order_status",
    "evidence_origin": "structured_tool"
  }
}
```

如果 tool result 是失败的，比如 `missing_order_id`，builder 不会生成 evidence。

### 2. Retrieved Evidence -> document Evidence

输入：

```text
retriever 返回的 Evidence
```

输出：

```json
{
  "evidence_type": "document",
  "source": "return_policy.md",
  "content": "退货需要保持商品和包装完整。",
  "metadata": {
    "document_type": "return_policy"
  }
}
```

## 5. `/chat` 三条路径怎么接入 builder

### structured_only

例如：

```text
订单 EC1001 是否已经发货？
```

流程：

```text
intent_router -> order_status
get_order_status -> ToolResult
build_evidence(tool_results=[result])
ChatResponse.evidence
```

返回 evidence：

```text
evidence_type=structured
source=structured:orders:ORD-1001
content=dict
```

### document_only

例如：

```text
这个商品可以七天无理由退货吗？
```

流程：

```text
retriever -> document evidence
build_evidence(retrieved_evidence=evidence)
prompt_builder
answer_generator
ChatResponse.evidence
```

返回 evidence：

```text
evidence_type=document
source=return_policy.md
content=str
```

### hybrid

例如：

```text
订单 ORD-1001 的耳机现在还能退货吗？
```

流程：

```text
get_order_status -> structured evidence
retriever -> document evidence
build_evidence(tool_results=[order_result], retrieved_evidence=document_response.evidence)
ChatResponse.evidence
```

返回 evidence list 同时包含：

```text
structured:orders:ORD-1001
return_policy.md
```

## 6. Prompt 和 Answer 做了什么增强

### `prompt_builder.py`

prompt 现在明确写了：

```text
Answer only from the Evidence items below.
Do not introduce order, refund, product, policy, or timeline facts that are absent from Evidence.
If Evidence is empty or insufficient, say that the system cannot answer from current evidence.
```

并且每条 evidence 会包含：

```text
id
type
source
score
metadata
content
```

这为以后接真实 LLM 做准备。

### `answer_generator.py`

当前还是 mock/rule-based answer generator。

它做了两件增强：

- 如果没有 evidence，仍然拒答。
- structured content 是 dict 时，直接把 dict 作为证据内容组织出来。

它还过滤了一些文档里的“政策元数据”行，减少 Day3 里出现的回答噪音。

## 7. 新增了哪些测试

新增：

```text
tests/test_evidence_builder.py
```

覆盖：

- tool result 能转 structured evidence
- failed tool result 不生成 evidence
- document evidence 保留 metadata
- hybrid evidence 同时包含 structured 和 document
- evidence_id 稳定生成

同时更新了：

- `tests/test_week2_chat_routes.py`
- `tests/test_rag_pipeline.py`

确保 `/chat` 返回的 evidence 有正确的 `evidence_type`。

## 8. 今天遇到的问题

### 随机 evidence_id 破坏 deterministic test

一开始 `Evidence.evidence_id` 使用随机 UUID 默认值。

这导致同一个 retriever 连续查询两次：

```python
first = retriever.retrieve("物流异常", top_k=2)
second = retriever.retrieve("物流异常", top_k=2)
assert first == second
```

失败。

原因是：

```text
source/content/score/metadata 都一样
但 evidence_id 不一样
```

修复方式：

在 retriever 创建 document evidence 时，显式传入稳定 ID：

```python
evidence_id=build_evidence_id("document", source, content)
```

这个错误已经记录到：

```text
.learnings/ERRORS.md
```

## 9. 今天的验收结果

### Evidence builder 测试

命令：

```powershell
python -m pytest tests\test_evidence_builder.py -q
```

结果：

```text
5 passed
```

### 相关路由/RAG/工具测试

命令：

```powershell
python -m pytest tests\test_week2_chat_routes.py tests\test_rag_pipeline.py tests\test_ecommerce_tools.py -q
```

结果：

```text
16 passed
```

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
60 passed
```

### 手动 structured 请求

请求：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day4","query":"订单 EC1001 是否已经发货？"}'
```

观察到：

```text
intent=order_status
route=structured_only
evidence[0].evidence_type=structured
evidence[0].content.order_id=ORD-1001
```

### 手动 document 请求

请求：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day4","query":"这个商品可以七天无理由退货吗？"}'
```

观察到：

```text
intent=return_policy
route=document_only
evidence[0].evidence_type=document
evidence[0].source=return_policy.md
```

### 手动 hybrid 请求

请求：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day4","query":"订单 ORD-1001 的耳机现在还能退货吗？"}'
```

观察到：

```text
route=hybrid
evidence 同时包含 structured 和 document
```

## 10. 当前仍然存在的限制

### mock answer 还不是完整推理器

现在 answer generator 只是整理 evidence，不会真正判断“这个订单是否一定可以退”。

它能展示订单事实和政策证据，但还不能做完整业务 eligibility decision。

### structured/document 冲突还没处理

如果结构化数据和文档政策出现冲突，目前系统只是把两类 evidence 返回出来，还没有冲突解决策略。

这个应该进入 Day5 fallback handler 或后续 evaluation。

## 11. 复习重点

你复习 Day4 时，重点理解：

- Evidence builder 是证据统一层，不负责查数据。
- Structured evidence 的 content 应该是可解析 dict。
- Document evidence 的 content 仍然可以是文本。
- evidence_id 应该稳定，不能影响 deterministic tests。
- prompt 必须明确告诉模型只能基于 evidence 回答。
- 没有 evidence 时不能强答。

## 12. 今日三句面试表达

- 我没有让模型直接输出最终答案，而是先构建 evidence，再让回答生成模块基于证据回答。
- Evidence builder 统一了数据库查询结果和文档检索结果，为 citation correctness 和 failure analysis 打基础。
- 回答带 evidence 可以降低幻觉，也方便后续做自动评估和人工审查。
