"""Dataclasses for xml parser."""

from typing import List
from dataclasses import dataclass, field


@dataclass
class Datapoint:
    """A data class to represent a datapoint."""

    name: str = ""
    group_addresses: List[int] = field(default_factory=list)

    def is_valid(self):
        """Check if the datapoint is valid."""
        return self.name != "" and len(self.group_addresses) > 0

    def get_lowest_address(self):
        """Return the lowest address."""
        if len(self.group_addresses) == 0:
            return 0
        return min(self.group_addresses)


@dataclass
class Channel:
    """A data class to represent a channel."""

    name: str = ""
    icon: str = ""
    serial_number: str = ""
    datapoints: List[Datapoint] = field(default_factory=list)

    def is_valid(self):
        """Check if the channel is valid."""
        return len(self.datapoints) > 0


@dataclass
class Product:
    """A data class to represent a product."""

    name: str = ""
    serialNumber: str = ""


@dataclass
class Project:
    """ "A data class to represent a txa project."""

    channels: List[Channel] = field(default_factory=list)
    products: List[Product] = field(default_factory=list)
