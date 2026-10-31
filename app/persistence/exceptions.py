"""Repository layer exception definitions for ILLUM AI STUDIO (P03-T03).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: Strict metadata boundaries and error categorization
- DEC-019: Project scoping and isolation
"""

from __future__ import annotations


class RepositoryError(Exception):
    """Base exception for all repository and persistence errors."""


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found within the authorized project scope."""


class ProjectMismatchError(RepositoryError):
    """Raised when an operation attempts cross-project access or entity-project mismatch."""


class ConstraintViolationError(RepositoryError):
    """Raised when an invariant, schema constraint, or allowlist validation fails."""
