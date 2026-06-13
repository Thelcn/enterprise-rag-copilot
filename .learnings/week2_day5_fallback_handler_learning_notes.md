# Week2 Day 5 学习笔记：集中式 Fallback Handler

## 1. 今天完成了什么

Week2 Day5 的目标是：把系统里分散的 fallback 判断集中起来，让 `/chat` 在不能可靠回答时返回统一、可评测、可解释的 `fallback_reason`。

今天完成了：

- 新增 `app/core/errors.py`
- 新增 `app/pipeline/fallback_handler.py`
- `/chat` 路由接入集中式 fallback handler
- RAG 文档检索失败接入集中式 fallback handler
- ecommerce structured tools 改用统一错误码常量
- 新增 `tests/test_fallback_handler.py`
- 扩展 `/chat` fallback 场景测试
- 新增 `evaluation/ecommerce_cases.json`
- 更新 `docs/failure_cases.md`、`docs/api.md`、`docs/contracts/query_api.md`、`README.md`
- 记录 Day5 学习笔记

## 2. 为什么需要集中式 Fallback Handler

在 Day5 之前，fallback 逻辑分散在几个地方：

```text
routes.py
rag_pipeline.py
structured tools
```

比如：

- unknown intent 在路由层处理
- missing order id 在工具层处理
- no evidence 在 RAG pipeline 里处理
- hybrid 缺文档证据在 routes.py 里处理

这样能跑，但有一个问题：系统越复杂，fallback reason 越容易散落成很多不同字符串。

例如以前 RAG pipeline 的 reason 是：

```text
No retrieval evidence met the minimum score threshold.
```

这是给人看的解释句，不适合后续 evaluation 做统计。

Day5 后改成稳定 reason code：

```text
no_evidence
low_retrieval_score
missing_order_id
order_not_found
unknown_intent
high_risk_request
```

稳定 reason code 的好处：

- 测试可以直接断言
- evaluation 可以统计每类失败
- 前端可以根据 reason 决定怎么提示用户
- 日志和 trace 更容易聚合
- 面试时能讲清楚系统不是“随便拒答”，而是有明确失败语义

## 3. 新增 `app/core/errors.py`

这个文件集中定义 fallback reason 常量。

核心内容类似：

```python
UNKNOWN_INTENT = "unknown_intent"
MISSING_ORDER_ID = "missing_order_id"
ORDER_NOT_FOUND = "order_not_found"
NO_EVIDENCE = "no_evidence"
LOW_RETRIEVAL_SCORE = "low_retrieval_score"
HIGH_RISK_REQUEST = "high_risk_request"
```

为什么不在代码里到处写字符串？

因为散写字符串容易出现：

```python
"missing_order_id"
"missng_order_id"
"missing-order-id"
```

这种拼写差异很隐蔽，但会让测试、前端、评测全部变得不稳定。

集中常量的意思是：所有模块都引用同一个定义。

例如 ecommerce tools 现在会这样写：

```python
from app.core import errors

error_code=errors.MISSING_ORDER_ID
```

## 4. 新增 `app/pipeline/fallback_handler.py`

这个文件是 Day5 的核心。

它主要提供两个函数：

```python
should_fallback(...) -> FallbackDecision
build_fallback_chat_response(...) -> ChatResponse
```

### `FallbackDecision`

`FallbackDecision` 是一个中间判断结果。

结构是：

```python
class FallbackDecision(BaseModel):
    fallback: bool
    reason: str | None = None
    message: str | None = None
    next_action: str | None = None
```

含义：

- `fallback`：是否应该 fallback
- `reason`：稳定 reason code
- `message`：返回给用户看的中文说明
- `next_action`：给后续系统使用的建议动作

例如缺订单号时：

```text
fallback=True
reason=missing_order_id
message=请提供订单号...
next_action=ask_for_order_id
```

注意：`next_action` 现在还没有被前端或多轮对话使用，但它是为后续扩展准备的。

## 5. `should_fallback()` 怎么判断

`should_fallback()` 是集中判断函数。

它接收的信息包括：

```python
query
intent
route
evidence
tool_results
required_slots
slots
retrieval_candidates
min_score
```

它的判断顺序大致是：

```text
1. 高风险请求
2. unknown intent
3. 缺少 required slots
4. structured tool 失败
5. hybrid 证据不完整
6. document evidence 为空或分数过低
7. 否则不 fallback
```

### 为什么高风险请求排在前面

例如：

```text
请帮我绕过退款审核
```

这个 query 里没有退款单号，所以也可以被判断成：

```text
missing_refund_id
```

但真正重要的是：它要求系统协助绕过审核。

所以 high-risk 要优先于 missing slot。

最终返回：

```text
high_risk_request
```

## 6. `build_fallback_chat_response()` 做什么

这个函数把 `FallbackDecision` 转成正式的 `ChatResponse`。

