# Day 6 学习笔记：Docker、Logging、架构文档与 AI Workflow

## 1. 今天完成了什么

Day 6 的目标不是新增 RAG 功能，而是补齐工程项目最容易被忽略的部分：

- 可复现启动
- Docker 文件
- 基础 logging
- 架构说明
- AI 协作规范
- README 更新

这些内容不是“花边文档”。它们能让别人知道项目怎么跑、系统怎么分层、日志怎么定位问题、AI 生成的代码如何 review。

## 2. 修改和新增了哪些文件

### `Dockerfile`

Day 1 的 Dockerfile 只复制了：

```dockerfile
COPY app ./app
```

Day 5 后 `/chat` 需要读取：

```text
data/ecommerce/docs/
```

所以 Day 6 增加：

```dockerfile
COPY data ./data
```

为什么这很重要？

因为如果 Docker 镜像里没有 `data/`，容器启动后 `/chat` 会找不到 policy 文档。这个问题在本地运行时不一定暴露，但在 Docker 环境中会失败。

### `.dockerignore`

新增 `.dockerignore`，作用类似 `.gitignore`，但它控制的是 Docker build context。

主要排除：

```text
.git
.venv
__pycache__
.pytest_cache
pytest-cache-files-*
.env
.learnings
rag_copilot_week1_execution_plan.pdf
```

为什么要排除这些？

- `.git`：不需要放进镜像
- `.venv`：本地虚拟环境不应该进入镜像
- cache 文件：无用且会增大镜像上下文
- `.env`：可能包含本地秘密配置
- `.learnings`：学习笔记不属于运行时依赖
- PDF 计划文档：运行服务不需要

### `.env.example`

新增：

```text
APP_LOG_LEVEL=INFO
```

这个变量控制日志级别。

默认 `INFO` 的意思是：输出重要运行信息，但不输出太细的 debug 细节。

### `app/core/config.py`

新增配置字段：

```python
log_level: str = "INFO"
```

这样 logging 不用在代码里写死，可以从环境变量读取：

```text
APP_LOG_LEVEL=DEBUG
```

### `app/core/logging_config.py`

新增 logging 配置文件。

核心代码：

```python
def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
```

通俗理解：

这段代码告诉 Python：

- 日志级别是什么
- 日志格式是什么
- 日志输出到哪里

这里输出到 `stdout`，适合本地运行和 Docker 容器日志收集。

为什么不用 `print`？

因为 `logging` 可以控制级别、模块名、格式，也更适合之后接 production observability。

### `app/main.py`

Day 6 在 app 创建时配置 logging：

```python
configure_logging(settings)
```

并在启动时记录：

```python
logger.info(
    "app_startup service=%s version=%s environment=%s",
    settings.service_name,
    settings.service_version,
    settings.environment,
)
```

这条日志能帮助确认：

- 服务名
- 版本
- 当前环境

### `app/pipeline/rag_pipeline.py`

Day 6 在 RAG pipeline 中加入 stage-level logging。

主要记录：

- `trace_id`
- `stage`
- `top_k`
- `evidence_count`
- `latency_ms`

例如：

```python
logger.info("rag_stage trace_id=%s stage=start top_k=%s", trace_id, top_k)
```

检索后：

```python
logger.info(
    "rag_stage trace_id=%s stage=retrieve evidence_count=%s latency_ms=%.2f",
    trace_id,
    len(evidence),
    retrieval_ms,
)
```

为什么不记录完整 prompt？

因为 prompt 可能包含用户问题、内部文档片段、甚至敏感业务信息。Day 6 的日志只记录定位问题需要的元信息，不记录完整 prompt 或完整用户输入。

这是一个重要工程习惯：日志要有用，但不能泄露敏感内容。

### `docs/design/architecture.md`

新增架构文档。

它说明：

- 项目目标
- runtime flow
- API layer
- schema layer
- core pipeline
- domain adapter
- data layer
- logging
- Week 1 能力
- 已知限制
- Week 2 方向

