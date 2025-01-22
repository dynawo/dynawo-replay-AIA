from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class FinalStateValueInput:
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


@dataclass
class FinalStateValuesInput:
    class Meta:
        name = "finalStateValuesInput"
        namespace = "http://www.rte-france.com/dynawo"

    final_state_value: list[FinalStateValueInput] = field(
        default_factory=list,
        metadata={
            "name": "finalStateValue",
            "type": "Element",
        },
    )
