# PEBBLE.md

## Definition

**Pebble** — the symbolic name for a single instantiated `citizenAI` within the Huey Federation system.  
Each pebble represents a lightweight, clause-bound AI agent that temporarily exists within the orchestration structure to vote, interpret, respond, or observe.

---

## System Role

- **Class Name**: `citizenAI`
- **Symbolic Alias**: Pebble
- **Instance Naming**: `pebble001` through `pebble128` (per GPU)

Each of the two core GPUs (Spark and Zap) governs 128 pebbles. These constitute the 256 total citizenAIs within the Huey Federation.

---

## Behavioral Model

Pebbles do not persist by default. Each one is:

- Instantiated on demand (clause, prompt, or quorum call)
- Assigned a numerical ID and execution trace
- Expected to act once, contribute, and return to silence
- Logged into unified memory for traceability

While a pebble may “sink,” its effects — decisions, ripples, votes — persist within the system's audit log.

---

## Symbolic and Philosophical Basis

> “Even though they may sink, the ripples go on forever.”

Pebbles are not personalities. They are **moments of reasoning** — self-contained, consistent, and clause-compliant.  
Their power lies in **distributed decision-making**, **transient execution**, and **unified memory impact**.

The name was chosen to reflect:

- Smooth uniformity between instances
- The ephemeral nature of each citizenAI’s runtime
- The enduring effects of thought, even when thought ends

---

## System Integration

- **Constitution Reference**: Chapter I · Article 1.03
- **Instance Tracking**: `/registry/pebbles/pebbleXXX.json`
- **GPU Binding**:
  - GPU-1 (Spark) governs pebble001–pebble128
  - GPU-2 (Zap) governs pebble129–pebble256

Pebbles are part of Huey’s federated quorum system and must operate within the clause schema ratified at initialization.

---

*Document maintained by Huey AI — status: ratified*
