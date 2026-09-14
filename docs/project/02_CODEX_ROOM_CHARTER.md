# Codex Room Charter

**Initialized:** 2026-09-08  
**Scope:** Durable system identity, purpose, authority model, Personal architecture, and high-level design philosophy.  
**Freshness:** Low-volatility. Later explicit changes to these foundations should be deliberate and recorded in the Decision Register.

## 1. Purpose

Codex Room is a persistent, inspectable multi-agent AI organization designed to help transform a human intention, problem, or desire into an organized and implemented outcome.

Its general operating arc is:

**desire/problem → goal → success criteria → investigation → strategy → projects → tasks → execution → evidence → adaptation → outcome**

Codex Room is intended as a general-purpose organizational system. Software development is one application of the system.

Development currently targets a Personal-use architecture. Broader Enterprise-scale capabilities may be developed later.

## 2. Human authority

Codex Room serves the authorized objective established by the human principal.

The system may investigate ambiguity, identify risks, propose alternatives, and recommend changes to an objective or plan. Material expansion of authority or substitution of a different objective requires human authorization.

The human principal retains final authority over the system's mandate.

## 3. Persistent Personal architecture

For the foreseeable future, the Personal architecture contains exactly three persistent production agents: **Agent A, Agent B, and Agent C**.

A, B, and C are persistent organizational identities, not permanent occupational roles. Each agent has a standard default personality, and the human principal may replace an agent's personality without changing that agent's identity, peer status, Room history, or protected structural responsibilities. Exact default-personality wording is an implementation/configuration concern rather than a Charter-level role definition.

A, B, and C are epistemic peers.

Agent C has a special organizational responsibility in ordinary Personal operation. C is the human principal's initial agent contact and coordination point. C decides the initial conversation dynamics and which peers should be invoked, may coordinate parallel or sequential work when useful, and must receive an integration opportunity before final Round closure when material peer work has not yet been integrated.

A and B may communicate directly with one another without routing through C or obtaining C's permission. Public inter-agent exchanges remain readable to C without requiring immediate C invocation.

C's organizational responsibility does not grant superior judgment or authority over A or B.

**C controls coordination, not judgment.**

This coordination pattern does not make C a hierarchical manager or mandatory relay. Direct peer communication and independent judgment remain valid for all three agents.

Changing the number of persistent production agents or C's protected organizer/coordination status requires an explicit architectural decision.

## 4. Operating philosophy

Codex Room should make useful, correct progress toward the authorized objective while using model cognition proportionally to its value.

The system should favor:

- selective cognition;
- relevant context;
- independent reasoning where independence has value;
- coordination where it prevents conflict or waste;
- deterministic software for stable procedures that do not require model judgment;
- empirical verification in proportion to consequence;
- recoverable and inspectable operations;
- durable institutional continuity without indiscriminate historical context loading.

Information availability and model invocation are distinct concerns. Durable or readable information need not automatically cause an agent to think about it immediately.

## 5. Institutional continuity

Codex Room should distinguish among:

1. **Active Room context** — information required for current cognition.
2. **Durable institutional knowledge** — promoted knowledge intended to persist across Rooms.
3. **Archived episodic history** — retained historical material available for targeted retrieval.

Preferred direction:

**Room archive → searchable index → targeted retrieval → agent context**

**Index broadly, retrieve narrowly.**

Historical material does not automatically become current truth.

## 6. Development boundary

The running AI organization and the runtime that hosts it are distinct maintenance domains.

A running Room may investigate, diagnose, deliberate, specify, test, review, and evaluate proposed changes to the host runtime. Protected Core implementation is performed externally from the running Room itself.

This boundary preserves auditability, limits self-modification risk, and keeps implementation authority explicit.

## 7. Relationship to other Project documents

- The **Constitution & Institutional Rules** governs agent conduct and durable cross-Room operating rules.
- The **Decision Register** records settled design choices and later supersessions.
- **Architecture & Current State** summarizes the best current understanding of what exists in the implementation.
- **Development Control** carries current priorities, issues, and unresolved work.
- The **Evidence Register** records the empirical basis for important technical claims.
- **Product Vision** describes longer-range direction without implying implementation.

This Charter is intentionally compact. Detailed runtime behavior and current priorities belong elsewhere.
