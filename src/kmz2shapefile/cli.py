"""Command-line interface for KMZ to Shapefile converter."""

import sys
from pathlib import Path

import click

from .converter import KMZConverter
from .exceptions import ConversionError


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_base', type=click.Path(path_type=Path), required=False)
@click.option(
    '--include-null-geometry',
    is_flag=True,
    help='Include features with null geometry (creates features without geometry)'
)
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.version_option(version='0.1.0')
def main(input_file, output_base, include_null_geometry, verbose):
    """
    Convert KMZ/KML files to ESRI Shapefile format.

    Automatically parses HTML table attributes from descriptions.
    Splits output by geometry type (Point, Line, Polygon).

    Examples:

        \b
        # Basic conversion (creates input_point.shp, input_line.shp, etc.)
        kmz2shapefile input.kmz

        \b
        # Specify output base name
        kmz2shapefile input.kmz output

        \b
        # Verbose mode
        kmz2shapefile input.kmz -v

        \b
        # Include features with null geometry
        kmz2shapefile input.kmz --include-null-geometry
    """
    try:
        converter = KMZConverter()

        # Convert
        created_files = converter.convert(
            input_path=input_file,
            output_path=output_base,
            verbose=verbose,
            skip_null_geometry=not include_null_geometry
        )

        # Report results
        if verbose:
            click.echo(f"\nCreated {len(created_files)} Shapefile(s):", err=True)
            for f in created_files:
                click.echo(f"  - {f}", err=True)
        else:
            for f in created_files:
                click.echo(str(f))

    except ConversionError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nAborted", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
