# Week2 Day 2 学习笔记：Intent Router 与电商 Structured Tools

## 1. 今天完成了什么

Week2 Day2 的目标是：不要让所有问题都走文档检索。订单状态、退款状态、商品信息这类“精确事实”应该走结构化工具。

今天完成了：

- 新增通用 intent router 机制
- 新增电商 schema
- 新增电商 repository
- 新增电商 structured tools
- 新增退款 mock 数据
- `/chat` 接入 intent router
- `/chat` 支持 `route` 字段
- `/chat` 支持 structured-only 路径
- `/chat` 预留并实现一个最小 hybrid 路径
- 新增工具测试、router 测试、chat 路由测试
- 更新 README 和 API 文档
- 更新 failure cases
- 新增本学习笔记

## 2. 今天为什么要做 structured tools

Week1 的 naive RAG v0 只有一条路径：

```text
用户问题 -> 文档检索 -> 拼 prompt -> 生成回答
```

这对政策类问题可以工作，例如：

```text
退货政策是什么？
```

因为答案确实在 markdown 文档里。

但这类问题不适合只靠文档检索：

```text
我的订单 ORD-1001 现在是什么状态？
退款 RF1001 处理到哪一步了？
商品 P-HEADPHONE-01 保修多久？
```

原因是：订单状态、退款状态、商品价格是结构化事实，不是知识库文章。让向量检索去“猜”这些事实，既不稳定，也不可信。

所以 Day2 引入：

```text
intent router -> structured tools -> structured evidence
```

## 3. 新增了哪些核心文件

### `app/pipeline/intent_router.py`

这个文件放的是通用路由机制。

它没有读取订单 JSON，也没有查询退款数据，只做一件事：

```text
输入 query
输出 RouteDecision
```

`RouteDecision` 包含：

```text
intent
route
required_slots
slots
confidence
reason
```

例如：

```text
我的订单 ORD-1001 现在是什么状态？
```

会得到类似：

```json
{
  "intent": "order_status",
  "route": "structured_only",
  "required_slots": ["order_id"],
  "slots": {
    "order_id": "ORD-1001"
  }
}
```

这里的关键词是 `structured_only`，意思是：这个问题不应该先去搜 FAQ，而应该调用结构化工具。

### `app/domains/ecommerce/schema.py`

这个文件定义电商领域的数据模型：

- `Order`
- `Product`
- `Refund`
- `ToolResult`

`ToolResult` 是 structured tools 的统一返回格式。

它包含：

```text
tool_name
success
message
data
evidence
error_code
```

为什么需要 `ToolResult`？

因为工具不只是“查到/查不到”，还要告诉上层：

- 用的是哪个工具
- 是否成功
- 查到的数据是什么
- 失败原因是什么
- 有没有可以进入最终回答的 evidence

这会让后续 evidence builder、fallback handler 更容易接入。

### `app/domains/ecommerce/repository.py`

这个文件负责读取 mock JSON 数据。

它把 JSON 读取封装起来，提供：

```python
get_order(order_id)
get_product(product_id)
get_refund(refund_id)
```

这样做的好处是：

- API route 不直接读 JSON。
- tools 不关心文件路径细节。
- 以后如果从 JSON 换成 SQLite，主要改 repository，不需要到处改业务代码。

它还做了一个小的 ID 归一化：

```text
EC1001 -> ORD-1001
ORD1001 -> ORD-1001
RF-1001 -> RF1001
```

这是为了兼容计划书里的 `EC1001` 示例，同时保留当前数据里的 `ORD-1001`。

### `app/domains/ecommerce/tools.py`

这个文件是真正的 structured tools。

今天实现了 3 个工具：

```python
get_order_status(order_id)
get_product_info(product_id)
get_refund_status(refund_id)
```

以 `get_order_status` 为例：

```text
输入: ORD-1001
查询: repository.get_order("ORD-1001")
输出: ToolResult
```

成功时会返回 structured evidence：

```json
{
  "source": "structured:orders:ORD-1001",
  "content": "{\"order_id\":\"ORD-1001\",\"status\":\"delivered\"}",
  "score": 1.0
}
```

这里 `score=1.0` 不是检索相似度，而是表示结构化工具精确命中了记录。后续如果做更严格的 evidence schema，可以把 evidence type 拆出来。

失败时会返回明确错误，例如：

```text
missing_order_id
order_not_found
missing_refund_id
refund_not_found
missing_product_id
product_not_found
```

这比一句模糊的“我不知道”更适合工程系统。

### `data/ecommerce/mock/refunds.json`

Week1 已经有：

```text
orders.json
products.json
```

Day2 补了：

```text
refunds.json
```

这样退款工具有真实 mock 数据可以查。

## 4. `/chat` 现在怎么工作

Day2 之后，`/chat` 的大致流程变成：

```text
POST /chat
-> intent_router.route(query)
-> 根据 route 决定路径
```

### structured_only

例如：

```text
我的订单 ORD-1001 现在是什么状态？
```

流程：

```text
intent_router -> order_status / structured_only
-> get_order_status("ORD-1001")
-> 返回 structured evidence
-> ChatResponse
```

返回里会看到：

```json
{
  "intent": "order_status",
  "route": "structured_only",
  "evidence": [
    {
      "source": "structured:orders:ORD-1001"
    }
  ]
}
```

这说明它没有去搜 `faq.md`。

### document_only

例如：

```text
退货政策是什么？
```

流程：

```text
intent_router -> return_policy / document_only
-> 原来的 RAG pipeline
-> 返回 document evidence
```

返回里会看到：

