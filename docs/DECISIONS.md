# ProjectBlur Decision Records

Create a new record when a decision changes. Mark the old record `Superseded`
and link the replacement; never delete historical rationale.

## DEC-001 — Isolate external detectors behind adapters

- Date: 2026-07-13
- Status: Accepted
- Related modules: `src/projectblur/detection`
- Related research: `research/external_repositories/retinaface.md`
- Related experiment: `EXP-001`

### Context

ProjectBlur needs to evaluate third-party face detectors without mixing their
source code or result formats into business logic.

### Options Considered

1. Copy detector repository source into ProjectBlur.
2. Call each detector directly throughout the application.
3. Use published packages through ProjectBlur-owned adapters.

### Decision

Use published external packages behind adapters in the detection module.

### Rationale

Adapters preserve attribution, limit coupling, normalize outputs, and allow a
detector to be replaced after evidence-based evaluation.

### Consequences

#### Positive

- External code remains separate and replaceable.
- Validation and error behavior can be tested without model inference.

#### Negative

- Each detector needs maintained mapping and compatibility tests.
- Package behavior and model assets still require integration validation.

### Validation Criteria

- Unit tests cover input and result normalization without network access.
- A real-model integration test confirms compatibility with a pinned version.
- A detector replacement does not require business-logic changes.

### Superseded By

None.

## Decisions Awaiting Evidence

Primary detector, tracker, embedding model, frame transport, detection interval,
anonymization technique, whitelist threshold, web stack, codec fallback, and
virtual-camera implementation remain `Proposed` only when a complete decision
record is added with evidence. They are not accepted decisions today.
