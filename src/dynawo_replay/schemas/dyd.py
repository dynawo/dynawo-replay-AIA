from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class Connect:
    id1: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    var1: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    id2: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    var2: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Identifiable:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class IdentifiableModel:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r"[a-zA-Z0-9_.]+",
        },
    )


@dataclass
class MacroConnect:
    connector: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    id1: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    id2: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    index1: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    index2: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    name1: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    name2: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MacroConnection:
    var1: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    var2: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class MacroStaticRef:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class StaticRef:
    var: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    static_var: Optional[str] = field(
        default=None,
        metadata={
            "name": "staticVar",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class UnitDynamicModel:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r"[a-zA-Z0-9_.]+",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    mo_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "moFile",
            "type": "Attribute",
        },
    )
    init_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "initName",
            "type": "Attribute",
        },
    )
    init_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "initFile",
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
    par_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "parId",
            "type": "Attribute",
        },
    )


@dataclass
class BlackBoxModel(Identifiable):
    static_ref: list[StaticRef] = field(
        default_factory=list,
        metadata={
            "name": "staticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_static_ref: list[MacroStaticRef] = field(
        default_factory=list,
        metadata={
            "name": "macroStaticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    static_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "staticId",
            "type": "Attribute",
        },
    )
    lib: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    par_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "parFile",
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


@dataclass
class MacroConnector:
    connect: list[MacroConnection] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    init_connect: list[MacroConnection] = field(
        default_factory=list,
        metadata={
            "name": "initConnect",
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
    index1: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    index2: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    name2: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MacroStaticReference:
    static_ref: list[StaticRef] = field(
        default_factory=list,
        metadata={
            "name": "staticRef",
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
class ModelTemplate(IdentifiableModel):
    unit_dynamic_model: list[UnitDynamicModel] = field(
        default_factory=list,
        metadata={
            "name": "unitDynamicModel",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    connect: list[Connect] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    init_connect: list[Connect] = field(
        default_factory=list,
        metadata={
            "name": "initConnect",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_connect: list[MacroConnect] = field(
        default_factory=list,
        metadata={
            "name": "macroConnect",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    static_ref: list[StaticRef] = field(
        default_factory=list,
        metadata={
            "name": "staticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_static_ref: list[MacroStaticRef] = field(
        default_factory=list,
        metadata={
            "name": "macroStaticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    use_aliasing: Optional[bool] = field(
        default=None,
        metadata={
            "name": "useAliasing",
            "type": "Attribute",
        },
    )
    generate_calculated_variables: Optional[bool] = field(
        default=None,
        metadata={
            "name": "generateCalculatedVariables",
            "type": "Attribute",
        },
    )


@dataclass
class ModelTemplateExpansion(IdentifiableModel):
    static_ref: list[StaticRef] = field(
        default_factory=list,
        metadata={
            "name": "staticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_static_ref: list[MacroStaticRef] = field(
        default_factory=list,
        metadata={
            "name": "macroStaticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    static_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "staticId",
            "type": "Attribute",
        },
    )
    template_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "templateId",
            "type": "Attribute",
            "required": True,
            "pattern": r"[a-zA-Z0-9_.]+",
        },
    )
    par_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "parFile",
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


@dataclass
class ModelicaModel(IdentifiableModel):
    unit_dynamic_model: list[UnitDynamicModel] = field(
        default_factory=list,
        metadata={
            "name": "unitDynamicModel",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    connect: list[Connect] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    init_connect: list[Connect] = field(
        default_factory=list,
        metadata={
            "name": "initConnect",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_connect: list[MacroConnect] = field(
        default_factory=list,
        metadata={
            "name": "macroConnect",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    static_ref: list[StaticRef] = field(
        default_factory=list,
        metadata={
            "name": "staticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    macro_static_ref: list[MacroStaticRef] = field(
        default_factory=list,
        metadata={
            "name": "macroStaticRef",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    static_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "staticId",
            "type": "Attribute",
        },
    )
    use_aliasing: Optional[bool] = field(
        default=None,
        metadata={
            "name": "useAliasing",
            "type": "Attribute",
        },
    )
    generate_calculated_variables: Optional[bool] = field(
        default=None,
        metadata={
            "name": "generateCalculatedVariables",
            "type": "Attribute",
        },
    )


@dataclass
class DynamicModelsArchitecture:
    class Meta:
        name = "dynamicModelsArchitecture"
        namespace = "http://www.rte-france.com/dynawo"

    modelica_model: list[ModelicaModel] = field(
        default_factory=list,
        metadata={
            "name": "modelicaModel",
            "type": "Element",
        },
    )
    model_template: list[ModelTemplate] = field(
        default_factory=list,
        metadata={
            "name": "modelTemplate",
            "type": "Element",
        },
    )
    black_box_model: list[BlackBoxModel] = field(
        default_factory=list,
        metadata={
            "name": "blackBoxModel",
            "type": "Element",
        },
    )
    model_template_expansion: list[ModelTemplateExpansion] = field(
        default_factory=list,
        metadata={
            "name": "modelTemplateExpansion",
            "type": "Element",
        },
    )
    connect: list[Connect] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    macro_connect: list[MacroConnect] = field(
        default_factory=list,
        metadata={
            "name": "macroConnect",
            "type": "Element",
        },
    )
    macro_connector: list[MacroConnector] = field(
        default_factory=list,
        metadata={
            "name": "macroConnector",
            "type": "Element",
        },
    )
    macro_static_reference: list[MacroStaticReference] = field(
        default_factory=list,
        metadata={
            "name": "macroStaticReference",
            "type": "Element",
        },
    )
