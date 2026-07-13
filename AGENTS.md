# ProjectBlur Agent Instructions

## Project Goal

ProjectBlur is intended to anonymize faces for privacy and PDPA-conscious
processing of images, recorded videos, CCTV streams, and real-time live video.
The intended policy is whitelist-based: registered or authorized faces remain
visible, while unregistered or unauthorized faces are anonymized with methods
such as pixelation or Gaussian blur.

Only the RetinaFace detection adapter is currently implemented. Do not describe
the complete anonymization pipeline as production-ready.

## Required Reading Before Changes

Before changing code or documentation, read:

1. `README.md`
2. `PROJECT_CONTEXT.md`
3. `ARCHITECTURE.md`
4. `CODING_RULES.md`
5. `TASKS.md`
6. `docs/DECISIONS.md` and `docs/EXPERIMENTS.md` when changing architecture or
   technology
7. Documentation relevant to the module
8. Relevant source code and tests

## Working Rules

- Inspect the existing structure before creating files or modules.
- Do not duplicate modules or modify unrelated files.
- Preserve backward compatibility and the current architecture unless a change
  has a clear, documented reason.
- Make the smallest change that fully solves the task.
- Read existing tests before changing implementation behavior.
- Never claim third-party code as ProjectBlur code.
- Do not copy an external repository into `src` or vendor it wholesale.
- Integrate external dependencies through ProjectBlur-owned adapters.
- Check upstream licenses and attribution before redistributing external code.

## Research-Driven Architecture Changes

ProjectBlur is not permanently tied to its current architecture, models,
libraries, or processing flow. A significant change is allowed when supported
by credible research, a reproducible benchmark, an implementation problem, a
measured performance or accuracy constraint, a privacy/security concern,
maintainability, target-hardware compatibility, or license/dependency risk.

Before a significant architecture or flow change:

1. Describe the current problem and proposed approach.
2. Cite supporting research or reproducible evidence.
3. Compare benefits, trade-offs, and affected modules.
4. Document migration and rollback plans.
5. Add or update tests.
6. Create a new decision record; preserve and supersede the old record.
7. Update architecture, context, task, development, experiment, milestone, and
   presentation records where their facts changed.

Do not adopt a tool merely because it is new or popular. Use these statuses
consistently: `Current`, `Planned`, `Under evaluation`, `Deprecated`, and
`Rejected`. Never describe planned work as implemented.

## Development Records

After significant work, decide which factual records need updates:

- `TASKS.md` when task status changes
- `docs/DEVELOPMENT_LOG.md` for significant implementation or fixes
- `docs/DECISIONS.md` for architecture or technology choices
- `docs/EXPERIMENTS.md` for experiments and benchmarks
- `docs/MILESTONES.md` for milestone progress
- `docs/PRESENTATION_NOTES.md` for evidence-backed presentation material
- `PROJECT_CONTEXT.md` or `ARCHITECTURE.md` when context or flow changes
- `docs/RESEARCH.md` when adding research or external sources

Do not add generic or duplicate entries. Preserve old records; correct a
factual error only with a recorded correction. Presentation claims must trace
to code, tests, experiments, research, decisions, diagrams, or demo artifacts.

## Coding Rules Summary

- Use type hints and docstrings for public classes and functions.
- Use the module logging system; do not use `print()` in library code.
- Never use machine-specific absolute paths.
- Put variable settings in configuration or environment variables once a
  configuration system is implemented.
- Validate inputs and report missing dependencies clearly.
- Do not suppress exceptions without a documented, safe reason.
- Do not add frameworks or dependencies unless the task requires them.

See `CODING_RULES.md` for the complete rules.

## Testing Requirements

- Run relevant unit tests and the full suite when the change warrants it.
- Run only formatter, linter, and type-checking tools already configured by the
  repository. None are configured at present.
- Do not add validation tools solely to validate a change.
- At minimum, validate Python syntax with:

  ```bash
  python -m compileall src examples tests
  ```

- See `docs/TESTING.md` for working commands.

## Privacy and Security

Never commit personal face images, biometric embeddings, whitelist identity
data, raw CCTV footage, secrets, API keys, passwords, `.env`, large generated
outputs, or private model files without redistribution rights. Tests must use
synthetic, public-domain, or explicitly authorized assets.

## Completion Report

Every completed task report must cover:

1. Files created
2. Files modified
3. Implementation decisions
4. Commands executed
5. Test results
6. Remaining limitations
7. Manual verification required
8. Documentation records updated or intentionally unchanged
9. Proposed commit grouping when commits were not requested
