"""Tests for main converter."""

import pytest
from pathlib import Path
import tempfile
import shutil
import zipfile

from kmz2shapefile.converter import KMZConverter
from kmz2shapefile.exceptions import ConversionError


class TestKMZConverter:
    """Tests for KMZConverter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = KMZConverter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_kml(self, content: str) -> Path:
        """Create a test KML file."""
        kml_path = Path(self.temp_dir) / 'test.kml'
        kml_path.write_text(content, encoding='utf-8')
        return kml_path

    def _create_test_kmz(self, kml_content: str) -> Path:
        """Create a test KMZ file."""
        kmz_path = Path(self.temp_dir) / 'test.kmz'
        with zipfile.ZipFile(kmz_path, 'w') as zf:
            zf.writestr('doc.kml', kml_content)
        return kmz_path

    def test_convert_simple_kml(self):
        """Test converting simple KML file."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test Point</name>
                    <Point>
                        <coordinates>-122.084075,37.4220033,0</coordinates>
                    </Point>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)
        output_base = Path(self.temp_dir) / 'output'

        result = self.converter.convert(kml_path, output_base)

        assert len(result) == 1
        assert result[0].exists()
        assert 'point' in result[0].name

    def test_convert_kmz(self):
        """Test converting KMZ file."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test Point</name>
                    <Point>
                        <coordinates>-122.084075,37.4220033,0</coordinates>
                    </Point>
                </Placemark>
            </Document>
        </kml>
        """
        kmz_path = self._create_test_kmz(kml)
        output_base = Path(self.temp_dir) / 'output'

        result = self.converter.convert(kmz_path, output_base)

        assert len(result) == 1
        assert result[0].exists()

    def test_convert_with_attributes(self):
        """Test converting KML with HTML table attributes."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test</name>
                    <description><![CDATA[
                        <table>
                            <tr><td>Population</td><td>10000</td></tr>
                            <tr><td>Area</td><td>5.5</td></tr>
                        </table>
                    ]]></description>
                    <Point>
                        <coordinates>0,0,0</coordinates>
                    </Point>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)
        output_base = Path(self.temp_dir) / 'output'

        result = self.converter.convert(kml_path, output_base)

        assert len(result) == 1
        assert result[0].exists()

    def test_convert_mixed_geometry(self):
        """Test converting KML with mixed geometry types."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Point</name>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
                <Placemark>
                    <name>Line</name>
                    <LineString><coordinates>0,0,0 1,1,0</coordinates></LineString>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)
        output_base = Path(self.temp_dir) / 'output'

        result = self.converter.convert(kml_path, output_base)

        # Should create 2 Shapefiles (point and line)
        assert len(result) == 2

    def test_convert_nonexistent_file_raises_error(self):
        """Test that nonexistent file raises error."""
        with pytest.raises(ConversionError, match="Input file not found"):
            self.converter.convert(Path('/nonexistent/file.kml'))

    def test_convert_empty_kml_raises_error(self):
        """Test that KML with no placemarks raises error."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)

        with pytest.raises(ConversionError, match="No Placemarks found"):
            self.converter.convert(kml_path)

    def test_convert_default_output_path(self):
        """Test conversion with default output path (based on input)."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test</name>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)

        # Don't specify output_path
        result = self.converter.convert(kml_path)

        assert len(result) == 1
        # Output should be in same directory as input
        assert result[0].parent == kml_path.parent

    def test_convert_verbose_mode(self):
        """Test conversion with verbose mode."""
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>Test</name>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)
        output_base = Path(self.temp_dir) / 'output'

        # Should not raise
        result = self.converter.convert(kml_path, output_base, verbose=True)
        assert len(result) == 1

    def test_convert_skip_null_geometry(self):
        """Test skipping features with null geometry."""
        # This KML has a placemark without geometry
        kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <Placemark>
                    <name>With Geometry</name>
                    <Point><coordinates>0,0,0</coordinates></Point>
                </Placemark>
                <Placemark>
                    <name>Without Geometry</name>
                </Placemark>
            </Document>
        </kml>
        """
        kml_path = self._create_test_kml(kml)
        output_base = Path(self.temp_dir) / 'output'

        result = self.converter.convert(
            kml_path,
            output_base,
            skip_null_geometry=True
        )

        assert len(result) == 1
