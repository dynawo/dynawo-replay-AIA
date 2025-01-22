from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class Constraint:
    time: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
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
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
        },
    )
    kind: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    limit: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    side: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    acceptable_duration: Optional[float] = field(
        default=None,
        metadata={
            "name": "acceptableDuration",
            "type": "Attribute",
        },
    )


@dataclass
class Constraints:
    class Meta:
        name = "constraints"
        namespace = "http://www.rte-france.com/dynawo"

    constraint: list[Constraint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
