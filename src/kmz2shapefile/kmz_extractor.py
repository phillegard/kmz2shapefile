"""Extract KML content from KMZ archives."""

import zipfile
from pathlib import Path
from typing import Optional

from .exceptions import KMZExtractionError


class KMZExtractor:
    """Extract KML from KMZ archive (ZIP format)."""

    def extract_kml(self, kmz_path: Path) -> str:
        """
        Extract doc.kml content from KMZ file.

        Args:
            kmz_path: Path to KMZ file

        Returns:
            KML content as string

        Raises:
            KMZExtractionError: If extraction fails
        """
        if not kmz_path.exists():
            raise KMZExtractionError(f"File not found: {kmz_path}")

        try:
            with zipfile.ZipFile(kmz_path, 'r') as kmz:
                # Find doc.kml (case-insensitive)
                kml_filename = self._find_kml_file(kmz.namelist())

                if not kml_filename:
                    raise KMZExtractionError(
                        f"No KML file found in {kmz_path}. "
                        f"Available files: {', '.join(kmz.namelist())}"
                    )

                # Extract and decode
                kml_bytes = kmz.read(kml_filename)
                return kml_bytes.decode('utf-8')

        except zipfile.BadZipFile:
            raise KMZExtractionError(
                f"{kmz_path} is not a valid ZIP file. "
                f"KMZ files must be ZIP archives containing KML."
            )
        except UnicodeDecodeError as e:
            raise KMZExtractionError(
                f"Failed to decode KML content as UTF-8: {e}"
            )

    def _find_kml_file(self, filenames: list[str]) -> Optional[str]:
        """
        Find KML file in archive (case-insensitive).

        Looks for doc.kml first, then any .kml file.

        Args:
            filenames: List of filenames in archive

        Returns:
            KML filename or None if not found
        """
        # Try doc.kml first (most common)
        for name in filenames:
            if name.lower() == 'doc.kml':
                return name

        # Fall back to any .kml file
        for name in filenames:
            if name.lower().endswith('.kml'):
                return name

        return None
