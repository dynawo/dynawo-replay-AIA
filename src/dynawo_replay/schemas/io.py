from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

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