```json
{
  "intent": "return_policy",
  "route": "document_only",
  "evidence": [
    {
      "source": "return_policy.md"
    }
  ]
}
```

### hybrid

例如：

```text
订单 ORD-1001 的耳机现在还能退货吗？
```

这个问题同时需要：

- 订单结构化事实
- 退货政策文档

今天做的是最小 hybrid：

```text
get_order_status -> structured evidence
RAG pipeline -> document evidence
合并 evidence -> ChatResponse(route="hybrid")
```

注意：这还不是完整 hybrid 引擎。Day4 会专门做 evidence builder，Day5 会完善 fallback handler。

### fallback

例如：

```text
我的订单现在是什么状态？
```

router 可以识别这是订单状态问题，但没有订单号。

所以工具返回：

```text
missing_order_id
```

最终 `/chat` 返回：

```json
{
  "intent": "order_status",
  "route": "fallback",
  "fallback": true,
  "fallback_reason": "missing_order_id"
}
```

这比瞎猜订单更安全。

## 5. 修改了哪些已有文件

### `app/schemas/chat.py`

新增了：

```python
route: RouteName = "document_only"
```

`route` 表示系统选择的处理路径：

```text
structured_only
document_only
hybrid
fallback
```

这会成为 Week2 后续 evidence、fallback、trace 的核心字段。

### `app/api/routes.py`

以前 `/chat` 直接调用 RAG pipeline。

现在 `/chat` 会先调用：

```python
get_ecommerce_intent_router().route(request.query)
```

然后根据 `decision.route` 分流。

这里要注意：route 只做编排，不直接读 JSON。真正读取数据的是 repository，真正业务查询的是 tools。

### `app/pipeline/rag_pipeline.py`

原来的 RAG pipeline 仍然保留。

只是让它可以接收：

```python
intent
route
```

这样文档问题可以返回更准确的 intent，例如：

```text
return_policy
warranty
logistics
```

而不是全部写成 Week1 的 `policy_question`。

## 6. 新增了哪些测试

### `tests/test_ecommerce_tools.py`

测试 structured tools。

覆盖：

- 订单状态查询成功
- `EC1001` 能归一化到 `ORD-1001`
- 缺少订单号返回 `missing_order_id`
- 订单不存在返回 `order_not_found`
- 商品信息查询成功
- 退款状态查询成功
- 退款单不存在返回 `refund_not_found`

### `tests/test_intent_router.py`

测试 intent router。

覆盖至少 7 类：

- `order_status`
- `refund`
- `return_policy`
- `warranty`
- `logistics`
- `hybrid`
- `unknown`

### `tests/test_week2_chat_routes.py`

测试 `/chat` 真实路由。

重点确认：

- 订单状态走 `structured_only`
- 退款状态走 `structured_only`
- 缺少订单号走 `fallback`
- 退货政策仍然走 `document_only`

### 更新的旧测试

`tests/test_chat_contract.py` 增加了 `route` 字段检查。

`tests/test_rag_pipeline.py` 增加了 document route 检查。

## 7. 今天的验收结果

### Day2 指定测试

命令：

```powershell
python -m pytest tests\test_ecommerce_tools.py tests\test_intent_router.py -q
```

结果：

```text
15 passed
```

### 路由和契约测试

命令：

```powershell
python -m pytest tests\test_week2_chat_routes.py tests\test_chat_contract.py tests\test_rag_pipeline.py tests\test_week1_baseline.py -q
```

结果：

```text
17 passed
```

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
44 passed
```

### 手动订单状态请求

命令：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day2","query":"我的订单 ORD-1001 现在是什么状态？"}'
```

观察到：

```text
intent=order_status
route=structured_only
evidence.source=structured:orders:ORD-1001
fallback=false
```

### 手动退款状态请求

命令：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_002","session_id":"manual-day2","query":"退款 RF1001 处理到哪一步了？"}'
```

观察到：

```text
intent=refund
route=structured_only
evidence.source=structured:refunds:RF1001
fallback=false
```

### 手动退货政策请求

命令：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day2","query":"退货政策是什么？"}'
```

观察到：

```text
intent=return_policy
route=document_only
evidence.source=return_policy.md
fallback=false
```

## 8. 今天遇到的问题和处理

今天没有遇到阻塞性代码问题。

仍然存在两个已知 warning：

- `StarletteDeprecationWarning`
- `PytestCacheWarning`

它们不影响测试通过，和 Week1/Day1 一样属于当前环境或依赖版本提醒。

今天新增的真实限制已经写进 `docs/failure_cases.md`：

- structured tools 需要明确 ID。
- hybrid route 目前还是最小版本，不是完整 eligibility decision engine。

## 9. 复习重点

你复习 Day2 时，可以重点抓这几条：

- `intent_router` 只分类和抽取 slot，不查询业务数据。
- `repository` 负责封装 JSON 读取，以后可以替换为 SQLite 或数据库。
- `tools` 负责业务查询，并统一返回 `ToolResult`。
- `ToolResult.evidence` 让 structured data 可以进入证据链，而不是只拼进 answer。
- `route` 是 Week2 的关键字段，它告诉我们这次回答走的是结构化工具、文档检索、混合路径还是 fallback。
- 缺少 ID 时 fallback 是正确行为，不能为了看起来“聪明”而猜订单或商品。

## 10. 今日三句面试表达

- 订单状态、退款状态和商品信息属于精确事实，我用 structured tools 处理，而不是让向量检索猜。
- Intent router 的职责是做路由决策和 slot 抽取，不直接查询 repository，这样职责边界更清晰。
- 我把电商查询逻辑放在 domain adapter 和 tools 中，保持 core pipeline 可迁移到其他企业场景。
