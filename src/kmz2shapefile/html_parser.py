"""Parse HTML tables from KML descriptions to extract attributes."""

from typing import Any, Dict, Optional, Union
from bs4 import BeautifulSoup
from lxml import etree


def _get_local_name(elem: etree._Element) -> Optional[str]:
    """Get the local name of an XML element without namespace prefix."""
    return etree.QName(elem.tag).localname if isinstance(elem.tag, str) else None


class HTMLTableParser:
    """Extract attributes from HTML tables in KML descriptions."""

    def parse_attributes(self, html_description: Optional[str]) -> Dict[str, Any]:
        """
        Parse HTML table into key-value dictionary.

        Extracts attributes from HTML tables in the format:
        <tr><td>key</td><td>value</td></tr>

        Args:
            html_description: HTML string from KML description

        Returns:
            Dictionary of attributes {key: value}
            Returns empty dict if no table found or description is None
        """
        if not html_description:
            return {}

        try:
            soup = BeautifulSoup(html_description, 'html.parser')

            # Find all table rows
            rows = soup.find_all('tr')
            if not rows:
                return {}

            attributes = {}

            for row in rows:
                # Try to get key from <th> or first <td>
                th = row.find('th')
                tds = row.find_all('td')

                if th and len(tds) == 1:
                    # Format: <th>key</th><td>value</td>
                    key = th.get_text(strip=True)
                    value_text = tds[0].get_text(strip=True)
                elif len(tds) == 2:
                    # Format: <td>key</td><td>value</td>
                    key = tds[0].get_text(strip=True)
                    value_text = tds[1].get_text(strip=True)
                else:
                    continue

                # Skip empty keys
                if not key:
                    continue

                # Coerce value to appropriate type
                value = self._coerce_type(value_text)

                attributes[key] = value

            return attributes

        except Exception:
            # If HTML parsing fails for any reason, return empty dict
            # This ensures graceful degradation
            return {}

    def _coerce_type(self, value: str) -> Union[str, int, float, None]:
        """
        Attempt to convert string to appropriate type.

        Rules:
        - "<Null>" or empty → None
        - Pure digits → int
        - Float pattern → float
        - Otherwise → string (stripped)

        Args:
            value: String value to coerce

        Returns:
            Coerced value
        """
        if not value or value == '<Null>':
            return None

        # Check for int (no decimal point, only digits with optional leading minus)
        if '.' not in value and value.lstrip('-').isdigit():
            return int(value)

        # Check for float (has decimal point)
        if '.' in value:
            try:
                return float(value)
            except ValueError:
                pass

        return value

    def parse_extended_data(self, extended_data: Optional[etree._Element]) -> Dict[str, Any]:
        """
        Parse ExtendedData/SimpleData into attributes dict.

        Handles:
        - SimpleData elements (with name attribute)
        - Data elements with value children

        Args:
            extended_data: ExtendedData XML element from lxml

        Returns:
            Dictionary of attributes {name: value}
        """
        if extended_data is None:
            return {}

        attributes = {}

        try:
            for elem in extended_data.iter():
                local_name = _get_local_name(elem)

                if local_name == 'SimpleData':
                    name = elem.get('name')
                    if name and elem.text:
                        attributes[name] = self._coerce_type(elem.text.strip())

                elif local_name == 'Data':
                    name = elem.get('name')
                    value_elem = next(
                        (child for child in elem if _get_local_name(child) == 'value'),
                        None
                    )
                    if name and value_elem is not None and value_elem.text:
                        attributes[name] = self._coerce_type(value_elem.text.strip())

        except Exception:
            pass

        return attributes
