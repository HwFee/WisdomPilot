## ADDED Requirements

### Requirement: AI assistance shall be policy-controlled
The system SHALL expose AI assistance through explicit learning-context policies instead of unrestricted default access. Each AI entry point MUST declare whether it is free, core-costed, cached, admin-only, or disabled for learners.

#### Scenario: Learner requests a challenge hint
- **WHEN** a learner requests a light, medium, or deep hint for a challenge exercise
- **THEN** the system uses the configured hint policy to determine the core cost, checks the learner balance, and either streams the hint or returns an insufficient-core response

#### Scenario: Learner uses cached hint
- **WHEN** a learner requests a hint previously purchased for the same exercise and hint level
- **THEN** the system returns the cached hint without deducting additional cores

#### Scenario: General AI chat remains available
- **WHEN** a learner uses a general AI chat entry point
- **THEN** the implementation MUST either route it through the same policy service or document that it is intentionally excluded from the controlled-learning demo flow

### Requirement: AI hints shall remain pedagogically bounded
The system SHALL keep tiered hint prompts aligned with teaching support rather than direct answer disclosure. Light hints MUST guide direction, medium hints MUST provide structured steps or pseudocode, and deep hints MUST provide detailed reasoning without requiring a complete runnable answer.

#### Scenario: Light hint generation
- **WHEN** a light hint is requested for a programming exercise
- **THEN** the prompt asks for problem interpretation, data structure or algorithm direction, and boundary-case reminders without full code

#### Scenario: Medium hint generation
- **WHEN** a medium hint is requested for a programming exercise
- **THEN** the prompt may include pseudocode or skeleton structure but must not include a complete implementation

#### Scenario: Deep hint generation
- **WHEN** a deep hint is requested for a programming exercise
- **THEN** the prompt may include detailed reasoning, complexity analysis, and commented code structure while still avoiding a copy-paste final answer

### Requirement: Reflection prompts shall be optional enhancement work
The system SHALL treat post-pass AI reflection prompts as an optional enhancement module that can be enabled after the core challenge flow remains stable. Reflection prompts MUST be generated from the submitted code, exercise goal, and knowledge points, and MUST not replace deterministic judge results.

#### Scenario: Reflection disabled
- **WHEN** the reflection module is not enabled
- **THEN** a learner can complete the challenge flow using existing judge, progress, reward, and leaderboard behavior

#### Scenario: Reflection enabled after pass
- **WHEN** a learner passes all authoritative tests and reflection is enabled
- **THEN** the system can generate short follow-up questions to check whether the learner understands the experiment goal

#### Scenario: Reflection assessment recorded
- **WHEN** a learner answers reflection questions
- **THEN** the system records reflection status separately from judge correctness so code correctness and conceptual verification remain distinguishable

### Requirement: Defense positioning shall be explicit
The system SHALL document the product position as deterministic teaching workflow plus controlled GAI assistance. Documentation MUST avoid claiming that AI alone reliably generates and evaluates the full curriculum.

#### Scenario: Reviewer reads design artifacts
- **WHEN** a reviewer reads the proposal, design, or implementation plan
- **THEN** they can identify which parts are deterministic system behavior and which parts are AI-assisted enhancement behavior
