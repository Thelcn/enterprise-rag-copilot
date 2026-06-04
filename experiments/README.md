# Experiments

This directory is reserved for exploration that should not enter the main
application path without review.

Examples:

- Trying a real embedding API.
- Comparing a local vector database.
- Testing alternative prompt formats.
- Measuring retrieval quality on small evaluation sets.

Week 1 production code must keep a deterministic keyword fallback so the
project can run without external embedding services. If an experiment depends
on an API key, network access, or a heavy service, keep it here and document how
it differs from the main pipeline.
