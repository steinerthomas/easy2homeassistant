"""Module for XML validation using XSD schema."""

from lxml import etree
import os


class XMLValidator:
    """Class for XML validation using XSD schema."""

    def __init__(self, schemes_path: str):
        """Initialize the XMLValidator with the XSD schemes path."""
        self.schemes = self._parse_schemes(schemes_path)

    def _parse_schemes(self, schemes_path: str) -> dict:
        """Parse the XSD schemes from the given path."""
        schemes = {}
        for scheme in os.listdir(schemes_path):
            if scheme.endswith(".xsd"):
                scheme_name = scheme.split(".")[0]
                xml_scheme_doc = etree.parse(os.path.join(schemes_path, scheme))
                xml_scheme = etree.XMLSchema(xml_scheme_doc)
                schemes[scheme_name] = xml_scheme
        return schemes

    def get_scheme_for_xml(self, xml_path: str) -> etree.XMLSchema:
        """Get the XSD scheme for the XML file."""
        xml_name = os.path.basename(xml_path).split(".")[0]
        return self.schemes.get(xml_name.lower())

    def validate(self, xml_path: str) -> bool:
        """Validate the XML file using the XSD scheme."""
        xml_doc = etree.parse(xml_path)
        result = self.get_scheme_for_xml(xml_path).validate(xml_doc)

        return result
