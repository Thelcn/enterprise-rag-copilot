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
