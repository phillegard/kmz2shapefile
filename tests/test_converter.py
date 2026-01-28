"""Tests for main converter."""

import pytest
from pathlib import Path
import zipfile

from kmz2shapefile.converter import KMZConverter
from kmz2shapefile.exceptions import ConversionError


# Sample KML templates
SIMPLE_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <Placemark>
            <name>Test Point</name>
            <Point><coordinates>-122.084075,37.4220033,0</coordinates></Point>
        </Placemark>
    </Document>
</kml>
"""

EMPTY_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document></Document>
</kml>
"""


class TestKMZConverter:
    """Tests for KMZConverter class."""

    @pytest.fixture
    def converter(self):
        return KMZConverter()

    @pytest.fixture
    def kml_file(self, tmp_path):
        """Create a simple test KML file."""
        kml_path = tmp_path / 'test.kml'
        kml_path.write_text(SIMPLE_KML, encoding='utf-8')
        return kml_path

    def _create_kmz(self, tmp_path, kml_content: str) -> Path:
        """Create a test KMZ file."""
        kmz_path = tmp_path / 'test.kmz'
        with zipfile.ZipFile(kmz_path, 'w') as zf:
            zf.writestr('doc.kml', kml_content)
        return kmz_path

    def test_convert_simple_kml(self, converter, kml_file, tmp_path):
        """Test converting simple KML file."""
        result = converter.convert(kml_file, tmp_path / 'output')
        assert len(result) == 1
        assert result[0].exists()
        assert 'point' in result[0].name

    def test_convert_kmz(self, converter, tmp_path):
        """Test converting KMZ file."""
        kmz_path = self._create_kmz(tmp_path, SIMPLE_KML)
        result = converter.convert(kmz_path, tmp_path / 'output')
        assert len(result) == 1
        assert result[0].exists()

    def test_convert_with_attributes(self, converter, tmp_path):
        """Test converting KML with HTML table attributes."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test</name>
                    <description><![CDATA[<table><tr><td>Population</td><td>10000</td></tr></table>]]></description>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = tmp_path / 'test.kml'
        kml_path.write_text(kml, encoding='utf-8')

        result = converter.convert(kml_path, tmp_path / 'output')
        assert len(result) == 1
        assert result[0].exists()

    def test_convert_mixed_geometry(self, converter, tmp_path):
        """Test converting KML with mixed geometry types."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark><name>Point</name><Point><coordinates>0,0,0</coordinates></Point></Placemark>
                <Placemark><name>Line</name><LineString><coordinates>0,0,0 1,1,0</coordinates></LineString></Placemark>
            </Document>
        </kml>
        """
        kml_path = tmp_path / 'test.kml'
        kml_path.write_text(kml, encoding='utf-8')

        result = converter.convert(kml_path, tmp_path / 'output')
        assert len(result) == 2

    def test_convert_nonexistent_file_raises_error(self, converter):
        """Test that nonexistent file raises error."""
        with pytest.raises(ConversionError, match="Input file not found"):
            converter.convert(Path('/nonexistent/file.kml'))

    def test_convert_empty_kml_raises_error(self, converter, tmp_path):
        """Test that KML with no placemarks raises error."""
        kml_path = tmp_path / 'empty.kml'
        kml_path.write_text(EMPTY_KML, encoding='utf-8')

        with pytest.raises(ConversionError, match="No Placemarks found"):
            converter.convert(kml_path)

    def test_convert_default_output_path(self, converter, kml_file):
        """Test conversion with default output path (based on input)."""
        result = converter.convert(kml_file)
        assert len(result) == 1
        assert result[0].parent == kml_file.parent

    def test_convert_verbose_mode(self, converter, kml_file, tmp_path):
        """Test conversion with verbose mode."""
        result = converter.convert(kml_file, tmp_path / 'output', verbose=True)
        assert len(result) == 1

    def test_convert_skip_null_geometry(self, converter, tmp_path):
        """Test skipping features with null geometry."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark><name>With Geometry</name><Point><coordinates>0,0,0</coordinates></Point></Placemark>
                <Placemark><name>Without Geometry</name></Placemark>
            </Document>
        </kml>
        """
        kml_path = tmp_path / 'test.kml'
        kml_path.write_text(kml, encoding='utf-8')

        result = converter.convert(kml_path, tmp_path / 'output', skip_null_geometry=True)
        assert len(result) == 1
