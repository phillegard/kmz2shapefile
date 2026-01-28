"""Tests for geometry conversion."""

import pytest
from lxml import etree
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString

from kmz2shapefile.geometry import GeometryConverter


class TestGeometryConverter:
    """Tests for GeometryConverter class."""

    @pytest.fixture
    def converter(self):
        return GeometryConverter()

    def test_convert_point(self, converter):
        """Test Point conversion."""
        kml = """
        <Point xmlns="http://www.opengis.net/kml/2.2">
            <coordinates>-122.084075,37.4220033,0</coordinates>
        </Point>
        """
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, Point)
        assert result.x == pytest.approx(-122.084075)
        assert result.y == pytest.approx(37.4220033)

    def test_convert_point_no_altitude(self, converter):
        """Test Point conversion without altitude."""
        kml = """
        <Point xmlns="http://www.opengis.net/kml/2.2">
            <coordinates>-122.084075,37.4220033</coordinates>
        </Point>
        """
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, Point)
        assert result.x == pytest.approx(-122.084075)
        assert result.y == pytest.approx(37.4220033)

    def test_convert_linestring(self, converter):
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
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, LineString)
        assert len(result.coords) == 3

    def test_convert_polygon(self, converter):
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
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, Polygon)
        assert result.is_valid

    def test_convert_polygon_with_hole(self, converter):
        """Test Polygon with inner ring (hole) conversion."""
        kml = """
        <Polygon xmlns="http://www.opengis.net/kml/2.2">
            <outerBoundaryIs>
                <LinearRing>
                    <coordinates>0,0,0 10,0,0 10,10,0 0,10,0 0,0,0</coordinates>
                </LinearRing>
            </outerBoundaryIs>
            <innerBoundaryIs>
                <LinearRing>
                    <coordinates>2,2,0 8,2,0 8,8,0 2,8,0 2,2,0</coordinates>
                </LinearRing>
            </innerBoundaryIs>
        </Polygon>
        """
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, Polygon)
        assert len(result.interiors) == 1

    def test_convert_multigeometry_same_type(self, converter):
        """Test MultiGeometry with same geometry types."""
        kml = """
        <MultiGeometry xmlns="http://www.opengis.net/kml/2.2">
            <Point><coordinates>-122.084,37.422,0</coordinates></Point>
            <Point><coordinates>-122.085,37.423,0</coordinates></Point>
        </MultiGeometry>
        """
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, MultiPoint)
        assert len(result.geoms) == 2

    def test_convert_multigeometry_linestrings(self, converter):
        """Test MultiGeometry with LineStrings."""
        kml = """
        <MultiGeometry xmlns="http://www.opengis.net/kml/2.2">
            <LineString><coordinates>0,0,0 1,1,0</coordinates></LineString>
            <LineString><coordinates>2,2,0 3,3,0</coordinates></LineString>
        </MultiGeometry>
        """
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, MultiLineString)
        assert len(result.geoms) == 2

    def test_convert_null_element(self, converter):
        """Test that None element returns None."""
        assert converter.convert(None) is None

    def test_convert_without_namespace(self, converter):
        """Test conversion without KML namespace."""
        kml = "<Point><coordinates>-122.084075,37.4220033,0</coordinates></Point>"
        result = converter.convert(etree.fromstring(kml))
        assert isinstance(result, Point)


class TestGetGeometryType:
    """Tests for GeometryConverter.get_geometry_type static method."""

    def test_point(self):
        assert GeometryConverter.get_geometry_type(Point(0, 0)) == 'Point'

    def test_multipoint(self):
        assert GeometryConverter.get_geometry_type(MultiPoint([(0, 0), (1, 1)])) == 'Point'

    def test_linestring(self):
        assert GeometryConverter.get_geometry_type(LineString([(0, 0), (1, 1)])) == 'LineString'

    def test_polygon(self):
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        assert GeometryConverter.get_geometry_type(poly) == 'Polygon'
