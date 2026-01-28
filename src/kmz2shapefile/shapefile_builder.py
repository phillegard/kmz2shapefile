"""Build and write Shapefile from features."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import fiona
from fiona.crs import CRS
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

from .field_mapper import FieldMapper
from .geometry import GeometryConverter
from .exceptions import ShapefileWriteError


# WGS84 CRS definition
WGS84_CRS = CRS.from_epsg(4326)


@dataclass
class Feature:
    """Represents a feature with geometry and properties."""
    geometry: Optional[BaseGeometry]
    properties: Dict[str, Any]
    name: str


class ShapefileBuilder:
    """Build and write Shapefile from features."""

    def __init__(self):
        self.field_mapper = FieldMapper()

    def build_shapefiles(
        self,
        features: List[Feature],
        output_base: Path,
        verbose: bool = False
    ) -> List[Path]:
        """
        Write features to Shapefile(s), split by geometry type.

        Args:
            features: List of Feature objects
            output_base: Base output path (without extension)
                        e.g., '/path/to/output' creates
                        '/path/to/output_point.shp', etc.
            verbose: Print progress messages

        Returns:
            List of created Shapefile paths

        Raises:
            ShapefileWriteError: If writing fails
        """
        # Group features by geometry type
        grouped = self._group_by_geometry_type(features)

        if not grouped:
            raise ShapefileWriteError("No features with valid geometry to write")

        created_files = []

        for geom_type, type_features in grouped.items():
            output_path = self._get_output_path(output_base, geom_type)

            if verbose:
                print(f"Writing {len(type_features)} {geom_type} features to {output_path}")

            try:
                self._write_shapefile(type_features, output_path, geom_type)
                created_files.append(output_path)
            except Exception as e:
                raise ShapefileWriteError(
                    f"Failed to write Shapefile {output_path}: {e}"
                )

        return created_files

    def _group_by_geometry_type(
        self,
        features: List[Feature]
    ) -> Dict[str, List[Feature]]:
        """
        Group features by base geometry type.

        Args:
            features: List of features

        Returns:
            Dictionary mapping geometry type to feature list
        """
        grouped: Dict[str, List[Feature]] = {}

        for feature in features:
            if feature.geometry is None:
                continue

            geom_type = GeometryConverter.get_geometry_type(feature.geometry)

            if geom_type == 'GeometryCollection':
                # Expand GeometryCollection into individual geometries
                self._expand_geometry_collection(feature, grouped)
            else:
                grouped.setdefault(geom_type, []).append(feature)

        return grouped

    def _expand_geometry_collection(
        self,
        feature: Feature,
        grouped: Dict[str, List[Feature]]
    ):
        """
        Expand a GeometryCollection into individual features by geometry type.

        Args:
            feature: Feature with GeometryCollection
            grouped: Dictionary to add expanded features to
        """
        from shapely.geometry import GeometryCollection

        if not isinstance(feature.geometry, GeometryCollection):
            return

        num_geoms = len(feature.geometry.geoms)
        for i, geom in enumerate(feature.geometry.geoms):
            geom_type = GeometryConverter.get_geometry_type(geom)
            sub_name = f"{feature.name}_{i}" if num_geoms > 1 else feature.name

            if geom_type == 'GeometryCollection':
                # Recursively expand nested collections
                sub_feature = Feature(
                    geometry=geom,
                    properties=feature.properties.copy(),
                    name=sub_name
                )
                self._expand_geometry_collection(sub_feature, grouped)
            else:
                new_feature = Feature(
                    geometry=geom,
                    properties=feature.properties.copy(),
                    name=sub_name
                )
                grouped.setdefault(geom_type, []).append(new_feature)

    def _get_output_path(self, output_base: Path, geom_type: str) -> Path:
        """
        Get output path for specific geometry type.

        Args:
            output_base: Base output path
            geom_type: Geometry type ('Point', 'LineString', 'Polygon')

        Returns:
            Path with geometry type suffix
        """
        suffix_map = {
            'Point': 'point',
            'LineString': 'line',
            'Polygon': 'polygon',
        }
        suffix = suffix_map.get(geom_type, geom_type.lower())
        return output_base.parent / f"{output_base.name}_{suffix}.shp"

    def _write_shapefile(
        self,
        features: List[Feature],
        output_path: Path,
        geom_type: str
    ):
        """
        Write features to a single Shapefile.

        Args:
            features: List of features (all same geometry type)
            output_path: Output Shapefile path
            geom_type: Geometry type for this file
        """
        # Collect all property names
        all_props = set()
        for feature in features:
            all_props.update(feature.properties.keys())
            all_props.add('name')  # Always include name

        # Create field name mapping
        prop_list = sorted(all_props)
        field_mapping = self.field_mapper.map_field_names(prop_list)

        # Build schema
        schema = self._build_schema(features, field_mapping, geom_type)

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write Shapefile
        with fiona.open(
            output_path,
            'w',
            driver='ESRI Shapefile',
            crs=WGS84_CRS,
            schema=schema
        ) as dst:
            for feature in features:
                record = self._feature_to_record(feature, field_mapping, schema)
                dst.write(record)

    def _build_schema(
        self,
        features: List[Feature],
        field_mapping: Dict[str, str],
        geom_type: str
    ) -> Dict:
        """
        Build fiona schema for Shapefile.

        Args:
            features: List of features to analyze for field types
            field_mapping: Original to truncated field name mapping
            geom_type: Geometry type

        Returns:
            Fiona schema dictionary
        """
        properties = {
            short_name: self._infer_field_type(features, original_name)
            for original_name, short_name in field_mapping.items()
        }

        return {
            'geometry': geom_type,
            'properties': properties
        }

    def _infer_field_type(
        self,
        features: List[Feature],
        field_name: str
    ) -> str:
        """
        Infer fiona field type from feature values.

        Args:
            features: List of features
            field_name: Field name to check

        Returns:
            Fiona field type string
        """
        has_int = False
        has_float = False
        has_str = False
        max_str_len = 80

        for feature in features:
            if field_name == 'name':
                value = feature.name
            else:
                value = feature.properties.get(field_name)

            if value is None:
                continue

            if isinstance(value, bool):
                has_str = True
                max_str_len = max(max_str_len, 5)  # 'True' or 'False'
            elif isinstance(value, int):
                has_int = True
            elif isinstance(value, float):
                has_float = True
            elif isinstance(value, str):
                has_str = True
                max_str_len = max(max_str_len, len(value))

        # Determine type (string is most flexible)
        if has_str:
            return f'str:{min(max_str_len + 10, 254)}'
        elif has_float:
            return 'float'
        elif has_int:
            return 'int'
        else:
            return 'str:80'

    def _feature_to_record(
        self,
        feature: Feature,
        field_mapping: Dict[str, str],
        schema: Dict
    ) -> Dict:
        """
        Convert feature to fiona record.

        Args:
            feature: Feature to convert
            field_mapping: Field name mapping
            schema: Shapefile schema

        Returns:
            Fiona record dictionary
        """
        properties = {}

        for original_name, short_name in field_mapping.items():
            if original_name == 'name':
                value = feature.name
            else:
                value = feature.properties.get(original_name)

            # Convert value to appropriate type
            properties[short_name] = self._convert_value(value, schema['properties'][short_name])

        return {
            'geometry': mapping(feature.geometry),
            'properties': properties
        }

    def _convert_value(self, value: Any, field_type: str) -> Any:
        """
        Convert value to match field type.

        Args:
            value: Original value
            field_type: Target fiona field type

        Returns:
            Converted value
        """
        if value is None:
            return None

        if field_type.startswith('str'):
            return str(value)
        elif field_type == 'int':
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        elif field_type == 'float':
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        return value