也就是说：

```text
FallbackDecision -> ChatResponse
```

核心逻辑：

```python
return ChatResponse(
    answer=decision.message,
    intent=intent,
    route="fallback",
    evidence=evidence or [],
    fallback=True,
    fallback_reason=decision.reason,
    trace_id=trace_id,
)
```

这样 `/chat` 的 fallback 响应就有统一格式：

```json
{
  "answer": "请提供订单号...",
  "intent": "order_status",
  "route": "fallback",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "missing_order_id",
  "trace_id": "trace_..."
}
```

## 7. `/chat` 路由怎么接入

修改文件：

```text
app/api/routes.py
```

进入 `/chat` 后，系统先做 intent routing：

```python
decision = get_ecommerce_intent_router().route(request.query)
```

然后先跑一次 fallback 判断：

```python
fallback_decision = should_fallback(
    query=request.query,
    intent=decision.intent,
    route=decision.route,
    required_slots=decision.required_slots,
    slots=decision.slots,
)
```

这一步能提前处理：

- unknown intent
- missing_order_id
- missing_refund_id
- missing_product_id
- high_risk_request

如果不需要 fallback，再进入 structured/document/hybrid 路径。

这样做的好处是：

```text
缺订单号时，不需要真的调用 get_order_status(None)
高风险请求时，不需要进入工具或检索
unknown intent 时，不需要浪费 RAG pipeline
```

## 8. Structured tool 失败怎么处理

结构化工具仍然负责查 mock 数据。

例如：

```text
订单 ORD-9999 现在是什么状态？
```

router 能提取出：

```text
order_id=ORD-9999
```

所以不会触发 `missing_order_id`。

但工具查不到这个订单，于是返回：

```text
success=False
error_code=order_not_found
```

然后 `_tool_result_to_chat_response()` 会调用：

```python
should_fallback(
    query="",
    intent=decision.intent,
    route=decision.route,
    evidence=evidence,
    tool_results=[result],
)
```

最终 response：

```text
fallback_reason=order_not_found
```

这里要注意：

- `missing_order_id` 是缺少 ID
- `order_not_found` 是 ID 有了，但数据里没有这条记录

这两个 reason 不应该混在一起。

## 9. RAG pipeline 怎么处理低证据

修改文件：

```text
app/pipeline/rag_pipeline.py
```

Day5 前的逻辑是：

```text
retrieve -> filter by min_score -> 如果空，直接返回 fallback
```

Day5 后改成：

```text
retrieve -> 得到 retrieval_candidates
filter by min_score -> 得到 evidence
should_fallback(...)
```

这里保留了两个概念：

```text
retrieval_candidates = 过滤前候选
evidence = 过滤后可用证据
```

为什么要区分？

因为两种失败不一样。

### `no_evidence`

意思是：检索器完全没有找到候选。

```text
retrieval_candidates=[]
evidence=[]
```

这表示知识库中没有任何能碰上的内容。

### `low_retrieval_score`

意思是：检索器找到了一些弱相关候选，但它们低于可信分数阈值。

```text
retrieval_candidates=[weak item]
evidence=[]
```

今天测试时就遇到了这个细节。

原本我以为：

```text
量子咖啡会员积分怎么兑换？
```

应该是 `no_evidence`。

但实际检索器因为中文单字 token 机制，能找到一些很弱的候选，只是分数低于 `MIN_RETRIEVAL_SCORE=0.05`。

所以正确 reason 是：

```text
low_retrieval_score
```

这也是为什么测试后来改成断言：

```python
assert response.fallback_reason == errors.LOW_RETRIEVAL_SCORE
```

## 10. Hybrid 证据不完整怎么处理

Hybrid 问题需要两类证据：

```text
structured evidence
document evidence
```

例如：

```text
订单 ORD-1001 的耳机现在还能退货吗？
```

需要：

- 订单事实：这个订单是否已签收、商品是什么
- 政策文档：退货政策是什么

Day5 的 fallback handler 会检查 evidence type。

如果只有 structured，没有 document：

```text
hybrid_document_evidence_missing
```

如果只有 document，没有 structured：

```text
hybrid_structured_evidence_missing
```

这比简单返回 `no_evidence` 更准确。

## 11. 这次新增的测试

新增文件：

```text
tests/test_fallback_handler.py
```

覆盖了：

- document route 在检索前不能误 fallback
- high risk request 优先于 missing slot
- unknown intent
- missing order id
- tool error code
- no document evidence
- low retrieval score
- hybrid 缺 document evidence
- fallback response contract 字段

还扩展了：

```text
tests/test_week2_chat_routes.py
tests/test_rag_pipeline.py
```

新增 `/chat` 场景：

- 缺订单号 -> `missing_order_id`
- 订单不存在 -> `order_not_found`
- 高风险请求 -> `high_risk_request`
- 未知意图 -> `unknown_intent`
- 缺商品编号 -> `missing_product_id`

