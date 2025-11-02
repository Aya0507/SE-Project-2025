from .bitpacking import BitPackingCrossing, BitPackingNonCrossing

def get_bitpacker(kind="noncrossing", choose_overflow=True):
    k=kind.lower()
    if k in ("noncrossing","non-crossing","no-cross"):
        return BitPackingNonCrossing(choose_overflow)
    if k in ("crossing","cross","bitstream"):
        return BitPackingCrossing(choose_overflow)
    raise ValueError("Unknown kind")
