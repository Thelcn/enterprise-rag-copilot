# Day 1 学习笔记：FastAPI 工程骨架与 /health 接口

## 1. 今天完成了什么

Day 1 的目标是把项目从“只有计划文档”变成一个可以启动、可以测试、可以继续迭代的 FastAPI 工程骨架。

今天没有做 RAG 检索、文档切分、向量库、电商规则，也没有实现 `/chat`。这是有意为之：第一天的重点是先建立一个稳定的服务入口，保证后续功能可以挂在清晰的工程结构上。

最终完成了：

- 创建 FastAPI 应用入口
- 创建 API 路由文件
- 创建配置管理文件
- 实现 `GET /health`
- 编写健康检查测试
- 编写 README 初版
- 编写最小依赖文件
- 编写 `.env.example`
- 编写 Dockerfile
- 运行测试和真实 HTTP 验收

## 2. 新建了哪些文件

### `README.md`

作用：说明项目是什么、如何启动、当前 API 是什么、当前目录结构是什么。

这里特别写明了项目定位是 `transferable enterprise RAG Copilot`，也就是“可迁移的企业级 RAG Copilot”，而不是一个固定写死的电商客服脚本。

这样做的原因是：后续虽然会先用电商售后做 demo，但核心代码应该能迁移到 HR、IT support、内部知识库等其他场景。

### `requirements.txt`

作用：记录项目运行和测试需要的 Python 依赖。

当前内容：

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
pytest
httpx
```

这些依赖的作用：

- `fastapi`：Web API 框架，用来实现 `/health`、后续 `/chat`
- `uvicorn[standard]`：FastAPI 常用的 ASGI 启动服务器
- `pydantic`：定义和校验数据结构，后续会用于 `ChatRequest`、`ChatResponse`
- `pydantic-settings`：从环境变量或 `.env` 中读取配置
- `python-dotenv`：支持读取 `.env` 文件
- `pytest`：测试框架
- `httpx`：FastAPI 测试客户端依赖会用到

### `.env.example`

作用：给别人一个环境变量模板。

内容：

```text
APP_SERVICE_NAME=enterprise-rag-copilot
APP_SERVICE_VERSION=0.1.0
APP_ENVIRONMENT=development
```

注意：`.env.example` 不是秘密文件，它只是告诉别人“你可以配置哪些变量”。真正的 `.env` 一般不提交。

### `Dockerfile`

作用：让项目后续可以被 Docker build/run，保证别人能更容易复现运行环境。

当前 Dockerfile 做了几件事：

1. 使用 `python:3.11-slim` 作为基础镜像
2. 设置工作目录 `/app`
3. 安装 `requirements.txt`
4. 复制 `app/` 目录
5. 暴露 8000 端口
6. 用 `uvicorn` 启动 FastAPI 服务

当前还没有运行 Docker 验收，这是 Day 6 的重点；Day 1 先放一个最小可用版本。

### `app/main.py`

作用：FastAPI 应用入口。

核心代码：

```python
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.service_name, version=settings.service_version)
    app.include_router(router)
    return app


app = create_app()
```

这段代码可以拆开理解：

- `FastAPI(...)` 创建一个 Web API 应用
- `get_settings()` 读取服务名、版本号、运行环境等配置
- `app.include_router(router)` 把 API 路由注册到应用里
- `app = create_app()` 是 `uvicorn app.main:app` 能找到服务入口的关键

为什么不把所有代码都写在 `main.py`？

因为如果后续 `/health`、`/chat`、配置、RAG pipeline 都塞进 `main.py`，这个文件会很快变得混乱。第一天就拆出 `routes.py` 和 `config.py`，是为了让工程结构从一开始就可维护。

### `app/api/routes.py`

作用：放 API 路由。

核心代码：

```python
from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
    }
```

这段代码定义了一个 `GET /health` 接口。

当用户访问：

```text
http://127.0.0.1:8000/health
```

服务会返回：

```json
{
  "status": "ok",
  "service": "enterprise-rag-copilot",
  "version": "0.1.0",
  "environment": "development"
}
```

为什么 `/health` 不只是返回 `"ok"`？

因为工程项目里的健康检查最好返回稳定结构。这样后续部署、监控、测试都可以明确知道：

- 服务是否可用
- 当前服务名是什么
- 当前版本是什么
- 当前运行环境是什么

### `app/core/config.py`

作用：集中管理配置。

核心代码：

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "enterprise-rag-copilot"
    service_version: str = "0.1.0"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

这段代码的重点：

- `Settings` 定义了服务配置
- 默认服务名是 `enterprise-rag-copilot`
- 默认版本是 `0.1.0`
- 默认环境是 `development`
- `env_prefix="APP_"` 表示它会读取 `APP_SERVICE_NAME`、`APP_SERVICE_VERSION`、`APP_ENVIRONMENT`
- `@lru_cache` 表示配置只创建一次，避免每次请求都重新读取

通俗理解：`config.py` 就像项目的“配置中心”。以后如果要加模型配置、检索参数、环境开关，也应该优先放这里，而不是散落在各个函数里。

### `tests/test_health.py`

作用：测试 `/health` 是否按预期工作。

核心代码：

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_service_metadata() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "enterprise-rag-copilot",
        "version": "0.1.0",
        "environment": "development",
    }
```

