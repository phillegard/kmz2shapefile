"""Tests for Shapefile building."""

import pytest
from pathlib import Path
from shapely.geometry import Point, LineString, Polygon, GeometryCollection
import fiona
import tempfile
import shutil

from kmz2shapefile.shapefile_builder import ShapefileBuilder, Feature
from kmz2shapefile.exceptions import ShapefileWriteError


class TestShapefileBuilder:
    """Tests for ShapefileBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = ShapefileBuilder()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_output_base(self, name: str) -> Path:
        """Get output base path in temp directory."""
        return Path(self.temp_dir) / name

    def test_build_point_shapefile(self):
        """Test building Shapefile with Point features."""
        features = [
            Feature(
                geometry=Point(0, 0),
                properties={'value': 100},
                name='Point 1'
            ),
            Feature(
                geometry=Point(1, 1),
                properties={'value': 200},
                name='Point 2'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        assert len(result) == 1
        assert result[0].name == 'test_point.shp'
        assert result[0].exists()

        # Verify contents
        with fiona.open(result[0]) as src:
            records = list(src)
            assert len(records) == 2

    def test_build_line_shapefile(self):
        """Test building Shapefile with LineString features."""
        features = [
            Feature(
                geometry=LineString([(0, 0), (1, 1), (2, 0)]),
                properties={'length': 10.5},
                name='Line 1'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        assert len(result) == 1
        assert result[0].name == 'test_line.shp'

    def test_build_polygon_shapefile(self):
        """Test building Shapefile with Polygon features."""
        features = [
            Feature(
                geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
                properties={'area': 1.0},
                name='Polygon 1'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        assert len(result) == 1
        assert result[0].name == 'test_polygon.shp'

    def test_build_mixed_geometry_types(self):
        """Test building Shapefiles with mixed geometry types."""
        features = [
            Feature(
                geometry=Point(0, 0),
                properties={'type': 'point'},
                name='Point'
            ),
            Feature(
                geometry=LineString([(0, 0), (1, 1)]),
                properties={'type': 'line'},
                name='Line'
            ),
            Feature(
                geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
                properties={'type': 'polygon'},
                name='Polygon'
            ),
        ]

        output_base = self._get_output_base('mixed')
        result = self.builder.build_shapefiles(features, output_base)

        # Should create 3 separate Shapefiles
        assert len(result) == 3

        names = {r.name for r in result}
        assert 'mixed_point.shp' in names
        assert 'mixed_line.shp' in names
        assert 'mixed_polygon.shp' in names

    def test_skip_null_geometry(self):
        """Test that features with null geometry are skipped."""
        features = [
            Feature(
                geometry=Point(0, 0),
                properties={},
                name='Valid'
            ),
            Feature(
                geometry=None,
                properties={},
                name='Null'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        assert len(result) == 1

        with fiona.open(result[0]) as src:
            records = list(src)
            assert len(records) == 1

    def test_field_name_truncation(self):
        """Test that long field names are truncated."""
        features = [
            Feature(
                geometry=Point(0, 0),
                properties={'verylongfieldname': 'value'},
                name='Test'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        with fiona.open(result[0]) as src:
            schema = src.schema
            # All field names should be <= 10 chars
            for field_name in schema['properties'].keys():
                assert len(field_name) <= 10

    def test_crs_is_wgs84(self):
        """Test that output CRS is WGS84."""
        features = [
            Feature(
                geometry=Point(-122.084, 37.422),
                properties={},
                name='Test'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        with fiona.open(result[0]) as src:
            crs = src.crs
            # Should be WGS84 (EPSG:4326)
            assert crs.to_epsg() == 4326

    def test_empty_features_raises_error(self):
        """Test that empty feature list raises error."""
        with pytest.raises(ShapefileWriteError):
            self.builder.build_shapefiles([], self._get_output_base('test'))

    def test_all_null_geometry_raises_error(self):
        """Test that all null geometries raises error."""
        features = [
            Feature(geometry=None, properties={}, name='Null1'),
            Feature(geometry=None, properties={}, name='Null2'),
        ]

        with pytest.raises(ShapefileWriteError):
            self.builder.build_shapefiles(features, self._get_output_base('test'))

    def test_geometry_collection_expanded(self):
        """Test that GeometryCollection is expanded into separate files."""
        features = [
            Feature(
                geometry=GeometryCollection([Point(0, 0), Point(1, 1)]),
                properties={'source': 'collection'},
                name='Collection'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        # Should create point Shapefile with expanded geometries
        assert len(result) == 1
        assert 'point' in result[0].name

        with fiona.open(result[0]) as src:
            records = list(src)
            # Should have 2 records (one per point in collection)
            assert len(records) == 2

    def test_properties_preserved(self):
        """Test that properties are preserved in output."""
        features = [
            Feature(
                geometry=Point(0, 0),
                properties={'count': 42, 'ratio': 3.14, 'label': 'test'},
                name='Test Feature'
            ),
        ]

        output_base = self._get_output_base('test')
        result = self.builder.build_shapefiles(features, output_base)

        with fiona.open(result[0]) as src:
            record = list(src)[0]
            props = record['properties']

            # Values should be preserved (may be truncated field names)
            values = list(props.values())
            assert 42 in values or '42' in values
            assert any(abs(float(v) - 3.14) < 0.01 for v in values if isinstance(v, (int, float)))
            assert 'test' in values
