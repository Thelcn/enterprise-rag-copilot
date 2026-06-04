# Day 7 学习笔记：Week 1 收尾、全链路验收与总结

## 1. 今天完成了什么

Day 7 的目标不是新增大功能，而是确认 Week 1 的 RAG v0 是否真正可运行、可解释、可测试、可继续迭代。

今天完成了：

- 跑全量测试
- 手动验证 `/health`
- 手动验证 `/chat` 成功 query
- 手动验证 `/chat` fallback query
- 更新 README
- 更新 API contract
- 更新 architecture 文档
- 更新 failure cases
- 新增 `notes/failure_log.md`
- 新增 `notes/week1_summary.md`
- 新增 Day 7 学习笔记

## 2. 为什么 Day 7 主要是文档和验收

Week 1 前 6 天已经完成了核心工程链路：

```text
FastAPI -> /chat contract -> data -> loader -> chunk -> retrieve -> prompt -> answer
```

Day 7 如果继续堆新功能，反而会让项目变得不稳定。

所以 Day 7 的重点是：

- 确认已有功能真的能跑
- 把启动方式写清楚
- 把 API 示例写清楚
- 把失败和限制写清楚
- 把 Week 2 方向写清楚

这体现了工程项目和 toy demo 的区别：真正的阶段完成，不只是“代码看起来能跑”，还要让别人能复现、review、理解和继续开发。

## 3. 今天怎么验收的

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
21 passed
```

这说明 Day 1 到 Day 5 的测试仍然都通过：

- health endpoint
- chat contract
- document loader
- retriever
- RAG pipeline

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

### 手动 `/chat` 成功 query

命令：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

观察到：

- `fallback=false`
- evidence 不为空
- evidence 包含 `return_policy.md`
- trace_id 存在

### 手动 `/chat` fallback query

命令：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"量子咖啡会员积分怎么兑换？"}'
```

观察到：

- `fallback=true`
- `intent=unknown`
- `evidence=[]`
- `fallback_reason` 说明没有足够证据

这说明系统没有对无关问题硬编答案。

## 4. 更新了哪些文档

### `README.md`

README 是项目入口。

今天补充了：

- Docker Desktop daemon 的已知环境限制
- fallback `/chat` 示例
- Day 7 progress
- Week 1 verification
- notes 文档入口

README 现在能回答：

- 项目是什么
- 怎么启动
- 怎么测试
- API 怎么调用
- Week 1 做到了什么
- 当前限制是什么

### `docs/contracts/query_api.md`

API 契约文档补充了：

- fallback request/response example
- Week 1 verification
- 更新 `trace_id` 说明，不再写成 Day 2 mock 语境

这个文档的作用是固定 `/chat` 的外部形状。

即使 Day 2 是 mock、Day 5 是 RAG v0，响应字段仍然稳定。

### `docs/design/architecture.md`

架构文档补充了：

- Week 1 final verification
- Docker build/run 仍需 Docker Desktop Linux engine 可用后复验

这个文档的作用是解释系统边界：

- API layer
- schema layer
- core pipeline
- domain adapter
- data layer

### `docs/failure_cases.md`

新增了第 4 个 RAG v0 局限：

```text
Broad Chunks Can Pull Weakly Related Evidence
```

这是一个真实观察到的问题：查询退货政策时，系统能命中 `return_policy.md`，但有时也会带出较弱相关的 FAQ 或物流 evidence。

这说明 Week 1 的 chunking 和 keyword fallback 可运行，但还不够精准。

### `notes/failure_log.md`

这个文件记录 Week 1 真实问题：

- `.venv` ensurepip 权限失败
- Git lock/permission 问题
- PowerShell curl JSON 引号问题
- retriever import 拼写修正
- Docker daemon 不可用
- pytest cache warning

它的价值是：失败不藏起来，而是变成可复盘的工程经验。

### `notes/week1_summary.md`

这个文件总结了：

- Week 1 完成内容
- 当前能力
- 验收结果
- Git history
- 设计决策
- 已知限制
- Week 2 plan
- 面试表达

这是 Week 1 的阶段总结，也可以作为之后简历/面试项目复盘的材料基础。

## 5. 今天没有做什么

Day 7 没有新增：

- SQL tool
- SQLite
- intent router
- real embedding
- real LLM
- reranker
- UI
- production deployment

这是符合 Day 7 任务卡的。今天只修复阻塞验收的问题、整理文档和总结，不新增复杂功能。

## 6. 遇到了什么问题

今天没有新的代码问题。

仍然存在两个环境/质量注意点：

### Docker daemon 未运行

Docker CLI 存在，但 Docker Desktop Linux engine 不可用，所以 Docker build/run 没有完成。

这个问题已经写进：

```text
.learnings/ERRORS.md
notes/failure_log.md
notes/week1_summary.md
```

### pytest cache warning

测试全部通过，但 pytest 仍然有本机 cache path warning。

这不影响当前 correctness，但已经记录为环境噪音。

## 7. 当前 Week 1 状态

当前项目已经具备：

- `/health`
- `/chat`
- stable ChatResponse contract
- ecommerce demo docs
- document loader
- chunker
- keyword fallback retriever
- prompt builder
- answer generator
- naive RAG pipeline
- evidence list
- fallback
- trace_id
- logging
- Dockerfile
- architecture docs
- AI workflow docs
- failure cases
- failure log
- Week 1 summary

## 8. 今日三句面试表达

- 第一周我完成了企业 RAG Copilot 的工程底座，并跑通了 naive RAG v0。
- 我没有把项目写成固定电商客服脚本，而是保留 core pipeline + domain adapter 的可迁移结构。
- Week 2 我会把 v0 升级为 SQL + 文档检索混合流程，并补 evidence citation、fallback、evaluation 和 performance tracing。
