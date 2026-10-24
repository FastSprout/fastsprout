"""Expose extra read and write fields only when explicitly requested.

Ordinary DTOs omit both extra markers, including ReadWriteDTO. Extended DTOs
include the ordinary fields for their operation plus the matching extra
fields. Internal fields remain hidden in every DTO.

Class declarations preserve visibility checks in IDEs. Dynamic derivation
uses the same runtime guards but exposes the source type to type checkers.
"""

from fastsprout.core import (
    BaseSchema,
    ExtraReadDTO,
    ExtraReadField,
    ExtraReadWriteDTO,
    ExtraWriteDTO,
    ExtraWriteField,
    Field,
    InternalField,
    ReadDTO,
    ReadWriteDTO,
    WriteDTO,
)
from fastsprout.core.dto import derive_dto


class Product(BaseSchema):
    name: Field[str]
    description: ExtraReadField[str]
    import_reference: ExtraWriteField[str | None] = ExtraWriteField(
        default=None
    )
    supplier_cost: InternalField[int | None] = InternalField(default=None)


class ProductRead(ReadDTO, Product): ...


class ProductWrite(WriteDTO, Product): ...


class ProductReadWrite(ReadWriteDTO, Product): ...


class ProductDetails(ExtraReadDTO, Product): ...


class ProductImport(ExtraWriteDTO, Product): ...


class ProductExtended(ExtraReadWriteDTO, Product): ...


def main() -> None:
    print("Read:", ProductRead(name="Notebook"))
    print("Write:", ProductWrite(name="Notebook"))
    print("Read/write:", ProductReadWrite(name="Notebook"))

    details = ProductDetails(name="Notebook", description="120 pages")
    imported = ProductImport(name="Notebook", import_reference="catalog-42")
    print("Extra read:", details)
    print("Extra write:", imported)
    print(
        "Extra read/write:",
        ProductExtended(
            name="Notebook",
            description=details.description,
            import_reference=imported.import_reference,
        ),
    )

    try:
        ProductWrite(name="Notebook", import_reference="catalog-42")
    except AttributeError as error:
        print(error)

    model = derive_dto(Product, ExtraReadDTO)
    print(
        "Dynamic extra read:",
        model(name="Notebook", description="Created with derive_dto"),
    )


if __name__ == "__main__":
    main()
