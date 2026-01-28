"""Custom exceptions for KMZ to Shapefile conversion."""


class ConversionError(Exception):
    """Base exception for conversion errors."""


class KMZExtractionError(ConversionError):
    """Error extracting KML from KMZ."""


class KMLParseError(ConversionError):
    """Error parsing KML XML."""


class GeometryConversionError(ConversionError):
    """Error converting geometry."""


class ShapefileWriteError(ConversionError):
    """Error writing Shapefile."""


class FieldMappingError(ConversionError):
    """Error mapping field names for Shapefile."""
