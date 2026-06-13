# Week2 Day 3 学习笔记：Policy Docs 与 Metadata Filtering

## 1. 今天完成了什么

Week2 Day3 的目标是：让文档检索不只依赖关键词相似度，还能利用文档类型、政策版本、适用场景等 metadata 约束检索范围。

今天完成了：

- 新增 `app/domains/ecommerce/metadata_rules.py`
- 扩充四份电商政策文档
- 修改 `document_loader.py`，支持外部 metadata provider
- 保持 `chunker.py` 继承文档 metadata
- 修改 `vector_store.py`，支持 metadata filter
- 修改 `retriever.py`，支持 `metadata_filter`
- 修改 `rag_pipeline.py`，让文档检索可以接收 metadata filter
- 修改 `/chat`，根据 intent 使用电商 metadata filter
- 修改 `Evidence` schema，让 evidence 能带 metadata
- 新增 `scripts/build_index.py`
- 新增 `tests/test_metadata_rules.py`
- 新增 `tests/test_metadata_filtering.py`
- 更新 README、API 文档和 failure cases
- 记录一次测试假设错误到 `.learnings/ERRORS.md`
- 新增本学习笔记

## 2. 为什么需要 Metadata Filtering

Week1/Week2 Day2 的文档检索主要靠 keyword score。

例如用户问：

```text
耳机保修多久？
```

如果只靠关键词，系统可能因为一些共享词误召回 FAQ、退货政策或物流政策。

但人类知道这个问题属于：

```text
document_type = warranty_policy
```

所以 Day3 加入 metadata filtering：

```text
query = "耳机保修多久？"
intent = warranty
metadata_filter = {"document_type": "warranty_policy"}
```

这样 retriever 会优先只在保修政策文档里检索。

这一步的意义是：检索不再只看“文本像不像”，还看“文档类型对不对”。

## 3. 新增的核心文件

### `app/domains/ecommerce/metadata_rules.py`

这个文件集中保存电商领域的 metadata 规则。

比如：

```python
ECOMMERCE_DOCUMENT_METADATA = {
    "return_policy.md": {
        "domain": "ecommerce",
        "document_type": "return_policy",
        "product_category": "all",
        "policy_version": "ecommerce-policy-2026-06",
        "applicable_scenario": "return_request",
    },
}
```

它还定义 intent 到 metadata filter 的映射：

```python
INTENT_METADATA_FILTERS = {
    "return_policy": {"document_type": "return_policy"},
    "hybrid": {"document_type": "return_policy"},
    "logistics": {"document_type": "logistics_policy"},
    "warranty": {"document_type": "warranty_policy"},
}
```

重点：这些规则放在 `domains/ecommerce/`，不是放在 `pipeline/retriever.py`。

这样以后如果换成 HR 或 IT support，只需要换 domain metadata rules，不需要重写通用 retriever。

### `scripts/build_index.py`

这个脚本用于做最小 index 构建验证。

运行：

```powershell
python scripts\build_index.py
```

输出：

```text
documents=4 chunks=8
document_types=faq,logistics_policy,return_policy,warranty_policy
```

它的作用是确认：

- 文档能加载
- chunk 能生成
- index 能构建
- metadata 里的 document_type 能被看到

## 4. 修改了哪些核心代码

### `document_loader.py`

以前 loader 自己生成基础 metadata：

```text
source
path
document_type
file_extension
```

现在它多了一个可选参数：

```python
metadata_provider: MetadataProvider | None = None
```

通俗理解：

```text
document_loader 负责通用 markdown 加载
metadata_provider 负责提供具体 domain 的额外 metadata
```

电商 adapter 里这样调用：

```python
load_markdown_documents(data_dir, metadata_provider=metadata_for_policy_document)
```

这就是“机制和策略分离”。

### `chunker.py`

chunker 本来已经会把 `document.metadata` 复制到 `chunk.metadata`。

Day3 确认并用测试锁住这个行为：

```python
chunk_metadata = {
    **document.metadata,
    "document_id": document.id,
    "chunk_index": index,
}
```

这意味着每个 chunk 都知道：

```text
它来自哪个文档
它是第几个 chunk
它是什么 document_type
它是什么 policy_version
它适用什么 scenario
```

### `vector_store.py`

`InMemoryIndex.search()` 现在支持：

```python
metadata_filter={"document_type": "warranty_policy"}
```

它的行为是：

```text
遍历 chunk
先检查 metadata 是否匹配
匹配后才计算 keyword score
```

注意：这里没有写任何“退货”“保修”“物流”的业务规则。它只是通用地比较 key/value。

### `retriever.py`

`KeywordRetriever.retrieve()` 现在支持：

```python
retrieve(
    query="耳机保修多久？",
    top_k=3,
    metadata_filter={"document_type": "warranty_policy"},
)
```

还支持：

```python
allow_filter_fallback=True
```

意思是：

- 先按 metadata filter 检索。
- 如果过滤后完全没有结果，可以放宽成不带 filter 的检索。

这解决 Day3 Review Gate 里的要求：

```text
metadata_filter 不应导致无结果时直接崩溃；应该允许 fallback 或放宽检索。
```

### `Evidence`

`Evidence` 新增了：

```python
metadata: dict[str, MetadataValue] = Field(default_factory=dict)
```

所以 `/chat` 返回的 document evidence 现在能看到：

