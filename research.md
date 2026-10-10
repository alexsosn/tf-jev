# Initial research framing

This document records bootstrap hypotheses and open questions. It is not evidence that the proposed architecture works.

## Research question

Can a low-cost bounded-decision model such as TypeSafe Jev translate natural-language requests into native Text-Fabric search queries accurately enough to be useful, without free-form query generation?

## Working hypothesis

The problem can be decomposed into three mostly independent layers:

1. **corpus/schema understanding** — extract the symbols and value domains available in the loaded Text-Fabric corpus;
2. **semantic decoding** — map natural-language intent onto a bounded typed representation using schema-derived choices;
3. **query compilation** — deterministically render that representation into native TF search syntax and validate it.

This should make syntactic validity easier than direct LLM query generation, but semantic correctness remains an empirical question.

## Evidence required before freezing an IR

Research must inspect the current Text-Fabric search implementation/documentation and enumerate:

- atom/node syntax;
- node-feature constraints and supported comparison/value forms;
- edge features and directed/undirected edge constraints;
- spatial/structural relations;
- named sets if relevant;
- quantifiers and nested constructs;
- query variables/templates if relevant;
- parser diagnostics and ways to validate without expensive execution;
- corpus APIs for discovering node types, features, edge features and useful value domains.

The IR should cover a deliberately chosen prototype subset first. Do not claim complete TF grammar coverage without tests.

## Jev questions to verify from the current API

Before implementing a Jev client, verify:

- supported primitive output types and limits;
- maximum practical `choice` cardinality;
- whether multiple independent decisions can be evaluated efficiently in one request;
- probability/confidence semantics;
- model/version pinning;
- rate limits, timeout/retry semantics and pricing;
- data-retention/privacy behavior relevant to schema/value transmission;
- whether hierarchical choice materially improves high-cardinality decoding.

All API and pricing claims must be date/version grounded in the research ticket.

## High-cardinality value problem

Some TF feature domains are small (for example grammatical categories), while others can contain thousands of lexemes, names or IDs. A bounded-choice backend should not receive an entire large vocabulary.

Candidate approaches to research:

- exact/normalized lookup;
- prefix/fuzzy retrieval;
- lexical aliases/gloss indexes;
- corpus-specific searchable labels;
- hierarchical narrowing;
- deterministic filters before model ranking.

Candidate retrieval must be measurable independently from the model.

## Evaluation hypothesis

Exact query-string match is insufficient because multiple native TF queries may be result-equivalent. The benchmark should therefore distinguish:

- exact compiler output for a fixed IR;
- parse/IR correctness;
- TF parser validity;
- execution/result equivalence against a gold expectation;
- unsupported/ambiguous-query detection;
- cost and latency.

## Candidate first corpus

BHSA is a strong candidate for the first benchmark because it exposes rich node/feature structure and supports realistic linguistic queries. This is a research preference, not yet a hard package dependency.

## Non-goals for the first prototype

- semantic interpretation of corpus text not represented in TF annotations;
- arbitrary natural-language question answering;
- generating or modifying corpus annotations;
- replacing Text-Fabric search execution;
- supporting every TF query construct before a smaller benchmarked subset works.
