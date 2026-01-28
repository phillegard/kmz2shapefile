"""Convert KML geometry to Shapely geometry."""

from typing import List, Optional, Tuple
from lxml import etree
from shapely.geometry import (
    Point,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    GeometryCollection,
)
from shapely.geometry.base import BaseGeometry

from .exceptions import GeometryConversionError


class GeometryConverter:
    """Convert KML geometry elements to Shapely geometry objects."""

    NAMESPACES = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }

    def _find_element(self, parent: etree._Element, tag: str) -> Optional[etree._Element]:
        """Find child element by tag, trying namespaced first then unnamespaced."""
        elem = parent.find(f'kml:{tag}', namespaces=self.NAMESPACES)
        return elem if elem is not None else parent.find(tag)

    def convert(self, geometry_element: Optional[etree._Element]) -> Optional[BaseGeometry]:
        """
        Convert KML geometry element to Shapely geometry.

        Supported types:
        - Point
        - LineString
        - Polygon
        - MultiGeometry
        - LinearRing

        Args:
            geometry_element: KML geometry XML element

        Returns:
            Shapely geometry object or None if conversion fails
        """
        if geometry_element is None:
            return None

        # Get tag name without namespace
        tag = geometry_element.tag
        if '}' in tag:
            tag = tag.split('}')[1]

        try:
            if tag == 'Point':
                return self._convert_point(geometry_element)
            elif tag == 'LineString':
                return self._convert_linestring(geometry_element)
            elif tag == 'Polygon':
                return self._convert_polygon(geometry_element)
            elif tag == 'MultiGeometry':
                return self._convert_multigeometry(geometry_element)
            elif tag == 'LinearRing':
                # LinearRing is like LineString
                return self._convert_linestring(geometry_element)
            else:
                # Unsupported geometry type
                return None

        except Exception:
            # If conversion fails, return None (graceful degradation)
            return None

    def _parse_coordinates(self, coord_text: str) -> List[Tuple[float, float]]:
        """
        Parse KML coordinate string to list of (lon, lat) tuples.

        Note: Shapefile format only supports 2D coordinates, so altitude is dropped.

        KML format: "lon,lat,alt lon,lat,alt ..."
        Output format: [(lon, lat), (lon, lat), ...]

        Args:
            coord_text: KML coordinate string

        Returns:
            List of (lon, lat) coordinate tuples

        Raises:
            GeometryConversionError: If coordinate parsing fails
        """
        if not coord_text:
            raise GeometryConversionError("Empty coordinate string")

        coordinates = []

        # Split by whitespace to get individual coordinate tuples
        coord_tuples = coord_text.strip().split()

        for coord_tuple in coord_tuples:
            if not coord_tuple:
                continue

            # Split by comma to get lon, lat, alt
            parts = coord_tuple.split(',')

            if len(parts) < 2:
                # Invalid coordinate format
                continue

            try:
                lon = float(parts[0])
                lat = float(parts[1])
                # Altitude is ignored for Shapefile (2D only)

                coordinates.append((lon, lat))
            except (ValueError, IndexError):
                # Skip invalid coordinates
                continue

        if not coordinates:
            raise GeometryConversionError("No valid coordinates found")

        return coordinates

    def _convert_point(self, element: etree._Element) -> Point:
        """
        Convert Point to Shapely Point.

        Args:
            element: Point XML element

        Returns:
            Shapely Point geometry
        """
        coord_elem = self._find_element(element, 'coordinates')
        if coord_elem is None or not coord_elem.text:
            raise GeometryConversionError("Point has no coordinates")

        coordinates = self._parse_coordinates(coord_elem.text)
        if not coordinates:
            raise GeometryConversionError("Point has invalid coordinates")

        return Point(coordinates[0])

    def _convert_linestring(self, element: etree._Element) -> LineString:
        """
        Convert LineString to Shapely LineString.

        Args:
            element: LineString XML element

        Returns:
            Shapely LineString geometry
        """
        coord_elem = self._find_element(element, 'coordinates')
        if coord_elem is None or not coord_elem.text:
            raise GeometryConversionError("LineString has no coordinates")

        return LineString(self._parse_coordinates(coord_elem.text))

    def _convert_polygon(self, element: etree._Element) -> Polygon:
        """
        Convert Polygon to Shapely Polygon.

        Handles outer boundary and inner boundaries (holes).

        Args:
            element: Polygon XML element

        Returns:
            Shapely Polygon geometry
        """
        outer_boundary = self._find_element(element, 'outerBoundaryIs')
        if outer_boundary is None:
            raise GeometryConversionError("Polygon has no outer boundary")

        linear_ring = self._find_element(outer_boundary, 'LinearRing')
        if linear_ring is None:
            raise GeometryConversionError("Outer boundary has no LinearRing")

        coord_elem = self._find_element(linear_ring, 'coordinates')
        if coord_elem is None or not coord_elem.text:
            raise GeometryConversionError("Polygon has no coordinates")

        outer_coords = self._parse_coordinates(coord_elem.text)

        # Find inner boundaries (holes)
        holes = []
        inner_boundaries = element.findall('kml:innerBoundaryIs', namespaces=self.NAMESPACES)
        if not inner_boundaries:
            inner_boundaries = element.findall('innerBoundaryIs')

        for inner_boundary in inner_boundaries:
            linear_ring = self._find_element(inner_boundary, 'LinearRing')
            if linear_ring is not None:
                coord_elem = self._find_element(linear_ring, 'coordinates')
                if coord_elem is not None and coord_elem.text:
                    holes.append(self._parse_coordinates(coord_elem.text))

        return Polygon(outer_coords, holes) if holes else Polygon(outer_coords)

    def _convert_multigeometry(self, element: etree._Element) -> BaseGeometry:
        """
        Convert MultiGeometry to appropriate Shapely type.

        If all child geometries are the same type, converts to Multi* format
        (MultiPoint, MultiLineString, MultiPolygon). Otherwise, returns
        GeometryCollection.

        Args:
            element: MultiGeometry XML element

        Returns:
            Shapely Multi* geometry or GeometryCollection
        """
        geometries = []
        geometry_types = set()

        # Get all child elements
        for child in element:
            # Skip non-geometry children
            tag = child.tag
            if '}' in tag:
                tag = tag.split('}')[1]

            if tag in ['Point', 'LineString', 'Polygon', 'MultiGeometry', 'LinearRing']:
                geom = self.convert(child)
                if geom is not None:
                    geometries.append(geom)
                    geometry_types.add(geom.geom_type)

        if not geometries:
            raise GeometryConversionError("MultiGeometry has no valid geometries")

        # If all geometries are the same type, convert to Multi* format
        if len(geometry_types) == 1:
            geom_type = list(geometry_types)[0]

            if geom_type == 'LineString':
                return MultiLineString(geometries)
            elif geom_type == 'Point':
                return MultiPoint(geometries)
            elif geom_type == 'Polygon':
                return MultiPolygon(geometries)

        # Mixed types or nested collections - use GeometryCollection
        return GeometryCollection(geometries)

    @staticmethod
    def get_geometry_type(geometry: BaseGeometry) -> str:
        """
        Get the base geometry type for Shapefile classification.

        Maps Shapely geometry types to Shapefile-compatible types:
        - Point, MultiPoint -> 'Point'
        - LineString, MultiLineString -> 'LineString'
        - Polygon, MultiPolygon -> 'Polygon'
        - GeometryCollection -> 'GeometryCollection' (needs special handling)

        Args:
            geometry: Shapely geometry object

        Returns:
            Base geometry type string
        """
        geom_type = geometry.geom_type

        if geom_type in ('Point', 'MultiPoint'):
            return 'Point'
        elif geom_type in ('LineString', 'LinearRing', 'MultiLineString'):
            return 'LineString'
        elif geom_type in ('Polygon', 'MultiPolygon'):
            return 'Polygon'
        else:
            return 'GeometryCollection'
