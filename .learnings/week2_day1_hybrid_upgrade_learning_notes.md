# Week2 Day 1 学习笔记：审阅 Week1 v0，设计 Hybrid RAG 升级路线

## 1. 今天完成了什么

Week2 Day 1 的目标不是马上重写 RAG 系统，而是先确认 Week1 naive RAG v0 仍然可用，然后把 Week2 要升级的方向写清楚。

今天完成了：

- 阅读 Week2 Day 1 任务卡
- 检查当前 Git 工作区状态
- 跑 Week1 现有全量测试
- 新增 `docs/week2_upgrade_plan.md`
- 新增 `docs/api.md`
- 新增 `tests/test_week1_baseline.py`
- 更新 `docs/failure_cases.md`
- 更新 `README.md`
- 手动验证 `/health` 和 `/chat`
- 新增本学习笔记

## 2. 为什么 Day1 不急着写 Hybrid RAG 代码

Week1 已经有一个可以运行的 naive RAG v0：

```text
/chat
-> 读取电商 markdown 文档
-> chunk
-> keyword retriever
-> prompt builder
-> answer generator
-> 返回 answer + evidence + fallback + trace_id
```

如果 Week2 一开始就直接大改，很容易出现两个问题：

- 新功能没完全做好，原来的 `/chat` 也被破坏了。
- 代码变复杂后，很难说清楚哪些模块负责通用 RAG，哪些模块负责电商业务规则。

所以 Day1 先做三件事：

- 固定 Week1 的 baseline tests。
- 写清楚 Week2 为什么要升级。
- 明确后面 Day2-Day7 每天要加什么模块。

这就是工程项目里常见的“先锁基线，再做演进”。

## 3. 开始前检查了什么

### Git 状态

一开始看到当前工作区有 4 个已修改代码文件：

```text
app/api/routes.py
app/core/config.py
app/schemas/chat.py
app/schemas/evidence.py
```

检查 diff 后发现，这些改动只是新增了中文解释注释，没有改变代码逻辑。

所以我没有回滚它们，也没有把它们当成今天的主要功能改动。

另外还看到 3 个新 PDF：

```text
rag_copilot_week2_execution_plan.pdf
rag_copilot_week3_execution_plan.pdf
rag_copilot_week4_execution_plan.pdf
```

这些是你新放进来的计划书，今天主要读取 Week2 计划书。

### 现有测试

修改前先运行：

```powershell
python -m pytest -q
```

结果：

```text
21 passed
```

这说明 Week1 v0 在 Day1 修改前是正常的。

## 4. 新增了哪些文件

### `docs/week2_upgrade_plan.md`

这个文件是 Week2 的升级设计文档。

它回答几个问题：

- Week1 v0 当前链路是什么？
- Week1 v0 已经做得好的地方是什么？
- Week1 v0 的短板是什么？
- 为什么要从单一路径 RAG 升级到 Hybrid RAG？
- Week2 每一天要做哪些模块？
- 哪些边界不能破坏？

里面最重要的设计点是：

```text
pipeline/ 放通用 RAG 机制
domains/ecommerce/ 放电商业务规则
evaluation/ 放评估数据和评估脚本
scripts/ 放压测或工具脚本
```

这条边界很重要。比如订单状态、退款状态、商品信息都属于电商业务，不应该写进通用 retriever 或 core pipeline。

### `docs/api.md`

这个文件记录 API 契约。

它分成两部分：

- Week1 当前 `/chat` 请求和响应结构
- Week2 目标响应结构

当前 `/chat` 请求必须包含：

```json
{
  "user_id": "u1",
  "session_id": "s1",
  "query": "退货政策是什么？"
}
```

注意：Week2 任务卡里的 curl 示例只写了 `query`，但我们当前项目的 `ChatRequest` 已经要求 `user_id` 和 `session_id`。所以文档和测试里继续使用完整请求，保证符合当前真实代码。

Week2 目标响应里会逐步增加：

```text
route
evidence_id
evidence_type
metadata
trace
```

这些字段不是今天立刻实现，而是先写清楚未来目标。

### `tests/test_week1_baseline.py`

这个文件是今天最关键的测试资产。

它的作用是：后面 Day2-Day7 做 Hybrid RAG 时，不能把 Week1 已经跑通的基础能力改坏。

新增了 4 个测试：

```text
test_week1_health_baseline
test_week1_chat_baseline_returns_answer
test_week1_chat_baseline_returns_evidence
test_week1_chat_baseline_fallback_stays_grounded
```

分别验证：

- `/health` 还能返回 ok。
- `/chat` 对退货政策问题还能返回 answer。
- `/chat` 对退货政策问题还能返回 evidence。
- 对无关问题仍然 fallback，不硬编答案。

