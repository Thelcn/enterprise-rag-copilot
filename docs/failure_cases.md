# RAG v0 Failure Cases

This document records known limitations of the Week 1 naive RAG pipeline. It is
not a success showcase; it is a review aid for deciding what to improve next.

## 1. Keyword Mismatch

### Example

Query:

```text
我想撤回购买，能不能处理？
```

### Current Behavior

The keyword fallback may miss the closest return policy if the query uses words
that do not overlap with policy text such as `退货` or `无理由`.

### Impact

The system can fallback even when a human would understand the query as a return
question.

### Week 2 Improvement

Add better intent routing, query rewriting, synonym handling, or real embeddings
behind the existing fallback interface.

## 2. Weak Semantic Understanding

### Example

Query:

```text
火星仓库配送政策是什么？
```

### Current Behavior

The keyword fallback may retrieve logistics policy because it matches words like
`配送` and `政策`, even though `火星仓库` is outside the supported domain.

### Impact

The system can return partially relevant evidence for out-of-scope questions.

### Week 2 Improvement

Add out-of-scope detection, metadata filters, and more explicit fallback rules
for unsupported locations or scenarios.

## 3. Template-Like Answers

### Example

Query:

```text
耳机可以退货吗？
```

### Current Behavior

The answer generator copies and summarizes retrieved evidence using a simple
rule-based template. It does not reason deeply about product category, order
date, package state, or user-specific eligibility.

### Impact

The answer can explain general policy but cannot decide whether a specific
order is eligible.

### Week 2 Improvement

Introduce structured order/product lookup, combine SQL evidence with document
evidence, and make answer generation distinguish general policy from specific
user eligibility.

## 4. Broad Chunks Can Pull Weakly Related Evidence

### Example

Query:

```text
退货政策是什么？
```

### Current Behavior

The top evidence includes `return_policy.md`, which is correct. Because the
Week 1 chunking strategy uses broad document-level chunks and keyword overlap,
we may also see weaker evidence from `faq.md` or `logistics_policy.md`.

### Impact

The answer can become longer than necessary and may include adjacent after-sales
information that is not strictly required for the user question.

### Week 2 Improvement

Tune chunk size, add metadata filters, introduce reranking, or use evaluation
cases to measure whether the top evidence is precise enough for the question.

## 5. Order Status Questions Are Routed Through Documents

### Example

Query:

```text
我的订单 ORD-1001 到哪里了？
```

### Current Behavior

Week 1 v0 only searches markdown policy documents. It has mock order data in the
repository, but the chat flow does not yet have structured ecommerce tools, so
the question cannot be answered from the right data source.

### Impact

The system may fallback or retrieve generic logistics policy even though the
user asked for a precise order-specific fact.

### Week 2 Improvement

Add an intent router and ecommerce structured tools so order-status questions
can use `structured_only` routing and cite structured evidence.

## 6. Hybrid Eligibility Questions Need Two Evidence Sources

### Example

Query:

```text
订单 ORD-1001 的耳机现在还能退货吗？
```

### Current Behavior

The question needs order facts, product information, and return-policy rules.
Week 1 v0 can retrieve general return policy, but it cannot combine that policy
with structured order state, delivery date, or product metadata.

### Impact

The answer can explain the general policy but cannot safely decide whether this
specific order is eligible.

### Week 2 Improvement

Use `hybrid` routing: query structured tools for order/product facts, retrieve
policy documents, normalize both into evidence, and fallback if either side is
missing.

## 7. Policy Evidence Can Be Empty Or Too Weak

### Example

Query:

```text
拆封后还能不能七天无理由？
```

### Current Behavior

The keyword fallback depends on lexical overlap. If the wording does not match
the policy document closely enough, the retriever may return weak evidence or no
evidence even though the question is about return policy.

### Impact

The user may receive a fallback for a supported policy question, or the system
may cite a less relevant chunk.

### Week 2 Improvement

Add intent-aware metadata filtering, evaluation cases, and a clearer fallback
reason for weak policy evidence.

## 8. Structured Tools Need Explicit IDs

### Example

Query:

```text
我的耳机多少钱？
```

### Current Behavior

Week 2 Day 2 introduces structured ecommerce tools, but product lookup still
requires a product ID such as `P-HEADPHONE-01`. The system should not guess which
product the user means from a product nickname alone.

### Impact

The system can identify that the question is about product information, but it
must fallback with `missing_product_id` unless a later slot-filling step asks the
user for the missing product ID.

### Week 2 Improvement

Keep the structured tool error explicit for now. A later fallback handler or
dialogue step can turn `missing_product_id` into a user-facing clarification.

## 9. Hybrid Routing Is Still Minimal

### Example

Query:

```text
订单 ORD-1001 的耳机现在还能退货吗？
```

### Current Behavior

Week 2 Day 2 can route this as `hybrid` and combine order structured evidence
with document evidence. However, it does not yet have a dedicated evidence
builder, product-level eligibility checks, or a full fallback policy for partial
hybrid evidence.

### Impact

The answer can show the two evidence sources, but it should still be reviewed as
a minimal hybrid prototype rather than a complete eligibility decision engine.

### Week 2 Improvement

Day 4 should normalize structured and document evidence through an evidence
builder. Day 5 should centralize fallback semantics for partial hybrid answers.

## 10. Metadata Filters Can Be Too Strict Or Too Loose

### Example

Query:

```text
耳机保修多久？
```

### Current Behavior

Week 2 Day 3 routes this as `warranty` and applies
`document_type=warranty_policy`, which correctly prioritizes
`warranty_policy.md`. If the system applied the wrong filter, retrieval might
either return an empty list or retrieve a semantically weak chunk that happens
to share Chinese characters with the query.

### Impact

Metadata filtering reduces broad mis-recall, but it does not replace ranking,
slot filling, or evaluation. A wrong or overly broad metadata rule can still
produce weak evidence.

### Week 2 Improvement

Keep metadata rules centralized in `domains/ecommerce/metadata_rules.py`, add
evaluation cases for filter misses, and use Day 4 evidence builder plus Day 5
fallback handler to make partial evidence safer.
