# Week2 Day 6 学习笔记：Evaluation Runner 与 Performance Tracer

## 1. 今天完成了什么

Week2 Day6 的目标是建立基础评估闭环和性能追踪。

今天完成了：

- Day5 commit 并 push 到 GitHub
- 扩展 `/chat` 响应，新增 `trace`
- 扩展 `app/schemas/trace.py`
- 新增 `app/pipeline/performance_tracer.py`
- `/chat` 路由和 RAG pipeline 接入 tracer
- 新增 `app/schemas/evaluation.py`
- 扩展 `evaluation/ecommerce_cases.json` 到 35 条 cases
- 新增 `evaluation/metrics.py`
- 新增 `evaluation/run_eval.py`
- 新增 `docs/evaluation.md`
- 新增 `docs/performance.md`
- 更新 README、API docs、contract docs
- 新增 tracer 和 evaluation metrics 测试
- 记录 Day6 发现的两个 intent router 问题
- 新增本学习笔记

## 2. Day5 Git 已完成

Day5 已经提交并推送：

```text
6373c12 feat: centralize fallback handling
```

提交前测试：

```text
73 passed
```

推送后确认：

```text
6373c12 (HEAD -> main, origin/main, origin/HEAD)
```

这一步完成后，才开始 Day6。

## 3. 为什么 Day6 要做 evaluation

RAG 项目最容易陷入一个问题：

```text
手动问几个问题，看起来能回答，于是觉得系统还不错。
```

这不够工程化。

Day6 的 evaluation runner 做的是：

```text
固定一批 cases
逐条调用 /chat
收集真实 response
计算指标
输出 JSON/Markdown 报告
```

这样我们可以从“感觉还行”变成：

```text
这 35 条本地 mock ecommerce cases 里，哪些 intent 对了，哪些 route 对了，哪些 evidence 命中了，哪些 fallback 对了。
```

注意：这仍然不是生产指标。

它只是本地 mock 数据集上的工程评估闭环。

## 4. Evaluation cases 放在哪里

文件：

```text
evaluation/ecommerce_cases.json
```

Day5 时这个文件只有失败案例。

Day6 扩展到 35 条，覆盖：

- structured order/refund/product 查询
- document-only 退货、保修、物流问题
- hybrid 订单 + 政策问题
- fallback 失败问题

每条 case 结构类似：

```json
{
  "id": "H006",
  "query": "订单 EC1001 的退款状态和退货政策是什么？",
  "expected_intent": "hybrid",
  "expected_route": "hybrid",
  "required_evidence_keywords": ["structured:orders:ORD-1001", "return_policy.md"],
  "expected_fallback": false,
  "notes": "Hybrid route for the Day6 manual check."
}
```

### 为什么要有 `required_evidence_keywords`

RAG 不能只看 answer。

如果 answer 看起来对，但 evidence 没有返回对应来源，这个回答仍然不可追溯。

所以 evaluation case 可以要求：

```text
evidence 里必须出现 structured:orders:ORD-1001
evidence 里必须出现 return_policy.md
```

这不是完整 faithfulness，但它是一个很有用的 smoke check。

## 5. 新增 `app/schemas/evaluation.py`

这里定义了 evaluation 的数据结构：

```python
EvaluationCase
EvaluationResult
EvaluationMetrics
EvaluationReport
```

### `EvaluationCase`

表示输入和预期：

```text
id
query
expected_intent
expected_route
required_evidence_keywords
expected_fallback
expected_fallback_reason
notes
```

### `EvaluationResult`

表示每条 case 跑完后的实际结果：

```text
actual_intent
actual_route
actual_fallback
actual_fallback_reason
evidence_count
evidence_keyword_hit
trace_id
total_latency_ms
passed
error
```

### `EvaluationMetrics`

表示整体统计：

```text
intent_accuracy
route_accuracy
fallback_correctness
fallback_reason_accuracy
evidence_presence_rate
evidence_keyword_hit_rate
error_count
average_total_latency_ms
```

## 6. 新增 `evaluation/metrics.py`

这个文件负责把 response 变成 result，再把 results 变成 metrics。

核心函数：

```python
build_result(case, response_payload)
compute_metrics(results)
```

### `build_result`

它会比较：

```text
expected_intent vs actual intent
expected_route vs actual route
expected_fallback vs actual fallback
expected_fallback_reason vs actual fallback_reason
required_evidence_keywords 是否出现在 evidence 里
```

