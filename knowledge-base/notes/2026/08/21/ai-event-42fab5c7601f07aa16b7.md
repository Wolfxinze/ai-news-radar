---
id: "ai-event-42fab5c7601f07aa16b7"
kind: "ai_event"
status: "candidate"
title: "SGLang 推出 Weight Cache Daemon，实现亚秒级引擎重启 / Blog Fast Engine Recovery： Sub-Second Engine Restart for SGLang via Weight Cache Daemon Nowadays， State-of-the-Art （SOTA） models are getting much bigger and reloading the model service after a crash is very expensive. Therefore， we are introducing the Weight Cache Daemon， a persistent GP… Ant Ling Infra Team （Ant Group）， Alibaba， SGLang Team"
canonical_url: "https://www.lmsys.org/blog/2026-08-21-sglang-fast-recovery"
published_at: "2026-08-21T17:56:25.415000Z"
confidence: "single_source"
radar_story_id: "story_a1a025194e2c"
radar_importance: 0.7512
source_generated_at: "2026-08-21T18:28:50.056307Z"
---

# SGLang 推出 Weight Cache Daemon，实现亚秒级引擎重启 / Blog Fast Engine Recovery： Sub-Second Engine Restart for SGLang via Weight Cache Daemon Nowadays， State-of-the-Art （SOTA） models are getting much bigger and reloading the model service after a crash is very expensive. Therefore， we are introducing the Weight Cache Daemon， a persistent GP… Ant Ling Infra Team （Ant Group）， Alibaba， SGLang Team

> Candidate generated from AI News Radar. The summary and recommendation below are unverified routing signals, not established facts.

## Radar summary

SGLang 团队推出 Weight Cache Daemon，通过 CUDA IPC 零拷贝映射将模型权重加载从约 495 秒降至约 0.63 秒（约 785 倍加速），端到端启动时间减少 93.9%。该守护进程在 GPU 内存中持久化后量化权重，支持多实例共享和亚秒级主备切换，是 Fast Engine Recovery Framework 的第一阶段。

## Why it may matter

Not provided. Add a verified assessment during review.

## Evidence

- [SGLang 推出 Weight Cache Daemon，实现亚秒级引擎重启 / Blog Fast Engine Recovery： Sub-Second Engine Restart for SGLang via Weight Cache Daemon Nowadays， State-of-the-Art （SOTA） models are getting much bigger and reloading the model service after a crash is very expensive. Therefore， we are introducing the Weight Cache Daemon， a persistent GP… Ant Ling Infra Team （Ant Group）， Alibaba， SGLang Team](https://www.lmsys.org/blog/2026-08-21-sglang-fast-recovery) — LMSYS：Blog（Chatbot Arena 团队）

## Review checklist

- [ ] Open and verify the primary source.
- [ ] Separate confirmed claims from commentary or projections.
- [ ] Resolve conflicts between sources.
- [ ] Add entities, products, models, and durable topic tags.
- [ ] Change `status` to `reviewed`, `published`, or `rejected`.