这个文档的价值是：让 reviewer 和未来的你能快速理解项目边界，而不是只能从代码里猜。

### `docs/ai-development-workflow.md`

新增 AI 协作规范。

它明确：

- Codex 输出是候选实现
- 每天先列文件计划
- 每天要测试或验收
- 每天更新学习笔记
- commit 前要人工 review
- 每次 git 后更新 git 学习文档
- 失败要记录

这个文档把你和 Codex 的协作方式正式写进项目，避免后续“AI 想怎么改就怎么改”。

### `README.md`

README 从 Day 1 的骨架说明升级为 Week 1 当前状态。

新增内容包括：

- `/chat` API 示例
- Docker build/run 命令
- 当前项目结构
- Week 1 Progress
- Design Notes
- Documentation links

README 是别人进入项目的第一入口，所以它必须能回答：

- 这是什么项目？
- 怎么启动？
- 有哪些 API？
- 项目结构是什么？
- 当前能力和限制是什么？

## 3. 怎么验收的

### 全量测试

```powershell
python -m pytest -q
```

结果：

```text
21 passed
```

### Docker CLI 检查

```powershell
docker --version
```

结果：

```text
Docker version 29.3.1, build c2be9cc
```

说明 Docker CLI 存在。

### Docker build

尝试运行：

```powershell
docker build -t enterprise-rag-copilot:week1 .
```

第一次失败：

```text
ERROR: open C:\Users\hp\.docker\buildx\.lock: Access is denied.
```

提升权限后再次运行，失败为：

```text
ERROR: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

这说明当前问题是 Docker Desktop Linux engine 没有运行或不可访问。

这个问题已经记录在：

```text
.learnings/ERRORS.md
```

### 本地服务验收

启动：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

请求 `/health`：

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

返回正常。

请求 `/chat`：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

返回 evidence-backed answer，说明 Day 6 logging 改动没有破坏 RAG pipeline。

## 4. 遇到了什么问题

### Docker daemon 不可用

Docker CLI 存在，但 Docker Desktop Linux engine 没有运行或不可访问。

解决方式不是改代码，而是启动 Docker Desktop 后重新运行：

```powershell
docker build -t enterprise-rag-copilot:week1 .
docker run --rm -p 8000:8000 enterprise-rag-copilot:week1
```

这属于环境问题，不是当前 Dockerfile 已知语法错误。

## 5. 今天的设计取舍

### 不引入 Docker Compose

Day 6 明确不做复杂 Compose。

当前项目只有一个 FastAPI 服务，还没有数据库、Redis、vector DB，所以单服务 Dockerfile 足够。

### logging 只记录元信息

RAG pipeline 记录：

- stage
- trace_id
- evidence_count
- latency

不记录：

- 完整 prompt
- 完整用户 query
- 完整内部文档上下文

这是为了降低敏感信息泄露风险。

### README 写当前真实能力

README 没有写“生产可用”或虚构性能指标。

它明确当前是 Week 1 naive RAG v0，keyword fallback 不是 semantic embedding。

## 6. 当前状态

当前项目已经具备：

- FastAPI 服务
- `/health`
- `/chat`
- naive RAG v0
- evidence list
- fallback
- trace_id
- Dockerfile
- `.dockerignore`
- logging 配置
- architecture 文档
- AI workflow 文档
- failure cases 文档
- 学习笔记

当前仍待补：

- Docker Desktop 启动后重新验证 docker build/run
- Day 7 全链路收尾和 Week 1 summary
- 更完整 README 示例和最终验收清单

## 7. 今日三句面试表达

- 我为项目补充 Dockerfile 和 `.env.example`，让别人可以更容易复现我的运行环境。
- 我用 logging 记录 pipeline 关键阶段，而不是依赖临时 print。
- 我把 AI Coding workflow 写进文档，说明 AI 负责辅助生成，设计、review、测试和合并由我控制。
