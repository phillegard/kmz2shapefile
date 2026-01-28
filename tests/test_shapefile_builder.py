"""Tests for Shapefile building."""

import pytest
from pathlib import Path
from shapely.geometry import Point, LineString, Polygon, GeometryCollection
import fiona

from kmz2shapefile.shapefile_builder import ShapefileBuilder, Feature
from kmz2shapefile.exceptions import ShapefileWriteError


class TestShapefileBuilder:
    """Tests for ShapefileBuilder class."""

    @pytest.fixture
    def builder(self):
        return ShapefileBuilder()

    def test_build_point_shapefile(self, builder, tmp_path):
        """Test building Shapefile with Point features."""
        features = [
            Feature(geometry=Point(0, 0), properties={'value': 100}, name='Point 1'),
            Feature(geometry=Point(1, 1), properties={'value': 200}, name='Point 2'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        assert len(result) == 1
        assert result[0].name == 'test_point.shp'
        assert result[0].exists()

        with fiona.open(result[0]) as src:
            assert len(list(src)) == 2

    def test_build_line_shapefile(self, builder, tmp_path):
        """Test building Shapefile with LineString features."""
        features = [
            Feature(geometry=LineString([(0, 0), (1, 1), (2, 0)]), properties={'length': 10.5}, name='Line 1'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        assert len(result) == 1
        assert result[0].name == 'test_line.shp'

    def test_build_polygon_shapefile(self, builder, tmp_path):
        """Test building Shapefile with Polygon features."""
        features = [
            Feature(geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), properties={'area': 1.0}, name='Polygon 1'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        assert len(result) == 1
        assert result[0].name == 'test_polygon.shp'

    def test_build_mixed_geometry_types(self, builder, tmp_path):
        """Test building Shapefiles with mixed geometry types."""
        features = [
            Feature(geometry=Point(0, 0), properties={'type': 'point'}, name='Point'),
            Feature(geometry=LineString([(0, 0), (1, 1)]), properties={'type': 'line'}, name='Line'),
            Feature(geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), properties={'type': 'polygon'}, name='Polygon'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'mixed')

        assert len(result) == 3
        names = {r.name for r in result}
        assert names == {'mixed_point.shp', 'mixed_line.shp', 'mixed_polygon.shp'}

    def test_skip_null_geometry(self, builder, tmp_path):
        """Test that features with null geometry are skipped."""
        features = [
            Feature(geometry=Point(0, 0), properties={}, name='Valid'),
            Feature(geometry=None, properties={}, name='Null'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        assert len(result) == 1
        with fiona.open(result[0]) as src:
            assert len(list(src)) == 1

    def test_field_name_truncation(self, builder, tmp_path):
        """Test that long field names are truncated."""
        features = [
            Feature(geometry=Point(0, 0), properties={'verylongfieldname': 'value'}, name='Test'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        with fiona.open(result[0]) as src:
            for field_name in src.schema['properties'].keys():
                assert len(field_name) <= 10

    def test_crs_is_wgs84(self, builder, tmp_path):
        """Test that output CRS is WGS84."""
        features = [Feature(geometry=Point(-122.084, 37.422), properties={}, name='Test')]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        with fiona.open(result[0]) as src:
            assert src.crs.to_epsg() == 4326

    def test_empty_features_raises_error(self, builder, tmp_path):
        """Test that empty feature list raises error."""
        with pytest.raises(ShapefileWriteError):
            builder.build_shapefiles([], tmp_path / 'test')

    def test_all_null_geometry_raises_error(self, builder, tmp_path):
        """Test that all null geometries raises error."""
        features = [
            Feature(geometry=None, properties={}, name='Null1'),
            Feature(geometry=None, properties={}, name='Null2'),
        ]
        with pytest.raises(ShapefileWriteError):
            builder.build_shapefiles(features, tmp_path / 'test')

    def test_geometry_collection_expanded(self, builder, tmp_path):
        """Test that GeometryCollection is expanded into separate files."""
        features = [
            Feature(geometry=GeometryCollection([Point(0, 0), Point(1, 1)]), properties={'source': 'collection'}, name='Collection'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        assert len(result) == 1
        assert 'point' in result[0].name
        with fiona.open(result[0]) as src:
            assert len(list(src)) == 2

    def test_properties_preserved(self, builder, tmp_path):
        """Test that properties are preserved in output."""
        features = [
            Feature(geometry=Point(0, 0), properties={'count': 42, 'ratio': 3.14, 'label': 'test'}, name='Test Feature'),
        ]
        result = builder.build_shapefiles(features, tmp_path / 'test')

        with fiona.open(result[0]) as src:
            props = list(src)[0]['properties']
            values = list(props.values())
            assert 42 in values or '42' in values
            assert any(abs(float(v) - 3.14) < 0.01 for v in values if isinstance(v, (int, float)))
            assert 'test' in values
