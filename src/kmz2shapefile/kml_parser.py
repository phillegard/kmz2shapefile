"""Parse KML XML and extract Placemarks."""

from dataclasses import dataclass
from typing import List, Optional
from lxml import etree

from .exceptions import KMLParseError


@dataclass
class Placemark:
    """Represents a KML Placemark."""
    name: str
    description: Optional[str]
    geometry_element: Optional[etree._Element]
    style_url: Optional[str]
    extended_data: Optional[etree._Element] = None


class KMLParser:
    """Parse KML XML and extract Placemarks."""

    NAMESPACES = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }

    def _find_element(self, parent: etree._Element, tag: str) -> Optional[etree._Element]:
        """Find child element by tag, trying namespaced first then unnamespaced."""
        elem = parent.find(f'kml:{tag}', namespaces=self.NAMESPACES)
        return elem if elem is not None else parent.find(tag)

    def parse(self, kml_content: str) -> List[Placemark]:
        """
        Parse KML and extract all Placemarks.

        Args:
            kml_content: KML XML string

        Returns:
            List of Placemark objects

        Raises:
            KMLParseError: If XML parsing fails
        """
        try:
            root = etree.fromstring(kml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            raise KMLParseError(f"Invalid KML XML: {e}")

        # Find all Placemarks using XPath
        placemarks = root.xpath('//kml:Placemark', namespaces=self.NAMESPACES)

        if not placemarks:
            # Try without namespace (some KML files may not use namespaces properly)
            placemarks = root.xpath('//Placemark')

        result = []
        for placemark_elem in placemarks:
            placemark = self._extract_placemark(placemark_elem)
            if placemark:
                result.append(placemark)

        return result

    def _extract_placemark(self, element: etree._Element) -> Optional[Placemark]:
        """
        Extract Placemark data from XML element.

        Args:
            element: Placemark XML element

        Returns:
            Placemark object or None if extraction fails
        """
        try:
            name_elem = self._find_element(element, 'name')
            name = name_elem.text if name_elem is not None and name_elem.text else "Unnamed"

            desc_elem = self._find_element(element, 'description')
            description = desc_elem.text if desc_elem is not None else None

            style_elem = self._find_element(element, 'styleUrl')
            style_url = style_elem.text if style_elem is not None else None

            return Placemark(
                name=name,
                description=description,
                geometry_element=self._extract_geometry_element(element),
                style_url=style_url,
                extended_data=self._find_element(element, 'ExtendedData')
            )

        except Exception:
            # Graceful degradation: skip malformed placemarks
            return None

    def _extract_geometry_element(self, placemark: etree._Element) -> Optional[etree._Element]:
        """
        Find geometry element in Placemark.

        Priority order: MultiGeometry, LineString, Polygon, Point, LinearRing

        Args:
            placemark: Placemark XML element

        Returns:
            Geometry element or None if not found
        """
        for geom_type in ('MultiGeometry', 'LineString', 'Polygon', 'Point', 'LinearRing'):
            elem = self._find_element(placemark, geom_type)
            if elem is not None:
                return elem
        return None
