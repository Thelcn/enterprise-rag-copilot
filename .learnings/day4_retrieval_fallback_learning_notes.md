# Day 4 学习笔记：Chunking、Keyword Fallback Index 与 Retriever

## 1. 今天完成了什么

Day 4 的目标是实现从 `Document` 到 `Chunk`，再到最小可检索索引的链路。

前一天 Day 3 我们已经能把 markdown policy 文档读成 `Document`。但一整篇文档通常太长，不适合直接检索和塞进 prompt，所以今天新增了：

- `Chunk` schema
- `split_documents`
- `KeywordEmbedder`
- `InMemoryIndex`
- `KeywordRetriever`
- retriever 测试
- `experiments/README.md`

今天的重点是：系统可以在没有真实 embedding API 的情况下，使用 deterministic keyword fallback 完成最小检索。

## 2. 新增和修改了哪些文件

### `app/schemas/document.py`

今天在原有 `Document` 基础上新增了 `Chunk`。

代码：

```python
class Chunk(BaseModel):
    id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)
```

通俗理解：

- `Document` 是一整篇原始文档
- `Chunk` 是从文档里切出来的一小段

为什么需要 chunk？

因为 RAG 通常不是把整篇文档都塞给模型，而是：

1. 把文档切成较小片段
2. 检索最相关的片段
3. 把片段作为 evidence 放进 prompt
4. 让 answer generator 基于 evidence 回答

字段含义：

- `id`：chunk 自己的 ID
- `document_id`：它来自哪篇文档
- `source`：来源文件，比如 `return_policy.md`
- `content`：chunk 文本
- `metadata`：继承文档 metadata，并补充 `chunk_index`

### `app/pipeline/chunker.py`

这个文件负责把 `Document` 切成 `Chunk`。

主函数：

```python
def split_documents(
    documents: list[Document],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
```

参数含义：

- `documents`：输入文档列表
- `chunk_size`：每个 chunk 的目标最大长度
- `overlap`：相邻 chunk 之间保留多少重叠文本

为什么要有 overlap？

如果一条重要信息刚好被切在两个 chunk 中间，没有 overlap 的话，检索时可能两个 chunk 都不完整。

overlap 可以保留一点上下文，让边界附近的信息不容易丢。

#### 切分逻辑

代码先用空行把文本分成段落：

```python
paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
```

然后尽量把多个段落合并到一个 chunk 中，只要不超过 `chunk_size`。

如果单个段落特别长，就用字符窗口切分：

```python
chunks.extend(_split_long_text(paragraph, chunk_size, overlap))
```

#### chunk id 如何保持稳定

```python
def _build_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    stable_key = f"{document_id}:{chunk_index}:{content}"
    return f"chunk_{uuid5(NAMESPACE_URL, stable_key).hex}"
```

这里用 `uuid5`，同样输入会生成同样 ID。

这样做的好处：

- 测试更稳定
- 后续索引更新更容易追踪
- 不会每次运行都出现新的随机 chunk id

### `app/pipeline/embedder.py`

这个文件实现 `KeywordEmbedder`。

注意：它不是语义 embedding 模型。

它只是 Week 1 的 deterministic keyword fallback。

核心代码：

```python
class KeywordEmbedder:
    """Deterministic keyword fallback, not a semantic embedding model."""

    def embed(self, text: str) -> KeywordVector:
        tokens = tokenize_text(text)
        if not tokens:
            return {}

        counts = Counter(tokens)
        norm = math.sqrt(sum(count * count for count in counts.values()))
        return {token: count / norm for token, count in counts.items()}
```

通俗理解：

1. 把文本拆成 token
2. 统计每个 token 出现次数
3. 做一个简单归一化
4. 得到一个关键词权重字典

例如：

```text
七天无理由退货
```

会被拆出一些中文字符和 bigram：

```text
七, 天, 无, 理, 由, 退, 货, 七天, 天无, 无理, 理由, 由退, 退货
```

为什么中文要加 bigram？

因为中文没有天然空格。如果只拆单字，`退` 和 `货` 会太弱；加上 `退货` 这个 bigram 后，查询“退货”和文档里的“退货”能更稳定匹配。

#### cosine similarity

```python
def cosine_similarity(left: KeywordVector, right: KeywordVector) -> float:
```

它用关键词权重计算两个文本的相似度。

这个 score 的含义是：

```text
query 和 chunk 在关键词 fallback 表示上的重合程度
```

它不是：

```text
真实 semantic embedding 相似度
```

这一点很重要，不能在 README 或面试里把它吹成高级向量检索效果。

### `app/pipeline/vector_store.py`

这个文件实现内存索引。

核心类：

```python
class InMemoryIndex:
```

它做三件事：

1. 保存 chunks
2. 保存每个 chunk 的 keyword vector
3. 根据 query 搜索最相关 chunks

搜索函数：

```python
def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
```

它会：

1. 把 query embed 成 keyword vector
2. 计算 query 和每个 chunk 的 cosine similarity
3. 过滤掉 score 为 0 的 chunk
4. 按 score 从高到低排序
5. 返回 top-k

排序代码：

```python
return sorted(
    results,
    key=lambda result: (-result.score, result.chunk.source, result.chunk.id),
)[:top_k]
```

这里不仅按 score 排，还加了 `source` 和 `chunk.id` 作为 tie-breaker。

为什么要这样？

因为如果两个 chunk 分数一样，排序也应该稳定。稳定排序可以让测试结果可复现。

### `app/pipeline/retriever.py`

这个文件实现 retriever。

核心类：

