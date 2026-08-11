---
id: "ai-event-6e8844397e4d6f5bfc65"
kind: "ai_event"
status: "candidate"
title: "统一 Radix 缓存：为混合模型前缀缓存构建单一树结构 / Blog Unified Radix Cache： One Tree for Hybrid Model Prefix Caching Prefix caching reuses KV when requests share the same token prefix. Under full attention， once the KV for a shared prefix is computed， it remains valid as more tokens are appended. A later request wit… Zhangheng Huang， Ke Bao， Yi Zhang， Jialin Ouyang， Sicheng Pan"
canonical_url: "https://www.lmsys.org/blog/2026-08-11-unified-radix-cache"
published_at: "2026-08-11T13:51:45.827000Z"
confidence: "single_source"
radar_story_id: "story_98891a5c0ebf"
radar_importance: 0.7639
source_generated_at: "2026-08-11T15:16:59.619194Z"
---

# 统一 Radix 缓存：为混合模型前缀缓存构建单一树结构 / Blog Unified Radix Cache： One Tree for Hybrid Model Prefix Caching Prefix caching reuses KV when requests share the same token prefix. Under full attention， once the KV for a shared prefix is computed， it remains valid as more tokens are appended. A later request wit… Zhangheng Huang， Ke Bao， Yi Zhang， Jialin Ouyang， Sicheng Pan

> Candidate generated from AI News Radar. The summary and recommendation below are unverified routing signals, not established facts.

## Radar summary

LMSYS 团队提出 Unified Radix Cache，用单一 token 键控 radix 拓扑统一管理混合模型的 FULL、SWA 和 MAMBA 组件缓存，各组件独立执行路径、滑动窗口和检查点复用语义。

## Why it may matter

Not provided. Add a verified assessment during review.

## Evidence

- [统一 Radix 缓存：为混合模型前缀缓存构建单一树结构 / Blog Unified Radix Cache： One Tree for Hybrid Model Prefix Caching Prefix caching reuses KV when requests share the same token prefix. Under full attention， once the KV for a shared prefix is computed， it remains valid as more tokens are appended. A later request wit… Zhangheng Huang， Ke Bao， Yi Zhang， Jialin Ouyang， Sicheng Pan](https://www.lmsys.org/blog/2026-08-11-unified-radix-cache) — LMSYS：Blog（Chatbot Arena 团队）

## Review checklist

- [ ] Open and verify the primary source.
- [ ] Separate confirmed claims from commentary or projections.
- [ ] Resolve conflicts between sources.
- [ ] Add entities, products, models, and durable topic tags.
- [ ] Change `status` to `reviewed`, `published`, or `rejected`.
