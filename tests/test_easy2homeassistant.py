"""Tests for easy2homeassistant.py."""

import unittest
import yaml
from easy2homeassistant import XMLParser


class TestXMLParser(unittest.TestCase):
    """Tests for XMLParser."""

    def test_xml_parser_channels_xml(self):
        """Test the XMLParser with a Channels.xml file."""

        parser = XMLParser()
        channels_xml_file = "tests/resources/configuration/Channels.xml"
        expected_output_file = "tests/resources/output.yaml"

        entities = parser.parse_channels_xml(channels_xml_file)

        with open(expected_output_file, "r", encoding="utf-8") as f:
            expected_output = yaml.safe_load(f)

        actual_output = yaml.safe_load(
            yaml.dump(entities, sort_keys=False, allow_unicode=True)
        )

        self.assertEqual(actual_output, expected_output)


if __name__ == "__main__":
    unittest.main()
