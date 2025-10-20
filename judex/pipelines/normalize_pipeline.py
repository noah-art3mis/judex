from __future__ import annotations

from typing import Any

from itemadapter import ItemAdapter

from judex.utils.text import normalize_spaces


def _normalize_spaces(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_spaces(value)
    return value


def _to_upper(value: Any) -> Any:
    if isinstance(value, str):
        return value.upper()
    return value


def _strip(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


class NormalizePipeline:
    """
    Normalize common text fields.

    - Uppercase selected fields (idempotent)
    - Strip surrounding whitespace on selected fields and lists of strings

    Adjust UPPER_FIELDS and STRIP_FIELDS to your needs.
    """

    UPPER_FIELDS = {"classe", "relator"}
    STRIP_FIELDS = {
        "numero_unico",
        "meio",
        "publicidade",
        "orgao_origem",
        "primeiro_autor",
        "relator",
        "classe",
    }

    def process_item(self, item: Any, spider) -> Any:  # type: ignore[override]
        adapter = ItemAdapter(item)

        for field_name in list(adapter.field_names()):
            value = adapter.get(field_name)

            # Trim strings
            if field_name in self.STRIP_FIELDS and isinstance(value, str):
                adapter[field_name] = _strip(value)

            # Trim list of strings
            if field_name in self.STRIP_FIELDS and isinstance(value, list):
                adapter[field_name] = [
                    _strip(element) if isinstance(element, str) else element
                    for element in value
                ]

            # Uppercase strings
            updated_value = adapter.get(field_name)
            if field_name in self.UPPER_FIELDS and isinstance(updated_value, str):
                adapter[field_name] = _to_upper(updated_value)

        return item
