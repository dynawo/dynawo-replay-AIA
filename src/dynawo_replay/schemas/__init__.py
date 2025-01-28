"""
The dataclasses defined in this package have been automatcally generated
out of XSD files provided by Dynaωo (v1.6.0) using ```xsdata``` generator tool.
Some of them have been modified later to add functionality.

More info at https://xsdata.readthedocs.io/en/latest/.
"""

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from .curves_input import CurveInput, CurvesInput
from .ddb_desc import Model
from .dyd import DynamicModelsArchitecture
from .jobs import Jobs
from .parameters import Parameter, ParametersSet, Set

parser = XmlParser()
serializer = XmlSerializer(
    config=SerializerConfig(
        indent="    ",
        globalns={
            "dyn": "http://www.rte-france.com/dynawo",
            "iidm": "http://www.itesla_project.eu/schema/iidm/1_0",
        },
    )
)

__all__ = [
    "parser",
    "serializer",
    "Jobs",
    "DynamicModelsArchitecture",
    "ParametersSet",
    "Set",
    "Parameter",
    "CurvesInput",
    "CurveInput",
    "Model",
]
