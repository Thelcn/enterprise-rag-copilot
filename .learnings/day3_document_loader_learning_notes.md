# Day 3 学习笔记：电商 demo 数据与通用 Document Loader

## 1. 今天完成了什么

Day 3 的目标是让“数据进入系统”。

前两天我们只有服务入口和 API 契约，`/chat` 还没有任何可检索的数据。今天补上两类数据：

- 结构化 mock 数据：订单、商品
- 非结构化 policy 文档：FAQ、退货政策、物流政策、保修政策

同时实现了一个通用的 markdown document loader。这个 loader 不懂电商业务，它只负责读取 `.md` 文件并转换成统一的 `Document` 对象。

今天完成了：

- 创建 `orders.json`
- 创建 `products.json`
- 创建 4 个电商 policy markdown 文档
- 新增 `Document` schema
- 新增通用 `load_markdown_documents`
- 新增 ecommerce domain adapter
- 新增 document loader 测试
- 全量测试通过

## 2. 新建了哪些数据文件

### `data/ecommerce/mock/orders.json`

这个文件模拟订单数据。

每条订单包含：

```json
{
  "order_id": "ORD-1001",
  "user_id": "demo_user_001",
  "product_id": "P-HEADPHONE-01",
  "status": "delivered",
  "created_at": "2026-05-28T10:30:00+08:00",
  "refund_status": "not_requested"
}
```

字段含义：

- `order_id`：订单号
- `user_id`：用户 ID
- `product_id`：商品 ID
- `status`：订单状态，比如 `delivered`、`shipped`、`processing`
- `created_at`：下单时间
- `refund_status`：退款状态，比如 `not_requested`、`approved`、`refunded`

这类数据是结构化数据。后续 Week 2 更适合用 SQL 或 structured tool 查询。

例如：

```text
我的 ORD-1001 订单现在是什么状态？
```

这类问题不适合靠 RAG 文档检索回答，因为订单状态是精确事实，应该查结构化数据。

### `data/ecommerce/mock/products.json`

这个文件模拟商品数据。

每个商品包含：

```json
{
  "product_id": "P-HEADPHONE-01",
  "name": "Aurora Noise-Canceling Headphones",
  "category": "audio",
  "price": 499.0,
  "warranty_months": 12,
  "returnable": true
}
```

字段含义：

- `product_id`：商品 ID
- `name`：商品名
- `category`：商品类别
- `price`：价格
- `warranty_months`：保修月数
- `returnable`：是否支持退货

这也是结构化数据。后续可以和订单数据一起用于 SQL tool 或 metadata filtering。

### `data/ecommerce/docs/faq.md`

这个文件记录售后常见问题。

内容包括：

- 如何申请售后
- 需要准备哪些材料
- 售后处理时间

这类内容是非结构化文本，适合做 RAG 检索。

### `data/ecommerce/docs/return_policy.md`

这个文件记录退货政策。

内容包括：

- 七天无理由退货
- 不支持无理由退货的情况
- 运费说明

后续 Day 4 检索“退货”时，应该能返回这个文件里的相关 chunk。

### `data/ecommerce/docs/logistics_policy.md`

这个文件记录物流政策。

内容包括：

- 发货时间
- 配送范围
- 物流异常处理

### `data/ecommerce/docs/warranty_policy.md`

这个文件记录保修政策。

内容包括：

- 保修期限
- 保修范围
- 不属于保修范围的情况

## 3. 新增的核心代码

### `app/schemas/document.py`

这个文件定义了统一的 `Document` 数据结构。

代码：

```python
from pydantic import BaseModel, Field


MetadataValue = str | int | float | bool | None


class Document(BaseModel):
    id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)
```

通俗理解：`Document` 是“进入 RAG 系统的一篇原始文档”。

字段含义：

- `id`：文档 ID
- `source`：来源，比如 `return_policy.md`
- `content`：文档正文
- `metadata`：附加信息，比如文档类型、路径、文件后缀

为什么需要 `metadata`？