只要有一个关键检查失败：

```text
passed=false
```

### `compute_metrics`

它会计算整体指标，例如：

```text
intent_accuracy = intent 正确的 case 数 / 总 case 数
```

这些指标都是从脚本输出算出来的，不是手写的。

## 7. 新增 `evaluation/run_eval.py`

运行命令：

```powershell
python -m evaluation.run_eval --cases evaluation/ecommerce_cases.json --out evaluation/eval_report.json --markdown-out evaluation/eval_report.md
```

runner 做的事：

```text
读取 cases
用 FastAPI TestClient 调用本地 app
逐条 POST /chat
收集 response
调用 metrics.py
写出 JSON report
可选写出 Markdown summary
在终端打印 metrics
```

为什么用 TestClient？

因为它不需要你提前启动 uvicorn，也不需要网络请求。

这让 evaluation 可以在本地、CI、面试演示里更稳定地运行。

## 8. 今天的 eval 结果

命令：

```powershell
python -m evaluation.run_eval --cases evaluation\ecommerce_cases.json --out evaluation\eval_report.json --markdown-out evaluation\eval_report.md
```

最终结果：

```json
{
  "total_cases": 35,
  "passed_cases": 35,
  "intent_accuracy": 1.0,
  "route_accuracy": 1.0,
  "fallback_correctness": 1.0,
  "fallback_reason_accuracy": 1.0,
  "evidence_presence_rate": 1.0,
  "evidence_keyword_hit_rate": 1.0,
  "error_count": 0,
  "average_total_latency_ms": 0.4705
}
```

重要提醒：

这个结果只代表本地 mock ecommerce cases，不代表真实生产指标。

报告输出文件：

```text
evaluation/eval_report.json
evaluation/eval_report.md
```

这两个文件被 `.gitignore` 忽略，因为 latency 每次运行都会变化。

## 9. 为什么 Day6 要做 performance tracing

现在 `/chat` 不只是返回答案，还返回：

```json
{
  "trace_id": "trace_...",
  "trace": {
    "trace_id": "trace_...",
    "total_latency_ms": 4.5718,
    "stages": [
      {
        "name": "intent",
        "latency_ms": 0.5327,
        "metadata": {}
      }
    ]
  }
}
```

`trace_id` 是请求编号。

`trace` 是本地调试和评估用的耗时摘要。

以后如果某个 case 很慢，我们可以看：

```text
是 intent 慢？
是 tool 慢？
是 retrieval 慢？
是 LLM/mock answer 慢？
```

## 10. 新增 `performance_tracer.py`

核心类：

```python
PerformanceTracer
```

它有三个重要方法：

```python
with tracer.span("retrieval"):
    ...

tracer.record_stage(...)
tracer.finish()
```

### `span()`

这是 context manager。

用法：

```python
with tracer.span("tool", tool_name="get_order_status"):
    result = get_order_status(order_id)
```

进入 `with` 时开始计时。

离开 `with` 时自动记录：

```text
stage name
latency_ms
metadata
```

### `finish()`

请求结束时调用：

```python
trace = tracer.finish()
```

它会生成：

```text
TraceInfo
```

其中包含总耗时：

```text
total_latency_ms
```

## 11. `/chat` 现在记录哪些阶段

当前阶段包括：

```text
intent
tool
retrieval
rerank_mock
llm_mock
fallback
```

### 为什么有 `rerank_mock`

现在还没有真实 reranker。

但 Day6 先把 stage 留出来，后续接真实 reranker 时不需要改 trace contract。

### 为什么叫 `llm_mock`

现在 answer generator 还是 deterministic rule-based，不是真实 LLM。

所以不能叫 `llm`，否则容易误导。

用 `llm_mock` 更诚实。

## 12. 今天修改了哪些核心文件

### `app/schemas/trace.py`

从只有：

```python
trace_id
```

扩展成：

```python
TraceStage
TraceInfo(trace_id, total_latency_ms, stages)
```

### `app/schemas/chat.py`

`ChatResponse` 新增：

```python
trace: TraceInfo | None = None
```

### `app/api/routes.py`

接入：

```python
PerformanceTracer()
```

并在：

- intent routing
- structured tool
- fallback
- hybrid response

记录阶段耗时。

### `app/pipeline/rag_pipeline.py`

接入 tracer，并记录：

- retrieval
- rerank_mock
- llm_mock
- fallback

还修正了一个 Day5 后的 hybrid 边界：

