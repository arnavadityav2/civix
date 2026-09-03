# AGENT INSTRUCTIONS FOR CIVIX 2.0

**STOP. READ THIS ENTIRE FILE BEFORE EXECUTING ANY TASK IN THIS REPOSITORY.**

This repository has a highly specific governance model. To prevent planning drift and hallucinations, you MUST obey the following rules:

## 1. Primary Source of Truth
`docs/00_CIVIX_CURRENT_STATE.md` is the FIRST project-state document you must read. It contains the officially verified, canonical status of all project phases and capabilities.

## 2. Ignore Transient Context
You MUST ignore all historical or transient material found in:
* `brain/` directory
* `docs/archive/transient_plans/`
* Any generated planning scratchpad

These files **cannot** establish requirements, phase scope, dependencies, or completion status. They are preserved for historical audit purposes only.

## 3. ADR Rule
An ADR (Architecture Decision Record) authorizes an architectural decision or technology choice. **An ADR DOES NOT prove implementation.** Do not assume a phase is complete simply because a framework was approved.

## 4. Requirement Verification
You must consult the Domain Bibles (e.g., `03_DATABASE_SCHEMA_BIBLE.md`, `15_API_BACKEND_BIBLE.md`) before declaring ANY capability complete.

## 5. Implementation Reality
Production code, tests, and live acceptance scripts determine the actual implementation reality. A plan claiming something is done holds no weight against the absence of code.

## 6. Conflict Resolution
If you discover conflicts between authoritative sources (e.g., Code contradicts a Bible), **DO NOT GUESS**. Escalate the contradiction to the human for a decision.

## 7. No Invention
You must NOT invent new phases or implementation steps. If you believe a step is missing, ask the human to authorize modifying the `19_IMPLEMENTATION_MASTER_PLAN.md`.

## 8. No Unsanctioned Execution
Do not treat historical planning artifacts as active instructions for your current session.

**Failure to follow these rules will result in context contamination and project drift.**
