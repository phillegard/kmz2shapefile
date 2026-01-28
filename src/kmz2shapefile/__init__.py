"""KMZ to Shapefile Converter.

Convert KMZ/KML files to Shapefile with automatic attribute parsing.
"""

__version__ = "0.1.0"

from .converter import KMZConverter

__all__ = ["KMZConverter", "__version__"]
