from .config import settings
from .schemas.ddb_desc import Model
from .schemas.io import parser


def list_available_vars(model, dynawo=settings.DYNAWO_HOME):
    model = parser.parse(dynawo / "ddb" / f"{model}.desc.xml", Model)
    return model.elements.variables.variable
