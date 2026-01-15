"""Tests for geometry conversion."""

import pytest
from lxml import etree
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString

from kmz2shapefile.geometry import GeometryConverter


class TestGeometryConverter:
    """Tests for GeometryConverter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = GeometryConverter()

    def test_convert_point(self):
        """Test Point conversion."""
        kml = """
        <Point xmlns="http://www.opengis.net/kml/2.2">
            <coordinates>-122.084075,37.4220033,0</coordinates>
        </Point>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, Point)
        assert result.x == pytest.approx(-122.084075)
        assert result.y == pytest.approx(37.4220033)

    def test_convert_point_no_altitude(self):
        """Test Point conversion without altitude."""
        kml = """
        <Point xmlns="http://www.opengis.net/kml/2.2">
            <coordinates>-122.084075,37.4220033</coordinates>
        </Point>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, Point)
        assert result.x == pytest.approx(-122.084075)
        assert result.y == pytest.approx(37.4220033)

    def test_convert_linestring(self):
        """Test LineString conversion."""
        kml = """
        <LineString xmlns="http://www.opengis.net/kml/2.2">
            <coordinates>
                -122.084075,37.4220033,0
                -122.085075,37.4230033,0
                -122.086075,37.4240033,0
            </coordinates>
        </LineString>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, LineString)
        assert len(result.coords) == 3

    def test_convert_polygon(self):
        """Test Polygon conversion."""
        kml = """
        <Polygon xmlns="http://www.opengis.net/kml/2.2">
            <outerBoundaryIs>
                <LinearRing>
                    <coordinates>
                        -122.084075,37.4220033,0
                        -122.085075,37.4220033,0
                        -122.085075,37.4230033,0
                        -122.084075,37.4230033,0
                        -122.084075,37.4220033,0
                    </coordinates>
                </LinearRing>
            </outerBoundaryIs>
        </Polygon>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, Polygon)
        assert result.is_valid

    def test_convert_polygon_with_hole(self):
        """Test Polygon with inner ring (hole) conversion."""
        kml = """
        <Polygon xmlns="http://www.opengis.net/kml/2.2">
            <outerBoundaryIs>
                <LinearRing>
                    <coordinates>
                        0,0,0 10,0,0 10,10,0 0,10,0 0,0,0
                    </coordinates>
                </LinearRing>
            </outerBoundaryIs>
            <innerBoundaryIs>
                <LinearRing>
                    <coordinates>
                        2,2,0 8,2,0 8,8,0 2,8,0 2,2,0
                    </coordinates>
                </LinearRing>
            </innerBoundaryIs>
        </Polygon>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, Polygon)
        assert len(result.interiors) == 1

    def test_convert_multigeometry_same_type(self):
        """Test MultiGeometry with same geometry types."""
        kml = """
        <MultiGeometry xmlns="http://www.opengis.net/kml/2.2">
            <Point>
                <coordinates>-122.084,37.422,0</coordinates>
            </Point>
            <Point>
                <coordinates>-122.085,37.423,0</coordinates>
            </Point>
        </MultiGeometry>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, MultiPoint)
        assert len(result.geoms) == 2

    def test_convert_multigeometry_linestrings(self):
        """Test MultiGeometry with LineStrings."""
        kml = """
        <MultiGeometry xmlns="http://www.opengis.net/kml/2.2">
            <LineString>
                <coordinates>0,0,0 1,1,0</coordinates>
            </LineString>
            <LineString>
                <coordinates>2,2,0 3,3,0</coordinates>
            </LineString>
        </MultiGeometry>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, MultiLineString)
        assert len(result.geoms) == 2

    def test_convert_null_element(self):
        """Test that None element returns None."""
        result = self.converter.convert(None)
        assert result is None

    def test_convert_without_namespace(self):
        """Test conversion without KML namespace."""
        kml = """
        <Point>
            <coordinates>-122.084075,37.4220033,0</coordinates>
        </Point>
        """
        element = etree.fromstring(kml)
        result = self.converter.convert(element)

        assert isinstance(result, Point)

    def test_get_geometry_type_point(self):
        """Test get_geometry_type for Point."""
        point = Point(0, 0)
        result = GeometryConverter.get_geometry_type(point)
        assert result == 'Point'

    def test_get_geometry_type_multipoint(self):
        """Test get_geometry_type for MultiPoint."""
        multipoint = MultiPoint([(0, 0), (1, 1)])
        result = GeometryConverter.get_geometry_type(multipoint)
        assert result == 'Point'

    def test_get_geometry_type_linestring(self):
        """Test get_geometry_type for LineString."""
        line = LineString([(0, 0), (1, 1)])
        result = GeometryConverter.get_geometry_type(line)
        assert result == 'LineString'

    def test_get_geometry_type_polygon(self):
        """Test get_geometry_type for Polygon."""
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        result = GeometryConverter.get_geometry_type(polygon)
        assert result == 'Polygon'
