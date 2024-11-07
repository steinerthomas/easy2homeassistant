"""A module to parse easy project xml files."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# data structures
class EntityKind(Enum):
    """An enumeration to differentiate entities."""

    UNDEFINED = 0
    LIGHT = 1
    COVER = 2
    TEMPERATURE_SENSOR = 3

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


@dataclass
class Entities:
    """A data class to represent a collection of entities."""

    light: List = field(default_factory=list)
    cover: List = field(default_factory=list)
    sensor: List = field(default_factory=list)

    def add_entity(self, entity):
        """Add an entity to the corresponding list."""

        if isinstance(entity, Light):
            self.light.append(entity)
        elif isinstance(entity, Cover):
            self.cover.append(entity)
        elif isinstance(entity, TemperatureSensor):
            self.sensor.append(entity)
        else:
            logger.critical("Invalid entity '%s'", entity)


# xml parsing
class XMLParser:
    """A class to parse an easy project xml file."""

    ADDRESS_MAP = {
        # light
        "On/Off": "address",
        "Dim value": "brightness_address",
        "On/Off status": "state_address",
        "Dim value status": "brightness_state_address",
        # cover
        "Up/Down": "move_long_address",
        "Step/Stop": "stop_address",
        "Position control": "position_address",
        "Slat angle control": "angle_address",
        "Position control status": "position_state_address",
        "Slat angle control status": "angle_state_address",
        # sensor
        "Indoor temperature": "state_address",
    }

    def __init__(self):
        self.entities = Entities()
        self.entity = None  # currently parsed entity
        self.address_attribute_name = None  # currently parsed address
        self.products = {}

    def add_entity(self):
        """Add the current entity to the entities list."""
        added = False
        if self.entity is not None and self.entity.is_valid():
            self.entities.add_entity(self.entity)
            added = True

        self.entity = None
        return added

    def parse_group_addresses(self, group_addresses):
        """Parse group addresses and set the lowest address to the currently parsed entity."""
        lowest_address = float("inf")
        for config in group_addresses.findall("config"):
            address = config.get("name")
            logger.debug("Parse group address '%s'", address)
            try:
                lowest_address = min(lowest_address, int(address))
            except ValueError:
                logger.warning("Skip invalid groupAddress '%s'", address)

        if lowest_address != float("inf"):
            setattr(self.entity, self.address_attribute_name, lowest_address)
            logger.info(
                "'%s': Set attribute '%s' to '%s'",
                self.entity.name,
                self.address_attribute_name,
                lowest_address,
            )
        else:
            logger.info(
                "'%s': No group address for '%s'",
                self.entity.name,
                self.address_attribute_name,
            )

    def parse_datapoints(self, datapoints):
        """Parse datapoints and map them to the corresponding entity attribute."""
        for config in datapoints.findall("config"):
            for prop in config.findall("property"):
                if prop.get("key") == "name":
                    datapoint_name = prop.get("value")
                    if datapoint_name in self.ADDRESS_MAP:
                        # set attribute name and search for group addresses
                        self.address_attribute_name = self.ADDRESS_MAP[datapoint_name]
                        if hasattr(self.entity, self.address_attribute_name):
                            self.parse_config(config)
                        else:
                            logger.error(
                                "'%s' has no attribute '%s'!",
                                self.entity.name,
                                self.address_attribute_name,
                            )
                    else:
                        logger.info(
                            "'%s': Skip unmapped datapoint '%s'",
                            self.entity.name,
                            datapoint_name,
                        )

    def parse_context(self, context):
        """Parse a context element and set the entity name."""
        if self.entity.name != "":
            logger.debug(
                "The entity name is already set: '%s'. Skip parsing name by serial number!",
                self.entity.name,
            )
            return

        serial_number = ""
        for prop in context.findall("property"):
            if prop.get("key") == "product.serialNumber":
                serial_number = prop.get("value")
                break

        if serial_number in self.products:
            self.entity.name = self.products[serial_number]
            logger.info(
                "Set entity name to '%s' by serial number '%s'.",
                self.entity.name,
                serial_number,
            )
        else:
            logger.error(
                "No product name found for serial number '%s'.",
                serial_number,
            )

    def parse_config(self, config):
        """Generic parser for a config element."""
        if config is None:
            logger.error("Unexpected empty config!")
            return

        name = config.get("name")
        if name in ("Parameters"):
            logger.debug("Skip '%s'", name)
            return
        if name == "datapoints":
            self.parse_datapoints(config)
            return
        if name == "groupAddresses":
            self.parse_group_addresses(config)
            return
        if name == "Context":
            self.parse_context(config)
            return

        if name == "FunctionalBlocks" or name.lstrip("-").isdigit():
            logger.debug("Handle known config '%s'", name)
        else:
            logger.warning("Skip unhandled config '%s'", name)
            return

        self.parse_configs(config)

    def parse_configs(self, configs):
        """Parse a list of config elements."""
        for config in configs.findall("config"):
            self.parse_config(config)

    def parse_channel(self, channel):
        """Parse a channel element and create an entity."""
        name = ""
        kind = EntityKind.UNDEFINED

        for prop in channel.findall("property"):
            if prop.get("key") == "Name":
                name = prop.get("value")
            elif prop.get("key") == "Icon":
                icon = prop.get("value")
                if icon == "icon-shutter":
                    kind = EntityKind.COVER
                elif icon in ("icon-light", "icon-dimmer"):
                    kind = EntityKind.LIGHT
                elif icon == "icon-indoor_temperature":
                    kind = EntityKind.TEMPERATURE_SENSOR

        if kind != EntityKind.UNDEFINED:
            if kind in (EntityKind.COVER, EntityKind.LIGHT) and name == "":
                logger.debug("Skip unnamed channel of kind %s", kind)
                return

            # create entity and search for attributes
            if kind is EntityKind.COVER:
                self.entity = Cover(name)
            elif kind is EntityKind.LIGHT:
                self.entity = Light(name)
            elif kind is EntityKind.TEMPERATURE_SENSOR:
                self.entity = TemperatureSensor(name)

            logger.info("Found entity '%s' of kind %s", name, kind)
            for config in channel.findall("config"):
                self.parse_config(config)

    def parse_channels_xml(self, channels_xml):
        """Parse the Channels.xml file and return the entities."""
        logger.info("Parsing xml file '%s'", channels_xml)

        tree = ET.parse(channels_xml)
        root = tree.getroot()

        for channel in root.findall("config"):
            self.parse_channel(channel)
            if not self.add_entity():
                logger.debug("Skip unnamed channel: %s", channel.get("name"))

        return self.entities

    def parse_product(self, product):
        """Parse a product element. Store the name for the serial number."""
        name = ""
        serial_number = ""
        for prop in product.findall("property"):
            if prop.get("key") == "SerialNumber":
                serial_number = prop.get("value")
                if serial_number == "":
                    logger.warning(
                        "Found product without SerialNumber: %s", product.get("name")
                    )
            elif prop.get("key") == "product.name":
                name = prop.get("value")

        if serial_number != "":
            logger.info(
                "Found product '%s' with serial number '%s'", name, serial_number
            )
            self.products[serial_number] = name

    def parse_products_xml(self, products_xml):
        """Parse the Products.xml file."""
        logger.info("Parsing xml file '%s'", products_xml)

        tree = ET.parse(products_xml)
        root = tree.getroot()

        for product in root.findall("config"):
            self.parse_product(product)
