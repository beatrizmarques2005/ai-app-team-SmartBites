"""Simple unit conversion utilities for common grocery units.

This module implements a small, extensible set of conversions used when
aggregating pantry quantities. It's intentionally minimal for a POC.
"""
from typing import Optional

# Conversion map to base units: grams for weight, milliliters for volume
_WEIGHT_UNITS = {
    'g': 1.0,
    'gram': 1.0,
    'grams': 1.0,
    'kg': 1000.0,
    'kilogram': 1000.0,
    'kilograms': 1000.0,
}

_VOLUME_UNITS = {
    'ml': 1.0,
    'milliliter': 1.0,
    'milliliters': 1.0,
    'l': 1000.0,
    'liter': 1000.0,
    'liters': 1000.0,
}


def convert_to_base(quantity: float, unit: Optional[str]) -> (Optional[float], Optional[str]):
    """Convert a quantity to a canonical base unit.

    Returns (value, base_unit) where base_unit is one of 'g', 'ml', or 'pcs'.
    If unknown unit, returns (quantity, unit)
    """
    if unit is None:
        return quantity, None

    u = unit.strip().lower()
    if u in _WEIGHT_UNITS:
        return quantity * _WEIGHT_UNITS[u], 'g'
    if u in _VOLUME_UNITS:
        return quantity * _VOLUME_UNITS[u], 'ml'
    # common piece/unit
    if u in ('pcs', 'pc', 'piece', 'pieces', 'unit', 'units'):
        return quantity, 'pcs'

    # unknown - return as-is
    try:
        return float(quantity), u
    except Exception:
        return quantity, u


def to_pretty(quantity: float, base_unit: str) -> (float, str):
    """Convert base_unit quantities to a user-friendly unit (e.g., grams->kg when large)

    Returns (value, unit)
    """
    if base_unit == 'g':
        if quantity >= 1000:
            return quantity / 1000.0, 'kg'
        return quantity, 'g'
    if base_unit == 'ml':
        if quantity >= 1000:
            return quantity / 1000.0, 'L'
        return quantity, 'ml'
    return quantity, base_unit
