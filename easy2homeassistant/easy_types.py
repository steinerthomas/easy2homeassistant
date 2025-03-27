"""Dataclasses for xml parser."""

from typing import List
from dataclasses import dataclass, field


@dataclass
class Datapoint:
    """A data class to represent a datapoint."""

    name: str = ""
    groupAddresses: List[int] = field(default_factory=list)

    def is_valid(self):
        """Check if the datapoint is valid."""
        return self.name != "" and len(self.groupAddresses) > 0

    def get_lowest_address(self):
        """Return the lowest address."""
        if len(self.groupAddresses) == 0:
            return None
        return min(self.groupAddresses)


@dataclass
class Channel:
    """A data class to represent a channel."""

    Name: str = ""
    Icon: str = ""
    serialNumber: str = ""
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
