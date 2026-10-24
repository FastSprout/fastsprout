from enum import Enum
from typing import Never

from .protocols.ables import AllComparisonsable

__all__ = ["FilterValue", "OrderedValue"]

# The operand type varies by value; field references retain its exact type.
type OrderedValue = AllComparisonsable[Never]
type FilterValue = OrderedValue | Enum | None
