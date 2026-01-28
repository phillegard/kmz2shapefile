"""Tests for field name mapping."""

import pytest

from kmz2shapefile.field_mapper import FieldMapper


class TestFieldMapper:
    """Tests for FieldMapper class."""

    @pytest.fixture
    def mapper(self):
        return FieldMapper()

    def test_short_names_unchanged(self, mapper):
        """Short names that are already valid should remain unchanged."""
        mapping = mapper.map_field_names(['name', 'type', 'id'])
        assert mapping == {'name': 'name', 'type': 'type', 'id': 'id'}

    def test_long_names_truncated(self, mapper):
        """Names longer than 10 chars should be truncated."""
        mapping = mapper.map_field_names(['verylongfieldname'])
        assert len(mapping['verylongfieldname']) <= 10

    def test_collision_handling(self, mapper):
        """Names that truncate to same value should get unique suffixes."""
        mapping = mapper.map_field_names([
            'verylongfield1',
            'verylongfield2',
            'verylongfield3'
        ])
        mapped_values = list(mapping.values())
        assert len(mapped_values) == len(set(mapped_values))

    def test_special_characters_cleaned(self, mapper):
        """Special characters should be replaced with underscore."""
        mapping = mapper.map_field_names(['field-name', 'field.name', 'field name'])
        for mapped_name in mapping.values():
            assert all(c.isalnum() or c == '_' for c in mapped_name)

    def test_starts_with_letter_or_underscore(self, mapper):
        """Names should start with letter or underscore."""
        mapping = mapper.map_field_names(['123field', '456data'])
        for mapped_name in mapping.values():
            assert mapped_name[0].isalpha() or mapped_name[0] == '_'

    def test_empty_name_handled(self, mapper):
        """Empty names should be handled gracefully."""
        mapping = mapper.map_field_names(['', 'validname'])
        assert len(mapping) == 2
        for mapped_name in mapping.values():
            assert len(mapped_name) > 0

    def test_max_length_10(self, mapper):
        """All mapped names should be max 10 characters."""
        mapping = mapper.map_field_names(['a' * 20, 'b' * 30, 'field_with_very_long_name'])
        for mapped_name in mapping.values():
            assert len(mapped_name) <= 10

    def test_reverse_mapping(self, mapper):
        """Reverse mapping should correctly map back to original names."""
        mapper.map_field_names(['short', 'verylongfieldname'])
        reverse = mapper.get_reverse_mapping()
        for orig, short in mapper.get_mapping().items():
            assert reverse[short] == orig

    def test_unicode_characters_handled(self, mapper):
        """Unicode characters should be handled properly."""
        mapping = mapper.map_field_names(['field_name', 'nombre'])
        for mapped_name in mapping.values():
            assert all(c.isascii() for c in mapped_name)
