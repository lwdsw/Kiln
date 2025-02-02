from typing import NoReturn


def raise_exhaustive_enum_error(value: NoReturn) -> NoReturn:
    raise ValueError(f"Unhandled enum value: {value}")
