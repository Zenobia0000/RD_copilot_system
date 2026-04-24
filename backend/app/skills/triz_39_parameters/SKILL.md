---
name: triz_39_parameters
description: TRIZ 39 engineering parameters for TC formulation and matrix lookup
type: knowledge
when_to_use: When agent needs parameter definitions for Technical Contradiction formulation
cache_policy: static
tags: [triz, parameters, tc]
---

Reference: rd_assistant_design_system/triz_knowledge_base/01_39_parameters.md

This skill provides the complete TRIZ 39 engineering parameters used for:
- Mapping natural language contradictions to parameter pairs (improving/worsening)
- Validating parameter IDs (1-39) during contradiction formalization
- Providing parameter names and descriptions for prompt context

The 39 parameters are loaded dynamically via `load_39_parameters()` from the
knowledge base. This skill metadata enables the prompt_assembler to inject
parameter context with proper cache separation.
