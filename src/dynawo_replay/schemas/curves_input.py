from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class CurveInput:
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
class CurvesInput:
    class Meta:
        name = "curvesInput"
        namespace = "http://www.rte-france.com/dynawo"

    curve: list[CurveInput] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
