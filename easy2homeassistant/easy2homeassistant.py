#!/usr/bin/env python3

"""A python script to convert a KNX easy configuration to a HomeAssistant YAML configuration."""

import argparse
import logging
import os
import tempfile
import zipfile

from logging_config import configure_logging, set_logging_level
from yaml_serializer import serialize_to_file
from easy_parser import XMLParser
from homeassistant_entities import convert_project_to_entities
from xml_validator import XMLValidator

configure_logging()
logger = logging.getLogger(__name__)


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
    arg_parser.add_argument(
        "--sort",
        action=argparse.BooleanOptionalAction,
        help="Sort the output YAML file by entity name.",
    )

    return arg_parser.parse_args()


def get_configuration_xml_file(project_dir, file_name):
    """Get the path to an xml file in the temporary directory."""
    xml_file = os.path.join(project_dir, "configuration", file_name)
    if not os.path.exists(xml_file):
        logger.error("%s not found in the extracted files.", xml_file)
        return None

    return xml_file


def main():
    """Main function to extract and convert an easy project to a HomeAssistant configuration."""
    args = parse_arguments()

    set_logging_level(args.loglevel.upper())

    package_directory = os.path.dirname(os.path.abspath(__file__))

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("Extracting files to temporary directory '%s'", temp_dir)

        with zipfile.ZipFile(args.input, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        channels_xml_file = get_configuration_xml_file(temp_dir, "Channels.xml")
        if channels_xml_file is None:
            return

        products_xml_file = get_configuration_xml_file(temp_dir, "Products.xml")
        if products_xml_file is None:
            return

        schemes_path = os.path.join(package_directory, "resources", "schemes")
        validator = XMLValidator(schemes_path)
        if not validator.validate(channels_xml_file):
            logger.error("Scheme validation of '%s' failed!", channels_xml_file)
            return

        if not validator.validate(products_xml_file):
            logger.error("Scheme validation of '%s' failed!", products_xml_file)
            return

        parser = XMLParser()
        parser.parse_products_xml(products_xml_file)
        parser.parse_channels_xml(channels_xml_file)
        project = parser.get_project()

        entities = convert_project_to_entities(project, args.sort)

        yaml_configuration = args.output
        logger.info("Exporting entities to '%s'", yaml_configuration)
        serialize_to_file(entities, yaml_configuration)

        logger.info("Data exported to '%s' successfully.", yaml_configuration)


if __name__ == "__main__":
    main()
