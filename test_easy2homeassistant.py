import unittest
import yaml
from easy2homeassistant import XMLParser


class TestXMLParser(unittest.TestCase):

    def test_xml_parser_with_real_file(self):
        parser = XMLParser()
        channels_xml_file = "tests/resources/configuration/Channels.xml"
        expected_output_file = "tests/resources/output.yaml"

        entities = parser.parse_channel_xml(channels_xml_file)

        with open(expected_output_file, "r", encoding="utf-8") as f:
            expected_output = yaml.safe_load(f)

        actual_output = yaml.safe_load(
            yaml.dump(entities, sort_keys=False, allow_unicode=True)
        )

        self.assertEqual(actual_output, expected_output)


if __name__ == "__main__":
    unittest.main()
