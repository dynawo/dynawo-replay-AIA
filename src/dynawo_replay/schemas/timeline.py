from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class Event:
    time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "modelName",
            "type": "Attribute",
            "required": True,
        },
    )
    message: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    priority: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Timeline:
    class Meta:
        name = "timeline"
        namespace = "http://www.rte-france.com/dynawo"

    event: list[Event] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
