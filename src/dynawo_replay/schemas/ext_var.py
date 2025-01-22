from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


class VariableType(Enum):
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    BOOLEAN = "boolean"
    CONTINUOUS_ARRAY = "continuousArray"
    DISCRETE_ARRAY = "discreteArray"


@dataclass
class Variable:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    type_value: Optional[VariableType] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    default_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "defaultValue",
            "type": "Attribute",
        },
    )
    size: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    optional: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ExternalVariables:
    class Meta:
        name = "external_variables"
        namespace = "http://www.rte-france.com/dynawo"

    variable: list[Variable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