因为后续检索不一定只看正文。

例如 Week 2 可以做：

- 只检索 `document_type=return_policy` 的文档
- 只检索某个 product category 相关政策
- 只使用某个 policy version

Day 3 先把 metadata 字段留下，就是给后续扩展留接口。

### `app/pipeline/document_loader.py`

这个文件实现通用 markdown loader。

核心函数：

```python
def load_markdown_documents(path: str | Path) -> list[Document]:
```

它接受一个路径，可以是：

- 一个 markdown 文件
- 一个目录

如果是目录，它会递归读取目录下所有 `.md` 文件：

```python
markdown_files = sorted(root.rglob("*.md"))
```

然后每个 markdown 文件都会被转换成一个 `Document`：

```python
Document(
    id=_build_document_id(relative_path),
    source=file_path.name,
    content=content,
    metadata={
        "source": file_path.name,
        "path": relative_path,
        "document_type": file_path.stem,
        "file_extension": file_path.suffix.lower(),
    },
)
```

这里几个字段很重要：

- `source=file_path.name`：只保存文件名，比如 `return_policy.md`
- `content=content`：保存 markdown 正文
- `document_type=file_path.stem`：从文件名提取类型，比如 `return_policy`
- `path=relative_path`：保存相对路径，方便之后定位文件

#### 为什么这个 loader 是通用的？

因为它没有写：

```python
if file_name == "return_policy.md":
```

也没有写：

```python
if "退货" in content:
```

它只知道一件事：读取 markdown 文件并生成 `Document`。

所以以后换成 HR domain，可以读取：

```text
data/hr/docs/leave_policy.md
```

换成 IT support domain，也可以读取：

```text
data/it/docs/password_reset.md
```

这就是 core pipeline 要保持通用的意思。

#### 文档 ID 是怎么来的

代码：

```python
def _build_document_id(relative_path: str) -> str:
    return f"doc_{uuid5(NAMESPACE_URL, relative_path).hex}"
```

这里用了 `uuid5`，它的特点是：同样的输入会生成同样的 UUID。

例如 `return_policy.md` 每次生成的 ID 都会稳定，不会每次运行都变。

为什么不用随机 UUID？

因为文档 loader 的结果最好稳定。稳定 ID 对测试、调试、后续索引更新都更友好。

### `app/domains/ecommerce/adapter.py`

这个文件是电商 domain adapter。

代码：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ECOMMERCE_DOCS_DIR = PROJECT_ROOT / "data" / "ecommerce" / "docs"
```

它定义了电商 policy 文档的默认位置。

然后提供两个函数：

```python
def get_policy_doc_paths(data_dir: str | Path = DEFAULT_ECOMMERCE_DOCS_DIR) -> list[Path]:
```

作用：返回电商 policy markdown 文件路径。

```python
def load_ecommerce_documents(data_dir: str | Path = DEFAULT_ECOMMERCE_DOCS_DIR) -> list[Document]:
    return load_markdown_documents(data_dir)
