# KMZ to Shapefile Converter

Convert KMZ/KML files to ESRI Shapefile format with automatic attribute extraction from HTML tables in descriptions.

## Features

- **Automatic attribute parsing**: Extracts key-value pairs from HTML tables in KML `<description>` fields
- **ExtendedData support**: Also parses KML `<ExtendedData>` and `<SimpleData>` elements
- **Type coercion**: Automatically converts string values to int, float, or null
- **Geometry splitting**: Creates separate Shapefiles for Point, Line, and Polygon features
- **Field name handling**: Automatically truncates field names to Shapefile's 10-character limit with collision avoidance
- **CLI and GUI**: Both command-line and graphical interfaces available

## Installation

### Prerequisites

This project requires GDAL to be installed on your system (for the fiona library).

**macOS:**
```bash
brew install gdal
```

**Ubuntu/Debian:**
```bash
sudo apt-get install gdal-bin libgdal-dev
```

**Windows:**
Download GDAL from [OSGeo4W](https://trac.osgeo.org/osgeo4w/) or use conda.

### Install from source

```bash
# Clone the repository
cd kmz2shapefile

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Basic conversion (creates output_point.shp, output_line.shp, etc.)
kmz2shapefile input.kmz output

# Use input filename as output base
kmz2shapefile input.kmz

# Verbose mode
kmz2shapefile input.kmz output -v

# Include features with null geometry
kmz2shapefile input.kmz --include-null-geometry
```

### GUI

```bash
# Launch GUI
kmz2shapefile-gui
```

### Python API

```python
from pathlib import Path
from kmz2shapefile import KMZConverter

converter = KMZConverter()
created_files = converter.convert(
    input_path=Path("input.kmz"),
    output_path=Path("output"),  # Creates output_point.shp, etc.
    verbose=True,
    skip_null_geometry=True
)

for f in created_files:
    print(f"Created: {f}")
```

## Output Format

Since Shapefiles can only contain one geometry type per file, the converter automatically splits output by geometry type:

- `output_point.shp` - Point and MultiPoint features
- `output_line.shp` - LineString and MultiLineString features
- `output_polygon.shp` - Polygon and MultiPolygon features

Each Shapefile includes the associated files (.shx, .dbf, .prj, .cpg).

## Field Name Handling

Shapefile DBF format limits field names to 10 characters. The converter:

1. Truncates field names longer than 10 characters
2. Replaces special characters with underscores
3. Handles collisions by appending numeric suffixes

Example:
- `verylongfieldname` → `verylongfi`
- `another_long_name` → `another_lo`
- Collision: `verylongfi` → `verylonf_1`

## Supported KML Features

- **Geometry types**: Point, LineString, Polygon, MultiGeometry, LinearRing
- **Description formats**: HTML tables with `<tr><td>key</td><td>value</td></tr>` pattern
- **ExtendedData**: SimpleData and Data elements
- **Coordinate systems**: WGS84 (EPSG:4326) output

## Development

### Running tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/kmz2shapefile --cov-report=html
```

### Code formatting

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint
flake8 src/ tests/
```

### Type checking

```bash
mypy src/kmz2shapefile
```

## License

MIT License
