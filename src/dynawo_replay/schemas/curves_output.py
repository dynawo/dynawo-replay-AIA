from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class Point:
    time: Optional[float] = field(
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
class CurveOutput:
    point: list[Point] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
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
class CurvesOutput:
    class Meta:
        name = "curvesOutput"
        namespace = "http://www.rte-france.com/dynawo"

    curve: list[CurveOutput] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
