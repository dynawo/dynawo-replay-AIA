from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.rte-france.com/dynawo"


@dataclass
class LostEquipment:
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class LostEquipments:
    class Meta:
        name = "lostEquipments"
        namespace = "http://www.rte-france.com/dynawo"

    lost_equipment: list[LostEquipment] = field(
        default_factory=list,
        metadata={
            "name": "lostEquipment",
            "type": "Element",
        },
    )
