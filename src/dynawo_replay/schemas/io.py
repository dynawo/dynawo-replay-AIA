from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

NAMESPACE_PREFIX_MAP = {
    "dyn": "http://www.rte-france.com/dynawo",
    "iidm": "http://www.itesla_project.eu/schema/iidm/1_0",
}


class CustomSerializer(XmlSerializer):
    "Class override to force using the namespace defined in this module"

    def write(self, out, obj, ns_map=None):
        super().write(out, obj, ns_map=NAMESPACE_PREFIX_MAP)


parser = XmlParser()
serializer = CustomSerializer(
    config=SerializerConfig(
        indent="    ",
    )
)
