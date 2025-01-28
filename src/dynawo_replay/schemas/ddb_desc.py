from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class Parameter:
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    value_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "valueType",
            "type": "Attribute",
        },
    )
    cardinality: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    read_only: Optional[str] = field(
        default=None,
        metadata={
            "name": "readOnly",
            "type": "Attribute",
        },
    )
    default_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "defaultValue",
            "type": "Attribute",
        },
    )


@dataclass
class Variable:
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    value_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "valueType",
            "type": "Attribute",
        },
    )


@dataclass
class Parameters:
    parameter: list[Parameter] = field(
        default_factory=list,
        metadata={
            "name": "parameter",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )


@dataclass
class Variables:
    variable: list[Variable] = field(
        default_factory=list,
        metadata={
            "name": "variable",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )


@dataclass
class Elements:
    parameters: Optional[Parameters] = field(
        default=None,
        metadata={
            "name": "parameters",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    variables: Optional[Variables] = field(
        default=None,
        metadata={
            "name": "variables",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )


@dataclass
class Model:
    class Meta:
        name = "model"
        namespace = "http://www.rte-france.com/dynawo"

    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "name",
            "type": "Element",
        },
    )
    elements: Optional[Elements] = field(
        default=None,
        metadata={
            "name": "elements",
            "type": "Element",
        },
    )