这段测试做了两件事：

1. 请求 `/health`
2. 断言返回状态码和 JSON 内容完全符合预期

为什么要测得这么具体？

因为 `/health` 是服务的第一个稳定接口。如果它的字段随便变，后续 README、部署脚本、监控或测试都会受到影响。第一天就固定结构，可以减少后续乱改接口的风险。

## 3. 今天没有做什么

根据 Day 1 任务卡，今天明确没有做：

- 没有创建 `app/pipeline/`
- 没有写 retriever
- 没有写 chunker
- 没有写 prompt builder
- 没有写 answer generator
- 没有写电商退货、物流、订单规则
- 没有实现 `/chat`

这是符合计划的。Day 1 的目标是工程骨架，不是 RAG 功能。

## 4. 怎么验收的

### 安装依赖

因为本机虚拟环境创建失败，最后使用的是当前用户 Python 环境安装依赖：

```powershell
python -m pip install -r requirements.txt --user
```

### 跑测试

```powershell
python -m pytest -q
```

结果：

```text
1 passed
```

### 启动服务

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 请求 `/health`

```powershell
curl.exe http://127.0.0.1:8000/health
```

返回：

```json
{"status":"ok","service":"enterprise-rag-copilot","version":"0.1.0","environment":"development"}
```

说明服务不仅在测试里能跑，也能通过真实 HTTP 请求访问。

## 5. 遇到了什么问题

### 问题 1：当前目录不是 git 仓库

运行：

```powershell
git status --short
```

返回：

```text
fatal: not a git repository (or any of the parent directories): .git
```

说明当前项目目录还没有初始化 git。

这个问题没有阻塞 Day 1 代码实现和测试，但会影响后续“每天至少一个 commit”的要求。之后可以在你确认后初始化 git。

### 问题 2：系统 Python 缺少 FastAPI 和 pytest

检查依赖时发现：

```text
fastapi=False
pytest=False
```

所以第一次跑测试失败：

```text
No module named pytest
```

解决方式：按 `requirements.txt` 安装依赖。

### 问题 3：`.venv` 创建失败

运行：

```powershell
python -m venv .venv
```

失败在 `ensurepip` 阶段。

进一步运行：

```powershell
.\.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip
```

出现 Windows 权限错误：

```text
ERROR: Could not install packages due to an OSError: [WinError 5] 拒绝访问
```

这说明本机在给 `.venv` 安装 pip 时遇到了权限问题。

临时解决方式：

```powershell
python -m pip install -r requirements.txt --user
```

也就是把依赖安装到当前用户 Python 环境，而不是项目 `.venv`。这样完成了 Day 1 验收。

这个问题已经记录在：

```text
.learnings/ERRORS.md
```

## 6. 今天的代码结构为什么这样设计

### 为什么有 `main.py`

`main.py` 是应用启动入口。`uvicorn app.main:app` 里的意思是：

- 找到 `app/main.py`
- 从里面找到变量 `app`
- 把这个 FastAPI 应用启动起来

### 为什么有 `routes.py`

`routes.py` 专门放 API 路由。这样以后新增 `/chat` 时，可以继续在 API 层处理请求和响应，而不是把所有接口都写在 `main.py`。

### 为什么有 `config.py`

配置应该集中管理。比如服务名、版本、环境、未来的模型参数、检索参数，都不应该散落在业务代码中。

### 为什么先写测试

测试让 `/health` 的行为可复现。以后如果有人改坏了返回结构，测试会立刻失败。

这就是“工程骨架”的意义：不是只有代码能跑，而是代码有边界、有验收、有继续迭代的基础。

## 7. 当前状态

当前项目已经具备：

- 最小 FastAPI 应用
- `GET /health`
- 配置管理
- 健康检查测试
- README 初版
- 最小 Dockerfile

当前项目还不具备：

- `/chat`
- Pydantic chat schema
- document loader
- chunking
- retrieval
- evidence-grounded answer
- fallback
- trace_id

这些会从 Day 2 开始逐步补上。

## 8. 之后每天我会自动补这类文档

从 Day 2 开始，每天任务完成后，我会自动在 `.learnings/` 下新增或更新一份对应的学习笔记，内容包括：

- 当天目标
- 修改了哪些文件
- 写了哪些代码
- 关键代码怎么理解
- 为什么这样设计
- 运行了哪些验收命令
- 遇到了什么问题
- 问题如何解决
- 当前还剩哪些风险或 TODO

这样你可以把 `.learnings/` 当作这个项目的学习复盘目录，一边做项目，一边积累自己的工程解释材料。