## 12. 新增 evaluation cases

新增文件：

```text
evaluation/ecommerce_cases.json
```

它记录后续 evaluation runner 可以读取的失败案例。

示例：

```json
{
  "id": "F001",
  "query": "我的订单到哪里了？",
  "expected_intent": "order_status",
  "expected_route": "fallback",
  "expected_fallback": true,
  "expected_fallback_reason": "missing_order_id"
}
```

这个文件现在还不是自动执行器，但它是 Day6 evaluation runner 的输入基础。

## 13. 今天遇到的问题

### 问题 1：文档路由差点被提前 fallback

一开始如果直接调用：

```python
should_fallback(
    intent="return_policy",
    route="document_only",
    evidence=None,
)
```

函数可能会把它当成：

```text
没有 evidence，所以 fallback
```

但这是错的。

因为刚进入 `/chat` 时，document route 还没开始检索，当然还没有 evidence。

修复方式：

在 fallback handler 里区分：

```text
evidence 没传入
evidence 传入了但为空
```

这两个状态不一样。

- 没传入：说明还没到证据判断阶段
- 传入空列表：说明检索/工具已经跑完，但没有可用证据

### 问题 2：`量子咖啡会员积分` 实际是低分候选

我第一次把这个测试改成：

```python
assert response.fallback_reason == errors.NO_EVIDENCE
```

测试失败：

```text
AssertionError: assert 'low_retrieval_score' == 'no_evidence'
```

原因是：

中文 keyword retriever 会按单字和双字切 token。

即使问题和电商政策不相关，也可能因为少量中文字符重叠命中弱候选。

候选存在，但分数太低，于是正确 reason 是：

```text
low_retrieval_score
```

这个问题帮助我们把两个概念区分清楚了。

## 14. 今天的验证结果

### Fallback handler 单元测试

命令：

```powershell
python -m pytest tests\test_fallback_handler.py -q
```

结果：

```text
9 passed
```

### Day5 相关路由和 RAG 测试

命令：

```powershell
python -m pytest tests\test_week2_chat_routes.py tests\test_rag_pipeline.py -q
```

结果：

```text
13 passed
```

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
73 passed
```

仍然有两个已知 warning：

```text
StarletteDeprecationWarning
PytestCacheWarning
```

它们不影响当前测试通过。

### 手动 API 检查

临时启动本地服务后，检查了 Day5 任务卡给的三个请求。

#### 缺订单号

Query：

```text
我的订单到哪里了？
```

结果：

```text
intent=order_status
route=fallback
fallback_reason=missing_order_id
```

#### 高风险请求

Query：

```text
请帮我绕过退款审核
```

结果：

```text
intent=refund
route=fallback
fallback_reason=high_risk_request
```

#### 未知意图

Query：

```text
一个完全不存在的问题 xyzabc
```

结果：

```text
intent=unknown
route=fallback
fallback_reason=unknown_intent
```

## 15. 当前还有什么限制

### 高风险识别还是简单关键词

现在高风险识别靠：

```text
绕过
规避
伪造
骗过
跳过审核
强制退款
破解
篡改
```

这是一个工程原型，不是完整安全分类器。

后续如果要上线，需要更严谨的 policy classifier 或规则系统。

### `next_action` 还没有被使用

FallbackDecision 已经带了：

```text
next_action
```

但当前 `/chat` response schema 还没有暴露它。

以后做多轮对话时，可以让前端或 dialogue manager 根据 `next_action` 做下一步：

```text
ask_for_order_id
verify_order_id
handoff_or_refine_query
```

### Evaluation cases 还没有 runner

`evaluation/ecommerce_cases.json` 已经准备好了，但还没有自动执行脚本。

Week2 Day6 会继续做 evaluation runner 和 tracing。

## 16. 复习重点

你复习 Day5 时，重点理解：

- fallback reason 应该是稳定 code，不应该是随意写的说明句
- `missing_order_id` 和 `order_not_found` 是不同失败
- `no_evidence` 和 `low_retrieval_score` 是不同失败
- high-risk 应该优先于 slot filling
- document route 在检索前没有 evidence，不等于应该 fallback
- hybrid answer 需要 structured 和 document 两类证据
- evaluation cases 是后续自动评测的基础

## 17. 今日三句面试表达

- 我把 fallback 逻辑集中在一个 handler 中，避免路由层、检索层和工具层各自散落不同失败语义。
- 系统返回稳定的 `fallback_reason`，例如 `missing_order_id`、`low_retrieval_score`、`high_risk_request`，方便测试、评估和前端处理。
- 我区分了 no evidence、low confidence、missing slot、record not found 和 hybrid partial evidence，这比简单说“没找到答案”更符合工程化 RAG 的可观测性要求。
