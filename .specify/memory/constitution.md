<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (initial ratification)
Modified principles: N/A (initial creation)
Added sections:
  - Core Principles (7 principles)
  - Quality Standards
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check section compatible)
  - .specify/templates/spec-template.md ✅ (Requirements section compatible)
  - .specify/templates/tasks-template.md ✅ (Phase structure compatible)
Follow-up TODOs: None
-->

# pako-tts-engines Constitution

## Core Principles

### I. Design for Clarity

All code MUST be immediately understandable without requiring external documentation.

- Prefer explicit over implicit behavior
- Names MUST convey intent (variables, functions, modules)
- Avoid abbreviations unless universally understood in the domain
- If code requires a comment to explain *what* it does, refactor until it doesn't
- Comments are reserved for explaining *why* a decision was made

**Rationale**: Clarity reduces onboarding time, minimizes bugs from misunderstanding, and enables
confident refactoring.

### II. Test for Safety

Tests MUST exist for all behavior that could break user functionality.

- Write tests before or alongside implementation (never after)
- Tests MUST fail before implementation passes them
- Contract tests for external interfaces; integration tests for user journeys
- Unit tests for complex logic; skip trivial getters/setters
- Test coverage is a signal, not a target—prioritize meaningful coverage

**Rationale**: Tests are the safety net that enables fearless iteration and refactoring.

### III. Prefer Clarity Over Cleverness

When choosing between a clever solution and a straightforward one, MUST choose straightforward.

- Avoid one-liners that sacrifice readability for brevity
- Eschew "magic" patterns that hide behavior
- Performance optimizations MUST be justified by measured need, not speculation
- Code that is hard to understand is hard to maintain

**Rationale**: Clever code impresses once; clear code serves forever.

### IV. Keep Iterations Small

Changes MUST be delivered in the smallest increments that provide value.

- Each commit SHOULD represent a single logical change
- PRs MUST be reviewable in under 30 minutes (roughly <400 lines changed)
- Break large features into independently deliverable slices
- Avoid "big bang" releases—prefer continuous small improvements

**Rationale**: Small iterations reduce risk, enable faster feedback, and make debugging easier.

### V. Avoid Designing for Unknown Future Requirements

Build for today's requirements. Do NOT add abstractions for hypothetical futures.

- YAGNI (You Aren't Gonna Need It) is mandatory
- Remove unused code paths immediately
- Abstractions MUST be justified by current use, not future speculation
- When requirements change, refactor—don't pre-engineer flexibility

**Rationale**: Speculative design creates maintenance burden without delivering value.

### VI. Reuse Before Create

Before writing new code, MUST search for existing solutions.

- Check standard library first, then existing project code, then external packages
- Document why existing solutions don't fit if creating new code
- Prefer composition of existing components over novel implementations
- Consolidate duplicate logic when discovered

**Rationale**: Reuse reduces bugs, improves consistency, and leverages battle-tested solutions.

### VII. Evolve for Growth

Architecture MUST support incremental evolution without rewrites.

- Modules MUST have clear boundaries and minimal coupling
- Interfaces SHOULD be designed for extension without modification
- Breaking changes MUST be versioned and documented
- Technical debt MUST be tracked and addressed incrementally

**Rationale**: Sustainable growth requires architecture that bends rather than breaks.

## Quality Standards

Performance, reliability, and user experience are non-negotiable quality attributes.

### Performance Requirements

- Response time targets MUST be defined before implementation
- Performance-critical paths MUST have benchmarks
- Regressions MUST block merges
- Measure before optimizing; optimize the measured bottleneck

### User Experience Consistency

- UI/UX patterns MUST be consistent across the application
- Error messages MUST be actionable and user-friendly
- Accessibility standards (WCAG 2.1 AA minimum) MUST be met for user-facing features
- Loading states and feedback MUST be provided for all async operations

### Code Quality Gates

- All code MUST pass linting (ruff) without warnings
- All code MUST pass type checking (mypy --strict)
- All tests MUST pass before merge
- Code review MUST be completed by at least one other contributor

## Development Workflow

### Change Process

1. **Specify**: Define requirements and acceptance criteria before coding
2. **Plan**: Break work into small, reviewable increments
3. **Implement**: Write code with tests, following constitution principles
4. **Review**: All changes require peer review against quality gates
5. **Validate**: Verify against acceptance criteria before merge

### Version Control

- Main branch MUST always be deployable
- Feature branches MUST be short-lived (prefer <3 days)
- Commits MUST have descriptive messages following conventional commits
- Force pushes to main are PROHIBITED

### Documentation

- API contracts MUST be documented before implementation
- README MUST be kept current with setup and usage instructions
- Architecture decisions MUST be recorded when deviating from defaults
- Documentation is code—apply the same quality standards

## Governance

This constitution supersedes all other development practices for the pako-tts-engines project.

### Amendment Process

1. Propose amendment with rationale in writing
2. Review period of at least 48 hours for team discussion
3. Amendments require consensus or documented decision
4. Update constitution version following semantic versioning
5. Propagate changes to dependent templates and documentation

### Compliance

- All pull requests MUST be reviewed for constitution compliance
- Violations MUST be addressed before merge
- Exceptions MUST be documented in the Complexity Tracking section of the plan
- Repeated violations warrant process review

### Versioning Policy

- MAJOR: Removing or fundamentally redefining principles
- MINOR: Adding new principles or substantially expanding guidance
- PATCH: Clarifications, typo fixes, non-semantic changes

**Version**: 1.0.0 | **Ratified**: 2025-12-21 | **Last Amended**: 2025-12-21
