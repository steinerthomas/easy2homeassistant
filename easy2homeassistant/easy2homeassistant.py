#!/usr/bin/env python3

"""A python script to convert a KNX easy configuration to a HomeAssistant YAML configuration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import argparse
import logging
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

import colorlog
import yaml

from xmlvalidator import XMLValidator

# logging
log_colors = {
    "DEBUG": "light_black",
    "INFO": "black",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

LOGGER_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
console_handler = colorlog.StreamHandler(sys.stdout)
console_formatter = colorlog.ColoredFormatter(
    f"%(log_color)s{LOGGER_FORMAT}", log_colors=log_colors
)
console_handler.setFormatter(console_formatter)

LOG_FILE_PATH = "easy2homeassistant.log"
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_formatter = logging.Formatter(LOGGER_FORMAT)
file_handler.setFormatter(file_formatter)

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class StringValue(str):
    """A class to represent a string value for yaml serialization."""


def quoted_str_representer(dumper, data):
    """A custom representer to quote strings in yaml."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(StringValue, quoted_str_representer)


def object_to_dict(obj):
    """Convert an object to a dictionary for yaml serialization."""
    if isinstance(obj, list):
        return [object_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {
            key: object_to_dict(value)
            for key, value in obj.items()
            if value is not None
        }
    if hasattr(obj, "__dict__"):
        return {
            key: object_to_dict(value)
            for key, value in obj.__dict__.items()
            if value is not None
        }
    if isinstance(obj, str):
        return StringValue(obj)
    return obj


def generic_representer(dumper, data):
    """A generic representer to convert objects to dictionaries."""
    return dumper.represent_dict(object_to_dict(data))


yaml.add_multi_representer(object, generic_representer)


# data structures
class EntityKind(Enum):
    """An enumeration to differentiate entities."""

    UNDEFINED = 0
    LIGHT = 1
    COVER = 2

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


@dataclass
class Entities:
    """A data class to represent a collection of entities."""

    light: List = field(default_factory=list)
    cover: List = field(default_factory=list)

    def add_entity(self, entity):
        """Add an entity to the corresponding list."""

        if isinstance(entity, Light):
            self.light.append(entity)
        elif isinstance(entity, Cover):
            self.cover.append(entity)
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
    }

    def __init__(self):
        self.entities = Entities()
        self.entity = None  # currently parsed entity
        self.address_attribute_name = None  # currently parsed address

    def add_entity(self):
        """Add the current entity to the entities list."""
        if self.entity is not None:
            self.entities.add_entity(self.entity)
            self.entity = None
        else:
            logger.error("Empty entity occurred!")

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
            logger.error("No group address found!")

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

    def parse_config(self, config):
        """Generic parser for a config element."""
        if config is None:
            logger.error("Unexpected empty config!")
            return

        name = config.get("name")
        if name in ("Context", "Parameters"):
            logger.debug("Skip '%s'", name)
            return
        if name == "datapoints":
            self.parse_datapoints(config)
            return
        if name == "groupAddresses":
            self.parse_group_addresses(config)
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
                if name == "":
                    logger.debug("Skip unnamed channel: %s", channel.get("name"))
            elif prop.get("key") == "Icon":
                if prop.get("value") == "icon-shutter":
                    kind = EntityKind.COVER
                else:
                    kind = EntityKind.LIGHT

        if name != "" and kind != EntityKind.UNDEFINED:
            # create entity and search for attributes
            if kind is EntityKind.COVER:
                self.entity = Cover(name)
            elif kind is EntityKind.LIGHT:
                self.entity = Light(name)

            logger.info("Found entity '%s' of kind %s", name, kind)
            for config in channel.findall("config"):
                self.parse_config(config)
            self.add_entity()

    def parse_channel_xml(self, channels_xml):
        """Parse the Channels.xml file and return the entities."""
        logger.info("Parsing xml file '%s'", channels_xml)

        tree = ET.parse(channels_xml)
        root = tree.getroot()

        for channel in root.findall("config"):
            self.parse_channel(channel)

        return self.entities


def parse_arguments():
    """Parse command line arguments."""
    arg_parser = argparse.ArgumentParser(
        description="Process an easy project and export data to YAML."
    )
    arg_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input easy project (txa) file.",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output HomeAssistant yaml file.",
    )
    arg_parser.add_argument(
        "-l",
        "--loglevel",
        default="INFO",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    return arg_parser.parse_args()


def main():
    """Main function to extract and convert an easy project to a HomeAssistant configuration."""
    args = parse_arguments()

    logger.setLevel(args.loglevel.upper())

    package_directory = os.path.dirname(os.path.abspath(__file__))

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Extracting files to temporary directory '%s'", temp_dir)

        with zipfile.ZipFile(args.input, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        channels_xml_file = os.path.join(temp_dir, "configuration", "Channels.xml")

        channels_scheme_file = os.path.join(
            package_directory, "resources", "schemes", "channels.xsd"
        )
        validator = XMLValidator(channels_scheme_file)
        if not validator.validate(channels_xml_file):
            logger.error("Scheme validation of '%s' failed!", channels_xml_file)
            return

        if not os.path.exists(channels_xml_file):
            logger.error("%s not found in the extracted files.", channels_xml_file)
            return

        parser = XMLParser()
        entities = parser.parse_channel_xml(channels_xml_file)

        yaml_configuration = args.output
        logger.info("Exporting entities to '%s'", yaml_configuration)
        with open(yaml_configuration, "w", encoding="utf-8") as yaml_file:
            yaml_file.write(yaml.dump(entities, sort_keys=False, allow_unicode=True))

        logger.info("Data exported to '%s' successfully.", yaml_configuration)


if __name__ == "__main__":
    main()
