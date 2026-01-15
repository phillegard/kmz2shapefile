# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that converts KMZ/KML files to ESRI Shapefile format. The unique challenge it solves is parsing feature attributes from HTML tables embedded in KML `<description>` fields, which standard converters ignore.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run the CLI tool
kmz2shapefile input.kmz output
kmz2shapefile input.kmz output -v  # verbose mode
kmz2shapefile input.kmz            # uses input name as output base

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/kmz2shapefile
```

## Architecture

### Conversion Pipeline

The conversion follows a linear pipeline orchestrated by `KMZConverter`:

```
KMZ/KML Input
    ↓
[KMZExtractor] → Extract doc.kml from ZIP (if KMZ)
    ↓
[KMLParser] → Parse XML to Placemark objects
    ↓
[For each Placemark]:
    ├─ [HTMLTableParser] → Extract attributes from HTML table
    ├─ [GeometryConverter] → Convert KML geometry to Shapely
    └─ Create Feature object
    ↓
[ShapefileBuilder] → Group by geometry type, write Shapefile(s)
    ├─ [FieldMapper] → Truncate field names to 10 chars
    └─ [fiona] → Write .shp, .shx, .dbf, .prj files
    ↓
Shapefile(s) Output (split by geometry type)
```

### Module Responsibilities

All source code is in `src/kmz2shapefile/`:

- **converter.py**: Main orchestrator, file I/O, format detection
- **kmz_extractor.py**: ZIP extraction (KMZ → KML)
- **kml_parser.py**: XML parsing with namespace handling, extracts Placemarks
- **html_parser.py**: Parses HTML tables from `<description>` → dict with type coercion
- **geometry.py**: KML coordinates → Shapely geometry (Point, LineString, Polygon, Multi*)
- **shapefile_builder.py**: Groups features by geometry type, writes Shapefiles via fiona
- **field_mapper.py**: Truncates field names to 10 chars with collision handling
- **cli.py**: Click-based CLI interface
- **gui.py**: Tkinter GUI application

### Key Data Structures

**Placemark** (src/kmz2shapefile/kml_parser.py):
```python
@dataclass
class Placemark:
    name: str
    description: Optional[str]  # HTML content with table
    geometry_element: Optional[etree._Element]  # lxml element
    style_url: Optional[str]
    extended_data: Optional[etree._Element] = None
```

**Feature** (src/kmz2shapefile/shapefile_builder.py):
```python
@dataclass
class Feature:
    geometry: Optional[BaseGeometry]  # Shapely geometry
    properties: Dict[str, Any]
    name: str
```

### Critical Implementation Details

**Field Name Truncation** (src/kmz2shapefile/field_mapper.py):
- Shapefile DBF format limits field names to 10 characters
- Truncates and handles collisions by appending `_1`, `_2`, etc.
- Replaces special characters with underscores

**Geometry Splitting** (src/kmz2shapefile/shapefile_builder.py):
- Shapefiles can only contain one geometry type per file
- Automatically splits output into `*_point.shp`, `*_line.shp`, `*_polygon.shp`
- GeometryCollections are expanded into individual geometries

**Coordinate Handling** (src/kmz2shapefile/geometry.py):
- KML format: `"lon,lat,alt lon,lat,alt"` (space-separated)
- Output: 2D coordinates only (Shapefile limitation)
- CRS: WGS84 (EPSG:4326)

**HTML Table Parsing** (src/kmz2shapefile/html_parser.py):
- Uses BeautifulSoup to handle potentially malformed HTML in CDATA sections
- Extracts `<tr><td>key</td><td>value</td></tr>` patterns
- Type coercion: "123" → int, "123.45" → float, "<Null>" → None, else string

**KML Namespace Handling** (src/kmz2shapefile/kml_parser.py, geometry.py):
- KML uses namespaces: `http://www.opengis.net/kml/2.2`
- Both namespaced and non-namespaced parsing attempted for compatibility

## Testing the Tool

```bash
# Convert and verify output
kmz2shapefile input.kmz output -v

# Check output files exist
ls -la output_*.shp output_*.dbf output_*.prj

# Verify with ogrinfo
ogrinfo output_point.shp -al

# Load in QGIS or ArcGIS for visual verification
```

## Common Extension Points

- **New geometry types**: Add handler in `src/kmz2shapefile/geometry.py` `convert()` method
- **Different description formats**: Extend `src/kmz2shapefile/html_parser.py` to handle non-table formats
- **Custom field mapping**: Modify `src/kmz2shapefile/field_mapper.py` for different truncation strategies
- **Error handling**: Use custom exceptions from `src/kmz2shapefile/exceptions.py`

## Dependencies

- **fiona**: OGR-based library for reading/writing Shapefiles (requires GDAL)
- **shapely**: Geometry operations
- **lxml**: XML parsing
- **beautifulsoup4**: HTML parsing
- **click**: CLI framework
