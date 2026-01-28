"""Main orchestrator for KMZ to Shapefile conversion."""

from pathlib import Path
from typing import List, Optional

from .kmz_extractor import KMZExtractor
from .kml_parser import KMLParser, Placemark
from .html_parser import HTMLTableParser
from .geometry import GeometryConverter
from .shapefile_builder import ShapefileBuilder, Feature
from .exceptions import ConversionError


class KMZConverter:
    """Main orchestrator for KMZ to Shapefile conversion."""

    def __init__(self):
        self.extractor = KMZExtractor()
        self.kml_parser = KMLParser()
        self.html_parser = HTMLTableParser()
        self.geometry_converter = GeometryConverter()
        self.shapefile_builder = ShapefileBuilder()

    def convert(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        verbose: bool = False,
        skip_null_geometry: bool = True
    ) -> List[Path]:
        """
        Convert KMZ/KML to Shapefile(s).

        Pipeline:
        1. Determine if input is KMZ or KML
        2. Extract/read KML content
        3. Parse KML to Placemarks
        4. Extract attributes from descriptions
        5. Convert geometries to Shapely
        6. Build Shapefile(s) split by geometry type

        Args:
            input_path: Path to KMZ or KML file
            output_path: Optional output base path (without extension)
                        If None, uses input filename as base
            verbose: Print progress messages
            skip_null_geometry: Skip features without geometry

        Returns:
            List of created Shapefile paths

        Raises:
            ConversionError: If conversion fails
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")

        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix('')  # Remove extension

        if verbose:
            print(f"Reading: {input_path}")

        # Step 1 & 2: Get KML content
        kml_content = self._get_kml_content(input_path)

        # Step 3: Parse KML to Placemarks
        placemarks = self.kml_parser.parse(kml_content)

        if verbose:
            print(f"Found {len(placemarks)} placemark(s)")

        if not placemarks:
            raise ConversionError(
                f"No Placemarks found in {input_path}. "
                f"The file may be empty or not contain valid KML features."
            )

        # Step 4 & 5: Convert placemarks to features
        features = self._placemarks_to_features(placemarks, skip_null_geometry, verbose)

        if not features:
            raise ConversionError(
                "No features with valid geometry found. "
                "All placemarks may have null or unsupported geometries."
            )

        if verbose:
            print(f"Converted {len(features)} feature(s) with valid geometry")

        # Step 6: Build Shapefile(s)
        created_files = self.shapefile_builder.build_shapefiles(
            features,
            output_path,
            verbose=verbose
        )

        return created_files

    def _get_kml_content(self, input_path: Path) -> str:
        """
        Get KML content from KMZ or KML file.

        Args:
            input_path: Path to input file

        Returns:
            KML content as string

        Raises:
            ConversionError: If reading fails
        """
        # Check if file is KMZ (ZIP) or KML (XML)
        if self._is_kmz(input_path):
            # Extract from KMZ
            return self.extractor.extract_kml(input_path)
        else:
            # Read KML directly
            try:
                return input_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                raise ConversionError(
                    f"Failed to read {input_path} as UTF-8. "
                    f"Ensure the file is a valid KML file."
                )
            except Exception as e:
                raise ConversionError(f"Failed to read {input_path}: {e}")

    def _is_kmz(self, path: Path) -> bool:
        """
        Check if file is KMZ (ZIP) or KML (XML).

        Args:
            path: File path

        Returns:
            True if KMZ, False if KML
        """
        suffix = path.suffix.lower()
        if suffix == '.kmz':
            return True
        if suffix == '.kml':
            return False

        # Check by file signature (magic bytes) - ZIP files start with PK
        try:
            with open(path, 'rb') as f:
                return f.read(2) == b'PK'
        except Exception:
            return False

    def _placemarks_to_features(
        self,
        placemarks: List[Placemark],
        skip_null_geometry: bool,
        verbose: bool
    ) -> List[Feature]:
        """
        Convert Placemarks to Feature objects.

        Args:
            placemarks: List of parsed placemarks
            skip_null_geometry: Skip features without geometry
            verbose: Print warnings for skipped features

        Returns:
            List of Feature objects
        """
        features = []
        skipped_count = 0

        for placemark in placemarks:
            # Convert geometry
            geometry = self.geometry_converter.convert(placemark.geometry_element)

            if geometry is None and skip_null_geometry:
                skipped_count += 1
                continue

            # Extract properties from HTML description
            properties = self.html_parser.parse_attributes(placemark.description)

            # Also extract from ExtendedData if present
            extended_props = self.html_parser.parse_extended_data(placemark.extended_data)
            properties.update(extended_props)

            feature = Feature(
                geometry=geometry,
                properties=properties,
                name=placemark.name
            )
            features.append(feature)

        if verbose and skipped_count > 0:
            print(f"Skipped {skipped_count} feature(s) with null geometry")

        return features
