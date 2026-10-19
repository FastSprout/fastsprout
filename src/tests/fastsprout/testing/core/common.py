from fastsprout.core import Field, dataclass


@dataclass
class CartContext:
    products: Field[list[str]] = Field(default_factory=list)
