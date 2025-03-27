"""A module to parse easy project xml files."""

import logging
import xml.etree.ElementTree as ET

from easy_types import Channel, Datapoint, Product, Project

logger = logging.getLogger(__name__)


# xml parsing
class XMLParser:
    """A class to parse an easy project xml file."""

    def __init__(self):
        self.project = Project()

    def parse_group_addresses(self, group_addresses):
        """Parse group addresses and append them to the currently parsed datapoint."""
        for config in group_addresses.findall("config"):
            address = config.get("name")

            logger.debug("Parse group address '%s'", address)
            try:
                numeric_address = int(address)
                self.project.channels[-1].datapoints[-1].group_addresses.append(
                    numeric_address
                )
            except ValueError:
                logger.warning("Skip invalid groupAddress '%s'", address)

    def parse_datapoints(self, datapoints):
        """Parse datapoints and set them on the currently parsed channel."""

        for config in datapoints.findall("config"):
            self.project.channels[-1].datapoints.append(Datapoint())

            for prop in config.findall("property"):
                if prop.get("key") == "name":
                    self.project.channels[-1].datapoints[-1].name = prop.get("value")
            # parse group addresses
            self.parse_config(config)

    def parse_context(self, context):
        """Parse a context element and set the serial number on the currently parsed channel."""
        for prop in context.findall("property"):
            if prop.get("key") == "product.serialNumber":
                self.project.channels[-1].serial_number = prop.get("value")
                break

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
        """Parse a channel element."""
        self.project.channels.append(Channel())

        for prop in channel.findall("property"):
            if prop.get("key") == "Name":
                self.project.channels[-1].name = prop.get("value")
            elif prop.get("key") == "Icon":
                self.project.channels[-1].icon = prop.get("value")

        for config in channel.findall("config"):
            self.parse_config(config)

    def parse_channels_xml(self, channels_xml):
        """Parse the Channels.xml file and return the entities."""
        logger.info("Parsing xml file '%s'", channels_xml)

        tree = ET.parse(channels_xml)
        root = tree.getroot()

        for channel in root.findall("config"):
            self.parse_channel(channel)

    def parse_product(self, product):
        """Parse a product element. Store the name for the serial number."""
        self.project.products.append(Product())
        for prop in product.findall("property"):
            if prop.get("key") == "SerialNumber":
                self.project.products[-1].serialNumber = prop.get("value")
            elif prop.get("key") == "product.name":
                self.project.products[-1].name = prop.get("value")

    def parse_products_xml(self, products_xml):
        """Parse the Products.xml file."""
        logger.info("Parsing xml file '%s'", products_xml)

        tree = ET.parse(products_xml)
        root = tree.getroot()

        for product in root.findall("config"):
            self.parse_product(product)

    def get_project(self):
        """Return the parsed project."""
        return self.project
