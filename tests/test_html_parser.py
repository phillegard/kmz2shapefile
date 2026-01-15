"""Tests for HTML table parsing."""

import pytest
from lxml import etree

from kmz2shapefile.html_parser import HTMLTableParser


class TestHTMLTableParser:
    """Tests for HTMLTableParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HTMLTableParser()

    def test_parse_simple_table(self):
        """Test parsing simple HTML table."""
        html = """
        <table>
            <tr><td>Name</td><td>John</td></tr>
            <tr><td>Age</td><td>30</td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert result['Name'] == 'John'
        assert result['Age'] == 30

    def test_parse_with_th_header(self):
        """Test parsing table with th headers."""
        html = """
        <table>
            <tr><th>Key</th><td>Value</td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert result['Key'] == 'Value'

    def test_type_coercion_int(self):
        """Test integer type coercion."""
        html = """
        <table>
            <tr><td>Count</td><td>42</td></tr>
            <tr><td>Negative</td><td>-10</td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert result['Count'] == 42
        assert isinstance(result['Count'], int)
        assert result['Negative'] == -10

    def test_type_coercion_float(self):
        """Test float type coercion."""
        html = """
        <table>
            <tr><td>Price</td><td>19.99</td></tr>
            <tr><td>Latitude</td><td>-122.084075</td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert result['Price'] == pytest.approx(19.99)
        assert isinstance(result['Price'], float)
        assert result['Latitude'] == pytest.approx(-122.084075)

    def test_type_coercion_null(self):
        """Test null type coercion."""
        html = """
        <table>
            <tr><td>Empty</td><td><Null></td></tr>
            <tr><td>Missing</td><td></td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert result['Empty'] is None
        assert result['Missing'] is None

    def test_type_coercion_string(self):
        """Test string values remain strings."""
        html = """
        <table>
            <tr><td>Name</td><td>Test String</td></tr>
            <tr><td>Code</td><td>ABC123</td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert result['Name'] == 'Test String'
        assert isinstance(result['Name'], str)
        assert result['Code'] == 'ABC123'

    def test_parse_none_description(self):
        """Test that None description returns empty dict."""
        result = self.parser.parse_attributes(None)
        assert result == {}

    def test_parse_empty_string(self):
        """Test that empty string returns empty dict."""
        result = self.parser.parse_attributes('')
        assert result == {}

    def test_parse_no_table(self):
        """Test HTML without table returns empty dict."""
        html = "<p>Just some text</p>"
        result = self.parser.parse_attributes(html)
        assert result == {}

    def test_parse_malformed_html(self):
        """Test malformed HTML is handled gracefully."""
        html = "<table><tr><td>Key<td>Value</tr></table"
        result = self.parser.parse_attributes(html)
        # Should not raise, may or may not parse successfully
        assert isinstance(result, dict)

    def test_parse_extended_data(self):
        """Test parsing ExtendedData XML."""
        xml = """
        <ExtendedData xmlns="http://www.opengis.net/kml/2.2">
            <SchemaData>
                <SimpleData name="Population">10000</SimpleData>
                <SimpleData name="Area">5.5</SimpleData>
            </SchemaData>
        </ExtendedData>
        """
        element = etree.fromstring(xml)
        result = self.parser.parse_extended_data(element)

        assert result['Population'] == 10000
        assert result['Area'] == pytest.approx(5.5)

    def test_parse_extended_data_with_data_elements(self):
        """Test parsing ExtendedData with Data elements."""
        xml = """
        <ExtendedData>
            <Data name="Category">
                <value>Residential</value>
            </Data>
        </ExtendedData>
        """
        element = etree.fromstring(xml)
        result = self.parser.parse_extended_data(element)

        assert result['Category'] == 'Residential'

    def test_parse_extended_data_none(self):
        """Test that None ExtendedData returns empty dict."""
        result = self.parser.parse_extended_data(None)
        assert result == {}

    def test_skip_empty_keys(self):
        """Test that rows with empty keys are skipped."""
        html = """
        <table>
            <tr><td></td><td>Value</td></tr>
            <tr><td>Key</td><td>Value</td></tr>
        </table>
        """
        result = self.parser.parse_attributes(html)

        assert '' not in result
        assert 'Key' in result