```python
class KeywordRetriever:
```

它支持两种创建方式：

```python
KeywordRetriever.from_documents(documents)
```

这会自动：

1. split documents
2. build index
3. 返回 retriever

也可以：

```python
KeywordRetriever.from_chunks(chunks)
```

如果你已经有 chunks，可以直接建 index。

#### retrieve 只返回 evidence

```python
def retrieve(query: str, index: InMemoryIndex, top_k: int = 3) -> list[Evidence]:
```

它返回的是：

```python
Evidence(source=..., content=..., score=...)
```

注意：retriever 不生成 answer。

这是 Day 4 的重要边界：

- retriever 负责找证据
- answer_generator 负责基于证据回答

如果 retriever 直接生成答案，pipeline 的职责就乱了。

## 3. `experiments/README.md`

今天新增了探索区说明。

它明确：

- 真实 embedding API 实验可以放在 `experiments/`
- 本地向量库对比可以放在 `experiments/`
- prompt 格式实验可以放在 `experiments/`
- 主线 Week 1 必须保留 keyword fallback

为什么需要这个文件？

因为真实 embedding 或向量库可能引入 API key、网络、重依赖或服务启动成本。

Week 1 的目标是最小闭环，不应该因为外部 embedding 服务不可用，导致主线无法运行。

## 4. 新增的测试

### `tests/test_retriever.py`

#### 测试 1：文档能被切成 chunks

```python
def test_split_documents_creates_chunks_with_metadata() -> None:
```

验证：

- chunk 数量不少于 document 数量
- chunk id 以 `chunk_` 开头
- 每个 chunk 有 `document_id`
- 每个 chunk 有内容
- metadata 里有 `chunk_index`

#### 测试 2：查询退货能命中退货政策

```python
def test_retriever_returns_return_policy_for_return_query() -> None:
```

查询：

```text
七天无理由退货
```

预期第一条 evidence 来自：

```text
return_policy.md
```

这说明 keyword fallback 至少能支持 Day 5 的退货政策 demo。

#### 测试 3：retriever 返回 evidence，不返回 answer

```python
def test_retriever_returns_evidence_not_answer() -> None:
```

这个测试很有工程意义。

它验证 retriever 输出有：

- `source`
- `content`
- `score`

但没有：

- `answer`

也就是 retriever 没有越权生成最终回答。

#### 测试 4：空 query 返回空列表

```python
def test_retriever_returns_empty_for_blank_query() -> None:
```

空 query 不应该崩溃，也不应该返回随机 evidence。

#### 测试 5：fallback 是 deterministic

```python
def test_keyword_fallback_is_deterministic() -> None:
```

同一个 query 检索两次，结果应该一致。

这对测试和调试很重要。

#### 测试 6：index 和 retriever 不绑定电商

```python
def test_index_and_loader_are_domain_agnostic() -> None:
```

这个测试用的是 HR 示例：

```text
Annual leave requires manager approval.
```

如果能检索 `manager approval`，说明 index/retriever 不是电商专用。

## 5. 怎么验收的

### 只跑 Day 4 测试

```powershell
python -m pytest tests/test_retriever.py -q
```

结果：

```text
6 passed
```

### 跑 loader + retriever 测试

```powershell
python -m pytest tests/test_document_loader.py tests/test_retriever.py -q
```

结果：

```text
11 passed
```

### 跑全部测试

```powershell
python -m pytest -q
```

结果：

```text
16 passed
```

## 6. 遇到了什么问题

今天没有遇到阻塞性问题。

开发过程中 `retriever.py` 初稿里出现过一次导入拼写错误，我在补全文件时立即修正为：

```python
from app.pipeline.chunker import split_documents
```

这类问题说明：新增 pipeline 模块时，测试和导入检查非常重要。Day 4 的 `tests/test_retriever.py` 正好覆盖了 retriever 的导入和调用路径。

本机仍然有 pytest cache warning：

```text
PytestCacheWarning: could not create cache path ...
```

这和之前一样，不影响测试结果。

## 7. 今天的设计取舍

### 不引入真实 embedding

Week 1 优先保证主线能跑。

所以今天没有接 OpenAI embedding、向量数据库或其他外部服务。

真实 embedding 可以后续放到 `experiments/` 里试，但不能让主线依赖它。

### score 只代表 fallback 关键词相似度

`score` 是 keyword vector cosine similarity。

它能帮助排序，但不能夸大成真实语义相关性。

### retriever 不生成答案

retriever 只返回 `Evidence`。

回答生成会留给 Day 5 的 `answer_generator.py`。

这样 pipeline 层次更清楚：

```text
Document -> Chunk -> Index -> Retrieve Evidence -> Build Prompt -> Generate Answer
```

Day 4 只完成到：

```text
Retrieve Evidence
```

## 8. 当前状态

当前项目已经具备：

- FastAPI app
- `/health`
- `/chat` mock contract
- ecommerce mock data
- policy markdown docs
- `Document`
- `Chunk`
- markdown document loader
- chunker
- keyword fallback embedder
- in-memory index
- retriever
- retriever tests

当前项目还不具备：

- prompt builder
- answer generator
- `/chat` 接入 RAG pipeline
- fallback reason 由检索结果驱动
- LLM/mock LLM answer generation

这些会在 Day 5 完成。

## 9. 今日三句面试表达

- 我实现了从文档加载、切分到最小检索的 RAG 数据链路。
- 我保留 keyword fallback，避免系统因为外部 embedding 服务不可用而完全无法演示。
- 第一版 retrieval 追求可运行和可测试，不虚构高级向量检索质量。
