from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class MacroParSet:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


class OriginData(Enum):
    IIDM = "IIDM"
    PAR = "PAR"


@dataclass
class ParameterInTable:
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    row: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    column: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


class Type(Enum):
    DOUBLE = "DOUBLE"
    INT = "INT"
    BOOL = "BOOL"
    STRING = "STRING"


@dataclass
class Parameter:
    type_value: Optional[Type] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Reference:
    type_value: Optional[Type] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    orig_data: Optional[OriginData] = field(
        default=None,
        metadata={
            "name": "origData",
            "type": "Attribute",
            "required": True,
        },
    )
    orig_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "origName",
            "type": "Attribute",
            "required": True,
        },
    )
    component_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "componentId",
            "type": "Attribute",
        },
    )
    par_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "parId",
            "type": "Attribute",
        },
    )
    par_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "parFile",
            "type": "Attribute",
        },
    )


@dataclass
class TableParameter:
    par: list[ParameterInTable] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
            "min_occurs": 1,
        },
    )
    type_value: Optional[Type] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class MacroParameterSet:
    reference: list[Reference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    par: list[Parameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Set:
    par_table: list[TableParameter] = field(
        default_factory=list,
        metadata={
            "name": "parTable",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    par: list[Parameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    reference: list[Reference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_par_set: list[MacroParSet] = field(
        default_factory=list,
        metadata={
            "name": "macroParSet",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ParametersSet:
    class Meta:
        name = "parametersSet"
        namespace = "http://www.rte-france.com/dynawo"

    set: list[Set] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    macro_parameter_set: list[MacroParameterSet] = field(
        default_factory=list,
        metadata={
            "name": "macroParameterSet",
            "type": "Element",
        },
    )