```

作用：从电商 docs 目录加载 `Document`。

这里的分层很关键：

- `document_loader.py`：通用，只会读取 markdown
- `adapter.py`：电商专用，知道电商文档目录在哪里

这就避免了把电商路径和业务规则塞进 core pipeline。

## 4. 新增的测试

### `tests/test_document_loader.py`

这个文件测试 Day 3 的数据和 loader。

#### 测试 1：能加载 4 个电商 policy 文档

```python
def test_load_ecommerce_policy_documents() -> None:
```

它验证：

- 能加载 4 个文档
- 文件名包含 `faq.md`、`return_policy.md`、`logistics_policy.md`、`warranty_policy.md`
- 每个文档都有 `id`
- 每个文档都有 `content`
- metadata 里包含 `source`
- metadata 里包含 `document_type`
- metadata 里包含 `.md` 后缀

#### 测试 2：能获取 policy 文档路径

```python
def test_get_policy_doc_paths_returns_markdown_files() -> None:
```

它验证：

- 返回 4 个路径
- 每个路径都是 `.md`
- 每个路径都在默认电商 docs 目录下

#### 测试 3：loader 不是电商专用

```python
def test_load_markdown_documents_is_domain_agnostic(tmp_path: Path) -> None:
```

这个测试很重要。

它临时创建了一个 HR 文档：

```text
leave_policy.md
```

然后用同一个 `load_markdown_documents` 去加载。

如果 loader 能正确加载 HR 文档，说明它没有写死电商业务。

#### 测试 4：路径不存在时抛错

```python
def test_load_markdown_documents_rejects_missing_path(tmp_path: Path) -> None:
```

如果路径不存在，应该抛出 `FileNotFoundError`。

这比静默返回空列表更清楚。因为路径错了通常是配置问题，应该尽早暴露。

#### 测试 5：mock JSON 数据结构正确

```python
def test_ecommerce_mock_data_has_expected_shape() -> None:
```

它验证：

- orders 数量在 5 到 10 条之间
- products 至少 5 条
- 每个订单都有必要字段
- 每个订单的 `product_id` 都能在 products 中找到

这个测试保证 mock 数据不是随便写的孤立数据。

## 5. 怎么验收的

### 只跑 Day 3 测试

```powershell
python -m pytest tests/test_document_loader.py -q
```

结果：

```text
5 passed
```

### 跑 Day 1 + Day 2 + Day 3 测试

```powershell
python -m pytest tests/test_health.py tests/test_chat_contract.py tests/test_document_loader.py -q
```

结果：

```text
10 passed
```

### 跑当前全部测试

```powershell
python -m pytest -q
```

结果：

```text
10 passed
```

## 6. 遇到了什么问题

今天没有遇到阻塞性代码问题。

仍然能看到一个本机 pytest cache warning：

```text
PytestCacheWarning: could not create cache path ...
```

这和之前一样，是本地 Windows 路径/pytest cache 的问题，不影响测试结果。因为测试已经全部通过，所以没有把它当成 Day 3 代码失败处理。

## 7. 今天的设计取舍

### 结构化数据和非结构化数据分开

订单和商品放在：

```text
data/ecommerce/mock/
```

政策文档放在：

```text
data/ecommerce/docs/
```

这样后续可以自然演进：

- 订单/商品：走 SQL 或 structured tool
- 政策文档：走 RAG retrieval

### core loader 保持通用

`app/pipeline/document_loader.py` 没有任何电商规则。

它不关心：

- 退货
- 物流
- 保修
- 订单

它只负责：

- 找 markdown 文件
- 读内容
- 生成 `Document`

这符合项目约束：`app/pipeline/` 是通用 RAG pipeline，不能写死电商业务。

### domain adapter 负责电商入口

`app/domains/ecommerce/adapter.py` 知道电商文档目录在哪里。

这就是 adapter 的意义：把 domain-specific 的东西放在 domain 层，而不是污染 core pipeline。

## 8. 当前状态

当前项目已经具备：

- FastAPI app
- `/health`
- `/chat` mock API contract
- `Evidence`
- `TraceInfo`
- `ChatRequest`
- `ChatResponse`
- 电商 orders/products mock 数据
- 电商 FAQ/退货/物流/保修 policy 文档
- `Document` schema
- 通用 markdown document loader
- ecommerce adapter
- document loader 测试

当前项目还不具备：

- chunking
- embedding/mock embedding
- vector store
- retriever
- prompt builder
- evidence-grounded answer
- `/chat` 接入 RAG pipeline

这些会从 Day 4 和 Day 5 开始补。

## 9. 今日三句面试表达

- 我把电商客服数据拆成结构化 mock 数据和非结构化 policy 文档两类，为 Week 2 的 SQL + RAG 混合问答做准备。
- 订单状态这类精确事实后续适合走结构化工具，而退货、物流、保修政策更适合走文档检索。
- document loader 保持通用，不绑定电商业务规则，这样后续可以替换成 HR 或 IT support domain。
