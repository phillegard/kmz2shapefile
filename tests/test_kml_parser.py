"""Tests for KML parsing."""

import pytest

from kmz2shapefile.kml_parser import KMLParser, Placemark
from kmz2shapefile.exceptions import KMLParseError


class TestKMLParser:
    """Tests for KMLParser class."""

    @pytest.fixture
    def parser(self):
        return KMLParser()

    def test_parse_simple_placemark(self, parser):
        """Test parsing a simple placemark with Point."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test Point</name>
                    <Point><coordinates>-122.084075,37.4220033,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        result = parser.parse(kml)
        assert len(result) == 1
        assert result[0].name == "Test Point"
        assert result[0].geometry_element is not None

    def test_parse_multiple_placemarks(self, parser):
        """Test parsing multiple placemarks."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark><name>Point 1</name><Point><coordinates>0,0,0</coordinates></Point></Placemark>
                <Placemark><name>Point 2</name><Point><coordinates>1,1,0</coordinates></Point></Placemark>
            </Document>
        </kml>
        """
        result = parser.parse(kml)
        assert len(result) == 2
        assert result[0].name == "Point 1"
        assert result[1].name == "Point 2"

    def test_parse_placemark_with_description(self, parser):
        """Test parsing placemark with HTML description."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test</name>
                    <description><![CDATA[<table><tr><td>Key</td><td>Value</td></tr></table>]]></description>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        result = parser.parse(kml)
        assert len(result) == 1
        assert result[0].description is not None
        assert 'table' in result[0].description

    def test_parse_without_namespace(self, parser):
        """Test parsing KML without namespace."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml>
            <Document>
                <Placemark>
                    <name>No Namespace</name>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        result = parser.parse(kml)
        assert len(result) == 1
        assert result[0].name == "No Namespace"

    def test_parse_invalid_xml(self, parser):
        """Test that invalid XML raises KMLParseError."""
        with pytest.raises(KMLParseError):
            parser.parse("not valid xml")

    def test_parse_empty_document(self, parser):
        """Test parsing document with no placemarks."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document></Document>
        </kml>
        """
        assert parser.parse(kml) == []

    def test_parse_placemark_with_extended_data(self, parser):
        """Test parsing placemark with ExtendedData."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>With ExtendedData</name>
                    <ExtendedData>
                        <SchemaData><SimpleData name="Population">10000</SimpleData></SchemaData>
                    </ExtendedData>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        result = parser.parse(kml)
        assert len(result) == 1
        assert result[0].extended_data is not None

    def test_parse_unnamed_placemark(self, parser):
        """Test parsing placemark without name gets 'Unnamed'."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark><Point><coordinates>0,0,0</coordinates></Point></Placemark>
            </Document>
        </kml>
        """
        result = parser.parse(kml)
        assert len(result) == 1
        assert result[0].name == "Unnamed"