```text
RagPipeline 内部只负责文档证据，不再把 route=hybrid 的文档检索误判成缺 structured evidence。
```

最终 hybrid 完整性仍然由 `routes.py` 聚合 structured + document evidence 后判断。

## 13. 今天遇到的问题 1：evaluation 暴露 router 优先级 bug

失败 case：

```text
D008
query=发货时间是什么？
```

预期：

```text
intent=logistics
route=document_only
fallback=false
```

实际：

```text
intent=order_status
route=fallback
fallback_reason=missing_order_id
```

原因：

`order_status` 规则里有宽泛关键词：

```text
发货
```

而 `logistics` 规则里有更具体关键词：

```text
发货时间
```

但 order_status 当时排在 logistics 前面，所以先匹配了 order_status。

修复：

把 logistics 规则放到 order_status 前面，并新增测试：

```python
test_router_prefers_logistics_policy_for_shipping_time_question
```

## 14. 今天遇到的问题 2：手动 hybrid query 被 refund 抢走

任务卡手动问题：

```text
订单 EC1001 的退款状态和退货政策是什么？
```

第一次结果：

```text
intent=refund
route=fallback
fallback_reason=missing_refund_id
```

原因：

hybrid rule 没有包含：

```text
退货政策
```

所以 refund rule 看到 `退款状态` 后先匹配。

修复：

在 hybrid rule keywords 里加入：

```text
退货政策
```

并新增：

```python
test_router_detects_hybrid_for_order_refund_and_return_policy_question
```

同时新增 evaluation case：

```text
H006
```

## 15. 手动 API 检查

命令检查了：

```text
订单 EC1001 的退款状态和退货政策是什么？
```

最终观察到：

```text
intent=hybrid
route=hybrid
fallback=false
trace.total_latency_ms 存在
trace.stages 包含 intent/tool/retrieval/rerank_mock/llm_mock
```

这说明 Day6 的 manual check 已通过。

## 16. 今天新增的测试

新增：

```text
tests/test_performance_tracer.py
tests/test_evaluation_metrics.py
```

更新：

```text
tests/test_chat_contract.py
tests/test_intent_router.py
```

测试覆盖：

- tracer 能记录 stage latency
- RAG pipeline 返回 trace
- evaluation metrics 能计算成功/失败
- `/chat` response contract 包含 trace
- 物流/混合 intent 优先级正确

## 17. 今天的最终验证结果

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
78 passed
```

### Evaluation runner

命令：

```powershell
python -m evaluation.run_eval --cases evaluation\ecommerce_cases.json --out evaluation\eval_report.json --markdown-out evaluation\eval_report.md
```

结果：

```text
35 cases
35 passed
error_count=0
```

仍然有两个已知 warning：

- `StarletteDeprecationWarning`
- `PytestCacheWarning`

不影响当前验收。

## 18. 当前限制

### Evaluation cases 仍然是小样本

35 条 cases 足够做 Week2 工程闭环，但不代表真实用户分布。

### Evidence keyword hit 不是完整 citation faithfulness

它只能检查 evidence 里是否出现了关键来源或字段。

它不能证明 answer 每一句都完全忠实于 evidence。

### Performance trace 是本地 debug trace

`average_total_latency_ms` 来自本地 TestClient 和 mock LLM。

它不能写成生产 P95/P99/QPS。

Day7 会继续补 load-test script 和 performance report。

## 19. 复习重点

你复习 Day6 时，重点理解：

- evaluation cases 应该集中在 `evaluation/`
- runner 应该输出可复现报告，而不是手写指标
- `intent_accuracy` 和 `route_accuracy` 是不同指标
- `fallback_correctness` 和 `fallback_reason_accuracy` 也是不同指标
- trace 要记录阶段耗时，而不是只返回一个 trace_id
- mock LLM 阶段要诚实标成 `llm_mock`
- 评估失败要反哺代码和测试

## 20. 今日三句面试表达

- 我用本地 evaluation runner 固定 35 条 ecommerce cases，覆盖结构化、文档、混合和失败问题，而不是只展示成功 demo。
- 我的评估指标包括 intent accuracy、route accuracy、fallback correctness、evidence keyword hit 和 trace latency，所有结果来自脚本输出。
- 我实现了轻量 performance tracer，能看到 intent、tool、retrieval、rerank/mock、LLM/mock 和 total latency，为后续真实 LLM、reranker、cache 和压测留接口。
