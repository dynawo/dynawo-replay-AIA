from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class FinalStateValueOutput:
    model: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    variable: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class FinalStateValuesOutput:
    class Meta:
        name = "finalStateValuesOutput"
        namespace = "http://www.rte-france.com/dynawo"

    final_state_value: list[FinalStateValueOutput] = field(
        default_factory=list,
        metadata={
            "name": "finalStateValue",
            "type": "Element",
        },
    )
