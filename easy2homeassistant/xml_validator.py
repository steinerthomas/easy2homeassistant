"""Module for XML validation using XSD schema."""

import logging
import os
from lxml import etree

logger = logging.getLogger(__name__)


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

        validator = self.get_scheme_for_xml(xml_path)
        if validator is None:
            return False

        result = validator.validate(xml_doc)
        if not result:
            logger.error(validator.error_log.filter_from_errors()[0])

        return result
