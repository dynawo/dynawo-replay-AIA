from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


class ConstraintsExportMode(Enum):
    XML = "XML"
    TXT = "TXT"


@dataclass
class CriteriaFileEntry:
    criteria_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "criteriaFile",
            "type": "Attribute",
            "required": True,
        },
    )


class CurvesExportMode(Enum):
    XML = "XML"
    CSV = "CSV"


@dataclass
class Directory:
    path: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    recursive: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class DynModelsEntry:
    dyd_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "dydFile",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class FinalStateEntry:
    export_iidmfile: Optional[bool] = field(
        default=None,
        metadata={
            "name": "exportIIDMFile",
            "type": "Attribute",
            "required": True,
        },
    )
    export_dump_file: Optional[bool] = field(
        default=None,
        metadata={
            "name": "exportDumpFile",
            "type": "Attribute",
            "required": True,
        },
    )
    timestamp: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


class FinalStateValuesExportMode(Enum):
    XML = "XML"
    CSV = "CSV"
    TXT = "TXT"


@dataclass
class FinalValuesEntry:
    pass


@dataclass
class InitValuesEntry:
    local: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    global_value: Optional[bool] = field(
        default=None,
        metadata={
            "name": "global",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class InitialStateEntry:
    file: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


class LevelFilter(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class LocalInitEntry:
    par_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "parFile",
            "type": "Attribute",
            "required": True,
        },
    )
    par_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "parId",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class LostEquipmentsEntry:
    pass


@dataclass
class NetworkEntry:
    iidm_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "iidmFile",
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
class SolverEntry:
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
            "required": True,
        },
    )
    par_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "parId",
            "type": "Attribute",
            "required": True,
        },
    )


class TimelineExportMode(Enum):
    TXT = "TXT"
    CSV = "CSV"
    XML = "XML"


@dataclass
class TimetableEntry:
    step: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class AppenderEntry:
    file: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    tag: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    lvl_filter: Optional[LevelFilter] = field(
        default=None,
        metadata={
            "name": "lvlFilter",
            "type": "Attribute",
        },
    )
    show_level_tag: Optional[bool] = field(
        default=None,
        metadata={
            "name": "showLevelTag",
            "type": "Attribute",
        },
    )
    time_stamp_format: Optional[str] = field(
        default=None,
        metadata={
            "name": "timeStampFormat",
            "type": "Attribute",
        },
    )
    separator: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ConstraintsEntry:
    export_mode: Optional[ConstraintsExportMode] = field(
        default=None,
        metadata={
            "name": "exportMode",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class CurvesEntry:
    input_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "inputFile",
            "type": "Attribute",
            "required": True,
        },
    )
    export_mode: Optional[CurvesExportMode] = field(
        default=None,
        metadata={
            "name": "exportMode",
            "type": "Attribute",
            "required": True,
        },
    )
    iteration_step: Optional[int] = field(
        default=None,
        metadata={
            "name": "iterationStep",
            "type": "Attribute",
        },
    )
    time_step: Optional[float] = field(
        default=None,
        metadata={
            "name": "timeStep",
            "type": "Attribute",
        },
    )


@dataclass
class FinalStateValuesEntry:
    input_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "inputFile",
            "type": "Attribute",
            "required": True,
        },
    )
    export_mode: FinalStateValuesExportMode = field(
        default=FinalStateValuesExportMode.CSV,
        metadata={
            "name": "exportMode",
            "type": "Attribute",
        },
    )


@dataclass
class ModelicaModelsDirEntry:
    directory: list[Directory] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    model_extension: Optional[str] = field(
        default=None,
        metadata={
            "name": "modelExtension",
            "type": "Attribute",
        },
    )
    use_standard_models: Optional[bool] = field(
        default=None,
        metadata={
            "name": "useStandardModels",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class PrecompiledModelsDirEntry:
    directory: list[Directory] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    use_standard_models: Optional[bool] = field(
        default=None,
        metadata={
            "name": "useStandardModels",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SimulationEntry:
    criteria: list[CriteriaFileEntry] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    start_time: Optional[float] = field(
        default=None,
        metadata={
            "name": "startTime",
            "type": "Attribute",
            "required": True,
        },
    )
    stop_time: Optional[float] = field(
        default=None,
        metadata={
            "name": "stopTime",
            "type": "Attribute",
            "required": True,
        },
    )
    criteria_step: Optional[int] = field(
        default=None,
        metadata={
            "name": "criteriaStep",
            "type": "Attribute",
        },
    )
    precision: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    timeout: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class TimelineEntry:
    export_mode: Optional[TimelineExportMode] = field(
        default=None,
        metadata={
            "name": "exportMode",
            "type": "Attribute",
            "required": True,
        },
    )
    export_time: Optional[bool] = field(
        default=None,
        metadata={
            "name": "exportTime",
            "type": "Attribute",
        },
    )
    max_priority: Optional[int] = field(
        default=None,
        metadata={
            "name": "maxPriority",
            "type": "Attribute",
        },
    )
    filter: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LogsEntry:
    appender: list[AppenderEntry] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )


@dataclass
class ModelerEntry:
    network: Optional[NetworkEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    dyn_models: list[DynModelsEntry] = field(
        default_factory=list,
        metadata={
            "name": "dynModels",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
            "min_occurs": 1,
        },
    )
    initial_state: Optional[InitialStateEntry] = field(
        default=None,
        metadata={
            "name": "initialState",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    precompiled_models: Optional[PrecompiledModelsDirEntry] = field(
        default=None,
        metadata={
            "name": "precompiledModels",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
            "required": True,
        },
    )
    modelica_models: Optional[ModelicaModelsDirEntry] = field(
        default=None,
        metadata={
            "name": "modelicaModels",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
            "required": True,
        },
    )
    compile_dir: Optional[str] = field(
        default=None,
        metadata={
            "name": "compileDir",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class OutputsEntry:
    dump_init_values: Optional[InitValuesEntry] = field(
        default=None,
        metadata={
            "name": "dumpInitValues",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    dump_final_values: Optional[FinalValuesEntry] = field(
        default=None,
        metadata={
            "name": "dumpFinalValues",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    constraints: Optional[ConstraintsEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    timeline: Optional[TimelineEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    timetable: Optional[TimetableEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    final_state: list[FinalStateEntry] = field(
        default_factory=list,
        metadata={
            "name": "finalState",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    curves: Optional[CurvesEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    final_state_values: Optional[FinalStateValuesEntry] = field(
        default=None,
        metadata={
            "name": "finalStateValues",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    lost_equipments: Optional[LostEquipmentsEntry] = field(
        default=None,
        metadata={
            "name": "lostEquipments",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    logs: Optional[LogsEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    directory: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Job:
    solver: Optional[SolverEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    modeler: Optional[ModelerEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    simulation: Optional[SimulationEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    outputs: Optional[OutputsEntry] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
        },
    )
    local_init: Optional[LocalInitEntry] = field(
        default=None,
        metadata={
            "name": "localInit",
            "type": "Element",
            "namespace": "http://www.rte-france.com/dynawo",
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
class Jobs:
    class Meta:
        name = "jobs"
        namespace = "http://www.rte-france.com/dynawo"

    job: list[Job] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