这些测试不依赖真实 LLM，也不依赖外部数据库，符合 Day1 任务卡要求。

## 5. 修改了哪些文件

### `docs/failure_cases.md`

新增了 3 类 Week2 Day1 复盘出来的失败案例：

1. 订单状态问题被迫走文档检索。
2. 具体订单能否退货的问题需要结构化证据 + 文档证据。
3. 政策问题可能因为关键词不匹配导致证据为空或较弱。

这些失败案例不是为了展示项目不好，而是为了说明 Week2 的升级是有原因的。

比如：

```text
我的订单 ORD-1001 到哪里了？
```

这个问题不应该只搜 markdown 文档，因为订单状态是结构化事实，应该走订单查询工具。

再比如：

```text
订单 ORD-1001 的耳机现在还能退货吗？
```

这个问题同时需要：

- 订单状态
- 商品信息
- 签收时间或售后状态
- 退货政策

这就是 Hybrid RAG 的典型场景。

### `README.md`

新增了 `Week 2 Roadmap`。

它把 Week2 每一天的目标写到 README 里，让项目首页可以直接看出后续升级路线。

## 6. 新增测试代码怎么理解

以这个测试为例：

```python
def test_week1_chat_baseline_returns_evidence() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "baseline-user",
            "session_id": "baseline-session",
            "query": "退货政策是什么？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["evidence"], list)
    assert payload["evidence"]

    first_evidence = payload["evidence"][0]
    assert first_evidence["source"] == "return_policy.md"
    assert first_evidence["content"]
    assert isinstance(first_evidence["score"], float)
```

这段测试在检查：

- 请求必须成功，HTTP 状态码是 200。
- response 里必须有 `evidence`。
- evidence 必须是 list。
- evidence 不能是空列表。
- 第一个 evidence 应该来自 `return_policy.md`。
- evidence 必须有内容和分数。

为什么要检查 `return_policy.md`？

因为 “退货政策是什么？” 是一个稳定的 Week1 主路径问题。如果后面我们改了 retriever 或 metadata filter，导致它不再命中退货政策文档，这个测试就会提醒我们：主路径被破坏了。

## 7. 今天的验收结果

### Day1 baseline 测试

命令：

```powershell
python -m pytest tests\test_week1_baseline.py -q
```

结果：

```text
4 passed
```

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
25 passed
```

说明新增测试后，项目测试数量从 21 个变成 25 个。

### 手动 `/health`

命令：

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

返回：

```json
{
  "status": "ok",
  "service": "enterprise-rag-copilot",
  "version": "0.1.0",
  "environment": "development"
}
```

### 手动 `/chat`

命令：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

观察到：

- `fallback=false`
- `intent=policy_question`
- `evidence` 不为空
- evidence 包含 `return_policy.md`
- 有 `trace_id`

## 8. 遇到了什么问题

今天没有遇到阻塞性问题。

但测试时仍然看到了两个 warning：

### StarletteDeprecationWarning

大意是当前 `fastapi.testclient` 使用的 `httpx` 方式未来会变化。

它不影响当前测试通过，后续如果依赖升级，再根据 FastAPI/Starlette 官方建议处理。

### PytestCacheWarning

pytest 试图写 `.pytest_cache` 时，因为当前 Windows 路径里有特殊字符或临时 cache 路径问题，出现 cache warning。

它不影响测试正确性。之前 Week1 已经记录过这是本机环境噪音。

## 9. 今天没有做什么

今天没有实现：

- `intent_router.py`
- ecommerce schema/repository/tools
- hybrid RAG 主流程
- evidence builder
- fallback handler
- evaluation runner
- performance tracer
- cache
- load test

这些是 Week2 后续 Day2-Day7 的内容。

Day1 的重点是先把路线和基线固定住。

## 10. 复习重点

你复习今天内容时，可以重点理解这几句话：

- Baseline test 的作用是保护已有能力，防止后续升级破坏主路径。
- Hybrid RAG 不是“把东西写复杂”，而是把不同类型的问题交给更合适的数据源。
- 订单状态、退款状态、商品信息适合 structured tools。
- 退货政策、物流政策、保修说明适合 document retrieval。
- 同时需要结构化事实和政策文本的问题，才是 hybrid route 的价值所在。
- `pipeline/` 和 `domains/ecommerce/` 的边界，决定这个项目能不能从电商迁移到其他企业场景。

## 11. 今日三句面试表达

- 我在升级 RAG 前先补了 baseline tests，确保后续 Hybrid RAG 改造不会破坏 Week1 的主路径。
- Week2 的目标是从单一文档检索升级为 structured tools + document retrieval 的混合问答系统。
- 我没有虚构性能指标，而是先规划 evaluation、trace、cache 和 load test，后续所有数字都从可复现脚本产生。
