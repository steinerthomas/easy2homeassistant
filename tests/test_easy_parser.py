"""Tests for easy_parser.py."""

import unittest
import yaml

from easy_parser import XMLParser
from homeassistant_entities import convert_project_to_entities


class TestXMLParser(unittest.TestCase):
    """Tests for XMLParser."""

    def setUp(self):
        """Set up the test case."""
        self.maxDiff = None  # Allow full diff output for assertions

    def test_xml_parser_channels_xml(self):
        """Test the XMLParser with a Channels.xml and Products.xml file."""

        parser = XMLParser()
        channels_xml_file = "tests/resources/configuration/Channels.xml"
        products_xml_file = "tests/resources/configuration/Products.xml"
        expected_output_file = "tests/resources/output.yaml"

        parser.parse_products_xml(products_xml_file)
        parser.parse_channels_xml(channels_xml_file)
        project = parser.get_project()

        entities = convert_project_to_entities(project)

        with open(expected_output_file, "r", encoding="utf-8") as f:
            expected_output = yaml.safe_load(f)

        actual_output = yaml.safe_load(
            yaml.dump(entities, sort_keys=False, allow_unicode=True)
        )

        self.assertEqual(actual_output, expected_output)


if __name__ == "__main__":
    unittest.main()
