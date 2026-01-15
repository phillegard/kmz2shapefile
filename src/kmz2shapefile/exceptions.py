"""Custom exceptions for KMZ to Shapefile conversion."""


class ConversionError(Exception):
    """Base exception for conversion errors."""
    pass


class KMZExtractionError(ConversionError):
    """Error extracting KML from KMZ."""
    pass


class KMLParseError(ConversionError):
    """Error parsing KML XML."""
    pass


class GeometryConversionError(ConversionError):
    """Error converting geometry."""
    pass


class ShapefileWriteError(ConversionError):
    """Error writing Shapefile."""
    pass


class FieldMappingError(ConversionError):
    """Error mapping field names for Shapefile."""
    pass
