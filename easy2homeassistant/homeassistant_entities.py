"""A module to convert parsed data into homeassistant entities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from easy_types import Project


class EntityKind(Enum):
    """An enumeration to differentiate entities."""

    UNDEFINED = 0
    LIGHT = 1
    COVER = 2
    TEMPERATURE_SENSOR = 3
    CLIMATE = 4

    def __str__(self):
        return f"{self.name} ({self.value})"


@dataclass
class Light:
    """A data class to represent a light entity."""

    name: str
    address: int = 0
    brightness_address: Optional[int] = None
    state_address: int = 0
    brightness_state_address: Optional[int] = None

    def is_valid(self):
        """Check if the entity is valid."""
        return self.name != "" and self.address != 0 and self.state_address != 0

    def get_kind(self):
        """Return the entity kind."""
        return EntityKind.LIGHT


@dataclass
class Cover:
    """A data class to represent a cover entity."""

    name: str
    move_long_address: int = 0
    stop_address: int = 0
    position_address: int = 0
    angle_address: int = 0
    position_state_address: int = 0
    angle_state_address: int = 0

    def is_valid(self):
        """Check if the entity is valid."""
        return (
            self.name != ""
            and self.move_long_address != 0
            and self.stop_address != 0
            and self.position_address != 0
            and self.angle_address != 0
            and self.position_state_address != 0
            and self.angle_state_address != 0
        )

    def get_kind(self):
        """Return the entity kind."""
        return EntityKind.COVER


@dataclass
class TemperatureSensor:
    """A data class to represent a temperature sensor entity."""

    name: str
    state_address: int = 0
    type: str = "temperature"
    state_class: str = "measurement"

    def is_valid(self):
        """Check if the entity is valid."""
        return self.name != "" and self.state_address != 0

    def get_kind(self):
        """Return the entity kind."""
        return EntityKind.TEMPERATURE_SENSOR


@dataclass
class Climate:
    """A data class to represent a climate entity."""

    name: str
    temperature_address: int = 0
    target_temperature_state_address: int = 0
    setpoint_shift_address: Optional[int] = None
    setpoint_shift_state_address: Optional[int] = None
    operation_mode_address: Optional[int] = None
    operation_mode_state_address: Optional[int] = None
    heat_cool_address: Optional[int] = None
    heat_cool_state_address: Optional[int] = None
    on_off_address: Optional[int] = None

    def is_valid(self):
        """Check if the entity is valid."""
        return (
            self.name != ""
            and self.temperature_address != 0
            and self.target_temperature_state_address != 0
        )

    def get_kind(self):
        """Return the entity kind."""
        return EntityKind.CLIMATE


@dataclass
class Entities:
    """A data class to represent a collection of entities."""

    LIGHT_ADDRESS_MAP = {
        "On/Off": "address",
        "Dim value": "brightness_address",
        "On/Off status": "state_address",
        "Dim value status": "brightness_state_address",
    }

    COVER_ADDRESS_MAP = {
        "Up/Down": "move_long_address",
        "Step/Stop": "stop_address",
        "Position control": "position_address",
        "Slat angle control": "angle_address",
        "Position control status": "position_state_address",
        "Slat angle control status": "angle_state_address",
    }

    SENSOR_ADDRESS_MAP = {
        "Indoor temperature": "state_address",
    }

    CLIMATE_ADDRESS_MAP = {
        "Indoor temperature": "temperature_address",
        "Room temperature": "target_temperature_state_address",
        "Setpoint shift": "setpoint_shift_address",
        "Setpoint shift status": "setpoint_shift_state_address",
        "Mode": "operation_mode_address",
        "Mode status": "operation_mode_state_address",
        "Heat/Cool": "heat_cool_address",
        "Heat/Cool status": "heat_cool_state_address",
        "On/Off": "on_off_address",
    }

    ADDRESS_MAP = {
        EntityKind.LIGHT: LIGHT_ADDRESS_MAP,
        EntityKind.COVER: COVER_ADDRESS_MAP,
        EntityKind.TEMPERATURE_SENSOR: SENSOR_ADDRESS_MAP,
        EntityKind.CLIMATE: CLIMATE_ADDRESS_MAP,
    }

    light: List = field(default_factory=list)
    cover: List = field(default_factory=list)
    sensor: List = field(default_factory=list)
    climate: List = field(default_factory=list)

    def add_entity(self, entity):
        """Add an entity to the corresponding list."""

        if isinstance(entity, Light):
            self.light.append(entity)
        elif isinstance(entity, Cover):
            self.cover.append(entity)
        elif isinstance(entity, TemperatureSensor):
            self.sensor.append(entity)
        elif isinstance(entity, Climate):
            self.climate.append(entity)
        # else:
        #    logger.critical("Invalid entity '%s'", entity)


def convert_project_to_entities(project: Project) -> Entities:
    """Convert a project to a list of entities."""
    entities = Entities()

    for channel in project.channels:
        if not channel.is_valid():
            continue

        name = channel.Name

        if channel.Icon == "icon-shutter":
            entity = Cover(name)
        elif channel.Icon in ("icon-light", "icon-dimmer"):
            entity = Light(name)
        elif channel.Icon == "icon-indoor_temperature":
            if name == "":
                # in case of an unnamed sensor fallback to the product name
                for product in project.products:
                    if product.serialNumber == channel.serialNumber:
                        name = product.name
                        break
            entity = TemperatureSensor(name)
        elif channel.Icon == "icon-heat_regul":
            entity = Climate(name)
            # find the matching sensor for the climate entity
            for otherChannel in project.channels:
                if (
                    otherChannel.Icon == "icon-indoor_temperature"
                    and otherChannel.serialNumber == channel.serialNumber
                ):
                    for otherDatapoint in otherChannel.datapoints:
                        if otherDatapoint.name == "Indoor temperature":
                            address = otherDatapoint.get_lowest_address()
                            if address is not None:
                                setattr(entity, "temperature_address", address)
                            break
        else:
            continue

        for datapoint in channel.datapoints:
            if not datapoint.is_valid():
                continue

            address = datapoint.get_lowest_address()
            if address is None:
                continue

            name = datapoint.name
            if name in Entities.ADDRESS_MAP[entity.get_kind()]:
                setattr(entity, Entities.ADDRESS_MAP[entity.get_kind()][name], address)

        if entity and entity.is_valid():
            entities.add_entity(entity)
        entity = None

    return entities
