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
            # Extract name
            name_elem = element.find('kml:name', namespaces=self.NAMESPACES)
            if name_elem is None:
                name_elem = element.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else "Unnamed"

            # Extract description
            desc_elem = element.find('kml:description', namespaces=self.NAMESPACES)
            if desc_elem is None:
                desc_elem = element.find('description')
            description = desc_elem.text if desc_elem is not None else None

            # Extract geometry element
            geometry_element = self._extract_geometry_element(element)

            # Extract style URL
            style_elem = element.find('kml:styleUrl', namespaces=self.NAMESPACES)
            if style_elem is None:
                style_elem = element.find('styleUrl')
            style_url = style_elem.text if style_elem is not None else None

            # Extract ExtendedData element
            ext_data_elem = element.find('kml:ExtendedData', namespaces=self.NAMESPACES)
            if ext_data_elem is None:
                ext_data_elem = element.find('ExtendedData')

            return Placemark(
                name=name,
                description=description,
                geometry_element=geometry_element,
                style_url=style_url,
                extended_data=ext_data_elem
            )

        except Exception:
            # Log warning but don't fail entire parse
            return None

    def _extract_geometry_element(self, placemark: etree._Element) -> Optional[etree._Element]:
        """
        Find geometry element in Placemark.

        Priority order:
        1. MultiGeometry (contains multiple geometry types)
        2. LineString
        3. Polygon
        4. Point
        5. LinearRing

        Args:
            placemark: Placemark XML element

        Returns:
            Geometry element or None if not found
        """
        geometry_types = [
            'MultiGeometry',
            'LineString',
            'Polygon',
            'Point',
            'LinearRing'
        ]

        for geom_type in geometry_types:
            # Try with namespace
            elem = placemark.find(f'kml:{geom_type}', namespaces=self.NAMESPACES)
            if elem is not None:
                return elem

            # Try without namespace
            elem = placemark.find(geom_type)
            if elem is not None:
                return elem

        return None
