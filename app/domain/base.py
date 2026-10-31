"""Base domain model abstraction for ILLUM AI STUDIO (P03-T01).

Provides seamless Pydantic v2 integration when available, with a standard-library
fallback ensuring domain validation runs consistently in minimal Python environments.
"""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

try:
    from pydantic import BaseModel as _PydanticBaseModel
    from pydantic import ConfigDict, Field

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    _PydanticBaseModel = object  # type: ignore[misc,assignment]

    def Field(*args: Any, default: Any = ..., default_factory: Any = None, **kwargs: Any) -> Any:  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        if default is not ...:
            return default
        return None

    ConfigDict = None  # type: ignore[assignment,misc]


class DomainBaseModel(_PydanticBaseModel):
    """Base domain model with strict validation and serializability."""

    if HAS_PYDANTIC:
        model_config = ConfigDict(
            extra="forbid",
            validate_assignment=True,
            arbitrary_types_allowed=True,
        )

    def __init__(self, **data: Any) -> None:
        if HAS_PYDANTIC:
            super().__init__(**data)
        else:
            cls = self.__class__
            annotations = getattr(cls, "__annotations__", {})
            for key, val in data.items():
                if key not in annotations and not hasattr(cls, key):
                    raise ValueError(f"Extra field not permitted: {key}")
                setattr(self, key, val)

            # Apply defaults for missing fields
            for key in annotations:
                if key not in data:
                    if hasattr(cls, key):
                        default_val = getattr(cls, key)
                        if callable(default_val):
                            setattr(self, key, default_val())
                        else:
                            setattr(self, key, default_val)
                    else:
                        raise ValueError(f"Missing required field: {key}")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize entity to dictionary."""
        if HAS_PYDANTIC:
            return super().model_dump(**kwargs)  # type: ignore[misc]

        res: dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if isinstance(v, DomainBaseModel):
                res[k] = v.model_dump(**kwargs)
            elif isinstance(v, (list, tuple)):
                res[k] = [
                    item.model_dump(**kwargs) if isinstance(item, DomainBaseModel)
                    else str(item) if isinstance(item, UUID)
                    else item.isoformat() if isinstance(item, (datetime.datetime, datetime.date))
                    else item
                    for item in v
                ]
            elif isinstance(v, UUID):
                res[k] = str(v)
            elif isinstance(v, (datetime.datetime, datetime.date)):
                res[k] = v.isoformat()
            elif hasattr(v, "value"):  # Enum
                res[k] = v.value
            else:
                res[k] = v
        return res

    def to_dict(self) -> dict[str, Any]:
        """Convenience alias for model_dump."""
        return self.model_dump()
