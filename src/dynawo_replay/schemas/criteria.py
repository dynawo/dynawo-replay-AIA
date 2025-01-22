from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class BusComponent:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    voltage_level_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "voltageLevelId",
            "type": "Attribute",
        },
    )


@dataclass
class Component:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Country:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class CriteriaParamsVoltageLevel:
    u_max_pu: Optional[float] = field(
        default=None,
        metadata={
            "name": "uMaxPu",
            "type": "Attribute",
        },
    )
    u_min_pu: Optional[float] = field(
        default=None,
        metadata={
            "name": "uMinPu",
            "type": "Attribute",
        },
    )
    u_nom_max: Optional[float] = field(
        default=None,
        metadata={
            "name": "uNomMax",
            "type": "Attribute",
        },
    )
    u_nom_min: Optional[float] = field(
        default=None,
        metadata={
            "name": "uNomMin",
            "type": "Attribute",
        },
    )


class Scope(Enum):
    FINAL = "FINAL"
    DYNAMIC = "DYNAMIC"


class Type(Enum):
    LOCAL_VALUE = "LOCAL_VALUE"
    SUM = "SUM"


@dataclass
class CriteriaParams:
    voltage_level: list[CriteriaParamsVoltageLevel] = field(
        default_factory=list,
        metadata={
            "name": "voltageLevel",
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
    scope: Optional[Scope] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
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
    p_max: Optional[float] = field(
        default=None,
        metadata={
            "name": "pMax",
            "type": "Attribute",
        },
    )
    p_min: Optional[float] = field(
        default=None,
        metadata={
            "name": "pMin",
            "type": "Attribute",
        },
    )


@dataclass
class CriteriaParamsWithVoltageLevel:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    scope: Optional[Scope] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
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
    p_max: Optional[float] = field(
        default=None,
        metadata={
            "name": "pMax",
            "type": "Attribute",
        },
    )
    p_min: Optional[float] = field(
        default=None,
        metadata={
            "name": "pMin",
            "type": "Attribute",
        },
    )
    u_max_pu: Optional[float] = field(
        default=None,
        metadata={
            "name": "uMaxPu",
            "type": "Attribute",
        },
    )
    u_min_pu: Optional[float] = field(
        default=None,
        metadata={
            "name": "uMinPu",
            "type": "Attribute",
        },
    )
    u_nom_max: Optional[float] = field(
        default=None,
        metadata={
            "name": "uNomMax",
            "type": "Attribute",
        },
    )
    u_nom_min: Optional[float] = field(
        default=None,
        metadata={
            "name": "uNomMin",
            "type": "Attribute",
        },
    )


@dataclass
class BusCriteria:
    parameters: Optional[CriteriaParamsWithVoltageLevel] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
            "required": True,
        },
    )
    component: list[BusComponent] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    country: list[Country] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )


@dataclass
class Criteria1:
    class Meta:
        name = "Criteria"

    parameters: Optional[CriteriaParams] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
            "required": True,
        },
    )
    component: list[Component] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    country: list[Country] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )


@dataclass
class Criteria:
    class Meta:
        name = "criteria"
        namespace = "http://www.rte-france.com/dynawo"

    bus_criteria: list[BusCriteria] = field(
        default_factory=list,
        metadata={
            "name": "busCriteria",
            "type": "Element",
        },
    )
    load_criteria: list[Criteria1] = field(
        default_factory=list,
        metadata={
            "name": "loadCriteria",
            "type": "Element",
        },
    )
    generator_criteria: list[Criteria1] = field(
        default_factory=list,
        metadata={
            "name": "generatorCriteria",
            "type": "Element",
        },
    )
