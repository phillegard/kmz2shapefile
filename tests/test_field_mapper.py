"""Tests for field name mapping."""

import pytest

from kmz2shapefile.field_mapper import FieldMapper


class TestFieldMapper:
    """Tests for FieldMapper class."""

    def test_short_names_unchanged(self):
        """Short names that are already valid should remain unchanged."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names(['name', 'type', 'id'])

        assert mapping['name'] == 'name'
        assert mapping['type'] == 'type'
        assert mapping['id'] == 'id'

    def test_long_names_truncated(self):
        """Names longer than 10 chars should be truncated."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names(['verylongfieldname'])

        assert len(mapping['verylongfieldname']) <= 10

    def test_collision_handling(self):
        """Names that truncate to same value should get unique suffixes."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names([
            'verylongfield1',
            'verylongfield2',
            'verylongfield3'
        ])

        # All mapped names should be unique
        mapped_values = list(mapping.values())
        assert len(mapped_values) == len(set(mapped_values))

    def test_special_characters_cleaned(self):
        """Special characters should be replaced with underscore."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names(['field-name', 'field.name', 'field name'])

        # Should contain only alphanumeric and underscore
        for mapped_name in mapping.values():
            assert all(c.isalnum() or c == '_' for c in mapped_name)

    def test_starts_with_letter_or_underscore(self):
        """Names should start with letter or underscore."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names(['123field', '456data'])

        for mapped_name in mapping.values():
            assert mapped_name[0].isalpha() or mapped_name[0] == '_'

    def test_empty_name_handled(self):
        """Empty names should be handled gracefully."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names(['', 'validname'])

        # Should have two mapped names
        assert len(mapping) == 2
        # Both should be valid
        for mapped_name in mapping.values():
            assert len(mapped_name) > 0

    def test_max_length_10(self):
        """All mapped names should be max 10 characters."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names([
            'a' * 20,
            'b' * 30,
            'field_with_very_long_name'
        ])

        for mapped_name in mapping.values():
            assert len(mapped_name) <= 10

    def test_reverse_mapping(self):
        """Reverse mapping should correctly map back to original names."""
        mapper = FieldMapper()
        original_names = ['short', 'verylongfieldname']
        mapper.map_field_names(original_names)

        reverse = mapper.get_reverse_mapping()

        # Check that reverse mapping works
        for orig, short in mapper.get_mapping().items():
            assert reverse[short] == orig

    def test_unicode_characters_handled(self):
        """Unicode characters should be handled properly."""
        mapper = FieldMapper()
        mapping = mapper.map_field_names(['field_name', 'nombre'])

        # All mapped names should be ASCII-compatible
        for mapped_name in mapping.values():
            assert all(c.isascii() for c in mapped_name)
