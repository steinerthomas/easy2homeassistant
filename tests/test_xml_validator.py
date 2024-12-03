"""Tests for xml_validator.py."""

import unittest
from xml_validator import XMLValidator


class TestXMLValidator(unittest.TestCase):
    """Tests for XMLValidator."""

    def test_xml_validator(self):
        """Test the XMLValidator with a valid XML file."""
        validator = XMLValidator("easy2homeassistant/resources/schemes")
        xml_file = "tests/resources/configuration/Channels.xml"

        result = validator.validate(xml_file)

        self.assertTrue(result)

    def test_xml_validator_no_property(self):
        """Test the XMLValidator with a valid XML file which has no Last-Modified property."""
        validator = XMLValidator("easy2homeassistant/resources/schemes")
        xml_file = "tests/resources/configuration/no-property/Channels.xml"

        result = validator.validate(xml_file)

        self.assertTrue(result)

    def test_xml_validator_invalid(self):
        """Test the XMLValidator with an invalid XML file."""
        validator = XMLValidator("easy2homeassistant/resources/schemes")
        xml_file = "tests/resources/configuration/invalid/Channels.xml"

        result = validator.validate(xml_file)

        self.assertFalse(result)

    def test_xml_validator_invalid_scheme(self):
        """Test the XMLValidator with an invalid scheme."""
        validator = XMLValidator("easy2homeassistant/resources/schemes")
        xml_file = "tests/resources/configuration/invalid/InvalidFilename.xml"

        result = validator.validate(xml_file)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
