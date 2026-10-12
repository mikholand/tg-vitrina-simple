from app.entities.product import Availability


def resolve_availability(quantity: int | None, requested: Availability) -> Availability:
    """quantity is the source of truth whenever it is known.

    quantity == 0  -> OUT_OF_STOCK
    quantity > 0   -> IN_STOCK
    quantity is None -> whatever the seller/extractor said (defaults to UNKNOWN)
    """
    if quantity is not None:
        return Availability.OUT_OF_STOCK if quantity == 0 else Availability.IN_STOCK
    return requested