```json
{
  "document_type": "warranty_policy",
  "policy_version": "ecommerce-policy-2026-06",
  "applicable_scenario": "warranty_repair"
}
```

这为 Day4 的 evidence builder 做准备。

## 5. `/chat` 现在怎么用 metadata filter

流程是：

```text
/chat
-> intent_router.route(query)
-> get_ecommerce_metadata_filter(intent)
-> rag_pipeline.run_chat(..., metadata_filter=...)
-> retriever.retrieve(..., metadata_filter=...)
```

例如：

```text
耳机保修多久？
```

router 判断：

```text
intent = warranty
route = document_only
```

metadata filter：

```json
{
  "document_type": "warranty_policy"
}
```

最终 evidence 来自：

```text
warranty_policy.md
```

## 6. 扩充了哪些文档

四份文档都加了“政策元数据”和“示例问题”：

- `data/ecommerce/docs/return_policy.md`
- `data/ecommerce/docs/logistics_policy.md`
- `data/ecommerce/docs/warranty_policy.md`
- `data/ecommerce/docs/faq.md`

例如保修文档现在明确写了：

```text
政策版本：ecommerce-policy-2026-06
文档类型：warranty_policy
适用场景：warranty_repair
适用品类：electronics
```

这样文档不只是散文式 FAQ，而是有工程化 metadata 语义。

## 7. 新增了哪些测试

### `tests/test_metadata_rules.py`

测试：

- 每个电商 policy doc 能映射到正确 document_type。
- metadata 有 policy_version、product_category、applicable_scenario。
- intent 能映射到正确 metadata_filter。
- 加载后的文档没有缺少必需 metadata。

### `tests/test_metadata_filtering.py`

测试：

- chunk 继承 document metadata。
- 退货问题用 `document_type=return_policy` 过滤后不会召回 warranty。
- 保修问题用 `document_type=warranty_policy` 过滤后不会召回 logistics。
- 不存在的 document_type 不会让检索崩溃。
- 过滤无结果时可以放宽检索。
- `/chat` 的保修问题返回 warranty metadata。

## 8. 今天遇到的问题

一开始有两个测试失败。

我原本写了一个假设：

```text
保修问题 + return_policy filter 应该返回空
```

但实际不是这样。原因是 keyword fallback 会把中文切成单字和双字 token。

所以：

```text
耳机保修多久？
```

和退货文档里的某些单字也可能有重合，导致 return_policy 过滤下仍然有弱命中。

修正方式：

- 不再用“错误但存在的 document_type”测试空结果。
- 改用不存在的 document_type：

```python
metadata_filter={"document_type": "nonexistent_policy"}
```

这个问题已经记录到：

```text
.learnings/ERRORS.md
```

## 9. 今天的验收结果

### Day3 指定测试

命令：

```powershell
python -m pytest tests\test_metadata_rules.py tests\test_metadata_filtering.py -q
```

结果：

```text
11 passed
```

### 构建 index

命令：

```powershell
python scripts\build_index.py
```

结果：

```text
documents=4 chunks=8
document_types=faq,logistics_policy,return_policy,warranty_policy
```

### 全量测试

命令：

```powershell
python -m pytest -q
```

结果：

```text
55 passed
```

### 手动保修问题

请求：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day3","query":"耳机保修多久？"}'
```

观察到：

```text
intent=warranty
route=document_only
evidence[0].source=warranty_policy.md
evidence[0].metadata.document_type=warranty_policy
```

### 手动退货问题

请求：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"demo_user_001","session_id":"manual-day3","query":"退货需要满足什么条件？"}'
```

观察到：

```text
intent=return_policy
route=document_only
evidence[0].source=return_policy.md
evidence[0].metadata.document_type=return_policy
```

## 10. 当前仍然存在的限制

### answer 仍然比较粗糙

现在 answer generator 仍然是 Week1 的简单模板，所以它可能把文档里的“政策元数据”也拼进回答。

这不影响 Day3 metadata filtering 的目标，但 Day4 做 evidence builder 和 prompt/answer 约束时应该继续优化。

### metadata filtering 不是语义理解

metadata filter 能缩小检索范围，但不能保证 answer 一定完美。

它解决的是：

```text
在哪类文档里找
```

不是完整解决：

```text
怎么理解用户意图
怎么判断答案是否充分
怎么处理多文档冲突
```

这些会继续交给后面的 evidence builder、fallback handler 和 evaluation。

## 11. 复习重点

你复习 Day3 时，重点理解这几句话：

- metadata filtering 是“检索范围约束”，不是替代向量检索或语义理解。
- domain rules 放在 `domains/ecommerce/metadata_rules.py`，通用 retriever 不写业务规则。
- loader 通过 metadata provider 接收 domain metadata，这是机制与策略分离。
- chunk 继承 document metadata，才能在检索结果里知道证据来源类型。
- 过滤过严可能没有结果，所以要有 fallback 或放宽检索策略。

## 12. 今日三句面试表达

- Metadata filtering 让检索不只依赖语义相似度，还能利用文档类型、产品类别和政策版本进行约束。
- 我把 metadata rules 放在 ecommerce domain adapter 中，避免 core retriever 写死业务场景。
- 这一步提升了系统可迁移性，因为换成 HR/IT domain 时只需要替换 metadata rules，而不是重写 retriever。
