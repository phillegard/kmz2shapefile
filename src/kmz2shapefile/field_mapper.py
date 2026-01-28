"""Map field names to valid Shapefile field names (max 10 characters)."""

import re
from typing import Dict, List, Set


class FieldMapper:
    """
    Map original field names to valid Shapefile field names.

    Shapefile DBF format limits field names to 10 characters.
    This class handles truncation and collision avoidance.
    """

    MAX_FIELD_LENGTH = 10

    def __init__(self):
        self._mapping: Dict[str, str] = {}
        self._used_names: Set[str] = set()

    def map_field_names(self, original_names: List[str]) -> Dict[str, str]:
        """
        Create mapping from original field names to valid Shapefile field names.

        Args:
            original_names: List of original field names

        Returns:
            Dictionary mapping original names to truncated names
        """
        self._mapping = {}
        self._used_names = set()

        for name in original_names:
            mapped_name = self._create_unique_name(name)
            self._mapping[name] = mapped_name
            self._used_names.add(mapped_name)

        return self._mapping

    def _create_unique_name(self, original: str) -> str:
        """
        Create a unique, valid Shapefile field name.

        Rules:
        1. Truncate to 10 characters
        2. Replace invalid characters with underscore
        3. If collision, append incrementing number
        4. Must start with letter or underscore

        Args:
            original: Original field name

        Returns:
            Valid, unique Shapefile field name
        """
        # Clean the name (replace invalid chars with underscore)
        cleaned = self._clean_name(original)

        # Truncate to max length
        truncated = cleaned[:self.MAX_FIELD_LENGTH]

        # Ensure it starts with letter or underscore
        if truncated and not (truncated[0].isalpha() or truncated[0] == '_'):
            truncated = '_' + truncated[:self.MAX_FIELD_LENGTH - 1]

        # Handle empty names
        if not truncated:
            truncated = 'field'

        # Handle collisions
        if truncated not in self._used_names:
            return truncated

        # Find unique name by appending number
        return self._resolve_collision(truncated)

    def _clean_name(self, name: str) -> str:
        """
        Clean field name to only contain valid characters.

        Valid characters: a-z, A-Z, 0-9, underscore

        Args:
            name: Original field name

        Returns:
            Cleaned field name
        """
        # Replace invalid characters with underscore, collapse multiple underscores
        cleaned = re.sub(r'[^a-zA-Z0-9_]+', '_', name)
        return cleaned.strip('_')

    def _resolve_collision(self, base_name: str) -> str:
        """
        Resolve field name collision by appending incrementing number.

        Examples:
            'longfieldna' with collision -> 'longfiel_1'
            'longfiel_1' with collision -> 'longfiel_2'

        Args:
            base_name: Base field name (already truncated)

        Returns:
            Unique field name with number suffix
        """
        counter = 1

        while True:
            suffix = f"_{counter}"
            suffix_len = len(suffix)

            # Truncate base to make room for suffix
            max_base_len = self.MAX_FIELD_LENGTH - suffix_len
            new_name = base_name[:max_base_len] + suffix

            if new_name not in self._used_names:
                return new_name

            counter += 1

            # Safety limit to prevent infinite loop
            if counter > 9999:
                raise ValueError(f"Unable to create unique name for '{base_name}'")

    def get_mapping(self) -> Dict[str, str]:
        """
        Get the current field name mapping.

        Returns:
            Dictionary mapping original names to Shapefile names
        """
        return self._mapping.copy()

    def get_reverse_mapping(self) -> Dict[str, str]:
        """
        Get reverse mapping from Shapefile names to original names.

        Returns:
            Dictionary mapping Shapefile names to original names
        """
        return {v: k for k, v in self._mapping.items()}
