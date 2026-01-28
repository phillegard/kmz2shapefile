"""Tests for HTML table parsing."""

import pytest
from lxml import etree

from kmz2shapefile.html_parser import HTMLTableParser


class TestHTMLTableParser:
    """Tests for HTMLTableParser class."""

    @pytest.fixture
    def parser(self):
        return HTMLTableParser()

    def test_parse_simple_table(self, parser):
        """Test parsing simple HTML table."""
        html = """
        <table>
            <tr><td>Name</td><td>John</td></tr>
            <tr><td>Age</td><td>30</td></tr>
        </table>
        """
        result = parser.parse_attributes(html)
        assert result == {'Name': 'John', 'Age': 30}

    def test_parse_with_th_header(self, parser):
        """Test parsing table with th headers."""
        html = "<table><tr><th>Key</th><td>Value</td></tr></table>"
        assert parser.parse_attributes(html) == {'Key': 'Value'}

    def test_type_coercion_int(self, parser):
        """Test integer type coercion."""
        html = """
        <table>
            <tr><td>Count</td><td>42</td></tr>
            <tr><td>Negative</td><td>-10</td></tr>
        </table>
        """
        result = parser.parse_attributes(html)
        assert result['Count'] == 42
        assert isinstance(result['Count'], int)
        assert result['Negative'] == -10

    def test_type_coercion_float(self, parser):
        """Test float type coercion."""
        html = """
        <table>
            <tr><td>Price</td><td>19.99</td></tr>
            <tr><td>Latitude</td><td>-122.084075</td></tr>
        </table>
        """
        result = parser.parse_attributes(html)
        assert result['Price'] == pytest.approx(19.99)
        assert isinstance(result['Price'], float)
        assert result['Latitude'] == pytest.approx(-122.084075)

    def test_type_coercion_null(self, parser):
        """Test null type coercion."""
        html = """
        <table>
            <tr><td>Empty</td><td><Null></td></tr>
            <tr><td>Missing</td><td></td></tr>
        </table>
        """
        result = parser.parse_attributes(html)
        assert result['Empty'] is None
        assert result['Missing'] is None

    def test_type_coercion_string(self, parser):
        """Test string values remain strings."""
        html = """
        <table>
            <tr><td>Name</td><td>Test String</td></tr>
            <tr><td>Code</td><td>ABC123</td></tr>
        </table>
        """
        result = parser.parse_attributes(html)
        assert result['Name'] == 'Test String'
        assert isinstance(result['Name'], str)
        assert result['Code'] == 'ABC123'

    def test_parse_none_description(self, parser):
        """Test that None description returns empty dict."""
        assert parser.parse_attributes(None) == {}

    def test_parse_empty_string(self, parser):
        """Test that empty string returns empty dict."""
        assert parser.parse_attributes('') == {}

    def test_parse_no_table(self, parser):
        """Test HTML without table returns empty dict."""
        assert parser.parse_attributes("<p>Just some text</p>") == {}

    def test_parse_malformed_html(self, parser):
        """Test malformed HTML is handled gracefully."""
        result = parser.parse_attributes("<table><tr><td>Key<td>Value</tr></table")
        assert isinstance(result, dict)

    def test_skip_empty_keys(self, parser):
        """Test that rows with empty keys are skipped."""
        html = """
        <table>
            <tr><td></td><td>Value</td></tr>
            <tr><td>Key</td><td>Value</td></tr>
        </table>
        """
        result = parser.parse_attributes(html)
        assert '' not in result
        assert 'Key' in result


class TestExtendedDataParser:
    """Tests for HTMLTableParser.parse_extended_data()."""

    @pytest.fixture
    def parser(self):
        return HTMLTableParser()

    def test_parse_extended_data_none(self, parser):
        """Test that None ExtendedData returns empty dict."""
        assert parser.parse_extended_data(None) == {}

    def test_parse_simple_data(self, parser):
        """Test parsing ExtendedData with SimpleData elements."""
        xml = """
        <ExtendedData xmlns="http://www.opengis.net/kml/2.2">
            <SchemaData>
                <SimpleData name="Population">10000</SimpleData>
                <SimpleData name="Area">5.5</SimpleData>
            </SchemaData>
        </ExtendedData>
        """
        result = parser.parse_extended_data(etree.fromstring(xml))
        assert result['Population'] == 10000
        assert result['Area'] == pytest.approx(5.5)

    def test_parse_data_with_value(self, parser):
        """Test parsing ExtendedData with Data elements."""
        xml = """
        <ExtendedData>
            <Data name="Category"><value>Residential</value></Data>
        </ExtendedData>
        """
        result = parser.parse_extended_data(etree.fromstring(xml))
        assert result == {'Category': 'Residential'}
