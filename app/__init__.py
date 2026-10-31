"""ILLUM AI STUDIO — Core Application Package.

Architectural boundaries defined per ADR-001:
- domain: Core domain models, enums, entities, and structural schemas.
- persistence: Database models, session management, and repositories.
- providers: AI provider adapter contracts and implementations.
- jobs: Job queue state machines, retry logic, and execution tracking.
- skills: Skills A–D pipeline orchestration and contract execution.
- research: Module E discovery connectors, ranking, and topic dossiers.
- security: Secret sanitization, masking, and boundary validation.
- use_cases: Application business workflows and approval gates.
- ui: Localhost presentation endpoints and web interface assets.
"""

__version__ = "0.1.0"
