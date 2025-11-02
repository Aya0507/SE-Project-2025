from typing import List, Optional
import math

WORD_SIZE = 32
WORD_MASK = (1 << WORD_SIZE) - 1


def bit_length(x: int) -> int:
    """Nombre de bits pour représenter x (0 -> 1)."""
    return x.bit_length() if x else 1


class BitPackingBase:
    def __init__(self, words: Optional[List[int]] = None):
        self.words = words or []
        self.n = 0                    # nombre d'entiers encodés
        self.k = 0                    # bits par valeur directe
        self.overflow_positions: List[int] = []
        self.overflow_values: List[int] = []
        self.idx_bits = 0             # bits pour indexer la zone overflow
        self.uses_overflow = False

    @staticmethod
    def _u32(x: int) -> int:
        return x & WORD_MASK

    def size_bits(self) -> int:
        """Taille totale (flux + payload overflow en mots complets)."""
        return len(self.words) * WORD_SIZE + len(self.overflow_values) * WORD_SIZE

    def compress(self, array: List[int]) -> None:
        raise NotImplementedError

    def decompress(self) -> List[int]:
        raise NotImplementedError

    def get(self, i: int) -> int:
        raise NotImplementedError


#            NON-CROSSING 
class BitPackingNonCrossing(BitPackingBase):
    """
    Flux empaqueté en blocs par valeur (on ne coupe jamais un bloc sur 2 mots).
    Si overflow activé : chaque valeur = [flag(1)] + (b bits ou idx_bits).
    Les payloads sont donc de longueur variable (1+b) ou (1+idx_bits).
    """

    def __init__(self, choose_overflow: bool = True):
        super().__init__()
        self.choose_overflow = choose_overflow

    def _choose_k_and_overflow(self, arr: List[int]) -> None:
        n = len(arr)
        bitlens = [bit_length(x) for x in arr]
        if not self.choose_overflow:
            self.k = max(bitlens) if bitlens else 1
            self.uses_overflow = False
            self.idx_bits = 0
            return

        best = None  # (total_bits, b, oc, idx_bits)
        for b in range(1, WORD_SIZE + 1):
            overflow_positions = [i for i, bl in enumerate(bitlens) if bl > b]
            oc = len(overflow_positions)
            idx_bits = math.ceil(math.log2(oc)) if oc > 1 else (1 if oc == 1 else 0)
            overhead_flag = 1 if oc > 0 else 0
            encoded_bits = (n - oc) * (overhead_flag + b) + oc * (overhead_flag + idx_bits)
            total = encoded_bits + oc * WORD_SIZE  # payload overflow stocké en mots complets
            if best is None or total < best[0]:
                best = (total, b, oc, idx_bits)

        _, b, oc, idx_bits = best
        self.k = b
        self.uses_overflow = oc > 0
        self.idx_bits = idx_bits

    def compress(self, arr: List[int]) -> None:
        self.n = len(arr)
        if self.n == 0:
            self.words = []
            self.overflow_positions = []
            self.overflow_values = []
            self.idx_bits = 0
            self.uses_overflow = False
            return

        self._choose_k_and_overflow(arr)
        b = self.k

        # Préparer l overflow
        bitlens = [bit_length(x) for x in arr]
        self.overflow_positions = [i for i, bl in enumerate(bitlens) if bl > b]
        self.overflow_values = [arr[i] for i in self.overflow_positions]
        oc = len(self.overflow_positions)
        # protection idx_bits = 0 quand oc in {0,1}
        self.idx_bits = math.ceil(math.log2(oc)) if oc > 1 else (1 if oc == 1 else 0)

        # Construire la liste (payload, length)
        stream: List[tuple[int, int]] = []
        for idx, val in enumerate(arr):
            if self.uses_overflow and bit_length(val) > b:
                # flag=1 + index overflow (0 si un seul élément)
                flag = 1
                ov_index = self.overflow_positions.index(idx) if oc > 1 else 0
                payload = (flag << self.idx_bits) | ov_index if self.idx_bits > 0 else 1  # juste le flag
                plen = 1 + (self.idx_bits if self.idx_bits > 0 else 0)
            else:
                if self.uses_overflow:
                    # flag=0 + b bits
                    payload = (0 << b) | (val & ((1 << b) - 1))
                    plen = 1 + b
                else:
                    # pas de flag
                    payload = val & ((1 << b) - 1)
                    plen = b
            stream.append((payload, plen))

        # Empaqueter sans couper le bloc sur 2 mots
        self.words = []
        cur_word = 0
        used = 0
        for payload, plen in stream:
            if used + plen > WORD_SIZE:
                self.words.append(self._u32(cur_word))
                cur_word = 0
                used = 0
            cur_word |= (payload & ((1 << plen) - 1)) << used
            used += plen
        if used > 0:
            self.words.append(self._u32(cur_word))

    def decompress(self) -> List[int]:
        if self.n == 0:
            return []

        res = [0] * self.n
        wi = 0
        bitpos = 0

        def read_bits(plen: int) -> int:
            nonlocal wi, bitpos
            v = 0
            r = 0
            while r < plen:
                available = WORD_SIZE - bitpos
                take = min(available, plen - r)
                part = (self.words[wi] >> bitpos) & ((1 << take) - 1)
                v |= part << r
                r += take
                bitpos += take
                if bitpos == WORD_SIZE:
                    wi += 1
                    bitpos = 0
            return v

        for i in range(self.n):
            if self.uses_overflow:
                flag = read_bits(1)
                if flag == 1:
                    idx = read_bits(self.idx_bits) if self.idx_bits > 0 else 0
                    # sécurité sur l'index overflow
                    if not self.overflow_values:
                        res[i] = 0
                    else:
                        idx = min(idx, len(self.overflow_values) - 1)
                        res[i] = self.overflow_values[idx]
                else:
                    res[i] = read_bits(self.k)
            else:
                res[i] = read_bits(self.k)
        return res

    def get(self, i: int) -> int:
        if i < 0 or i >= self.n:
            raise IndexError("Index out of range")

        wi = 0
        bitpos = 0

        def read_bits(plen: int) -> int:
            nonlocal wi, bitpos
            v = 0
            r = 0
            while r < plen:
                available = WORD_SIZE - bitpos
                take = min(available, plen - r)
                part = (self.words[wi] >> bitpos) & ((1 << take) - 1)
                v |= part << r
                r += take
                bitpos += take
                if bitpos == WORD_SIZE:
                    wi += 1
                    bitpos = 0
            return v

        val = 0
        for _ in range(i + 1):
            if self.uses_overflow:
                f = read_bits(1)
                if f == 1:
                    ov = read_bits(self.idx_bits) if self.idx_bits > 0 else 0
                    if not self.overflow_values:
                        val = 0
                    else:
                        ov = min(ov, len(self.overflow_values) - 1)
                        val = self.overflow_values[ov]
                else:
                    val = read_bits(self.k)
            else:
                val = read_bits(self.k)
        return val


#           CROSSING 
class BitPackingCrossing(BitPackingBase):
    """
    Flux bit-à-bit continu (LSB-first). Les valeurs peuvent franchir
    une frontière de mot 32 bits. Overflow identique au non-crossing.
    """

    def __init__(self, choose_overflow: bool = True):
        super().__init__()
        self.choose_overflow = choose_overflow

    def _choose_k_and_overflow(self, arr: List[int]) -> None:
        bitlens = [bit_length(x) for x in arr]
        if not self.choose_overflow:
            self.k = max(bitlens) if bitlens else 1
            self.uses_overflow = False
            self.idx_bits = 0
            return

        best = None
        n = len(arr)
        for b in range(1, WORD_SIZE + 1):
            overflow_positions = [i for i, bl in enumerate(bitlens) if bl > b]
            oc = len(overflow_positions)
            idx_bits = math.ceil(math.log2(oc)) if oc > 1 else (1 if oc == 1 else 0)
            overhead_flag = 1 if oc > 0 else 0
            encoded_bits = (n - oc) * (overhead_flag + b) + oc * (overhead_flag + idx_bits)
            total = encoded_bits + oc * WORD_SIZE
            if best is None or total < best[0]:
                best = (total, b, oc, idx_bits)

        _, b, oc, idx_bits = best
        self.k = b
        self.uses_overflow = oc > 0
        self.idx_bits = idx_bits

    def compress(self, arr: List[int]) -> None:
        self.n = len(arr)
        if self.n == 0:
            self.words = []
            self.overflow_positions = []
            self.overflow_values = []
            self.idx_bits = 0
            self.uses_overflow = False
            return

        self._choose_k_and_overflow(arr)
        b = self.k

        bitlens = [bit_length(x) for x in arr]
        self.overflow_positions = [i for i, bl in enumerate(bitlens) if bl > b]
        self.overflow_values = [arr[i] for i in self.overflow_positions]
        oc = len(self.overflow_positions)
        self.idx_bits = math.ceil(math.log2(oc)) if oc > 1 else (1 if oc == 1 else 0)

        stream = 0
        slen = 0
        self.words = []

        def push_bits(val: int, length: int):
            nonlocal stream, slen
            if length == 0:
                return
            stream |= (val & ((1 << length) - 1)) << slen
            slen += length
            while slen >= WORD_SIZE:
                self.words.append(self._u32(stream))
                stream >>= WORD_SIZE
                slen -= WORD_SIZE

        for idx, val in enumerate(arr):
            if self.uses_overflow and bit_length(val) > b:
                push_bits(1, 1)
                if self.idx_bits > 0:
                    push_bits(self.overflow_positions.index(idx) if oc > 1 else 0, self.idx_bits)
            else:
                push_bits(0, 1)
                push_bits(val, b)

        if slen > 0:
            self.words.append(self._u32(stream))

    def decompress(self) -> List[int]:
        if self.n == 0:
            return []

        res = [0] * self.n
        wi = 0
        bitpos = 0

        def read_bits(plen: int) -> int:
            nonlocal wi, bitpos
            v = 0
            r = 0
            while r < plen:
                available = WORD_SIZE - bitpos
                take = min(available, plen - r)
                part = (self.words[wi] >> bitpos) & ((1 << take) - 1)
                v |= part << r
                r += take
                bitpos += take
                if bitpos == WORD_SIZE:
                    wi += 1
                    bitpos = 0
            return v

        for i in range(self.n):
            f = read_bits(1)
            if f == 1:
                idx = read_bits(self.idx_bits) if self.idx_bits > 0 else 0
                if not self.overflow_values:
                    res[i] = 0
                else:
                    idx = min(idx, len(self.overflow_values) - 1)
                    res[i] = self.overflow_values[idx]
            else:
                res[i] = read_bits(self.k)
        return res

    def get(self, i: int) -> int:
        if i < 0 or i >= self.n:
            raise IndexError("Index out of range")

        wi = 0
        bitpos = 0

        def read_bits(plen: int) -> int:
            nonlocal wi, bitpos
            v = 0
            r = 0
            while r < plen:
                available = WORD_SIZE - bitpos
                take = min(available, plen - r)
                part = (self.words[wi] >> bitpos) & ((1 << take) - 1)
                v |= part << r
                r += take
                bitpos += take
                if bitpos == WORD_SIZE:
                    wi += 1
                    bitpos = 0
            return v

        val = 0
        for _ in range(i + 1):
            f = read_bits(1)
            if f == 1:
                idx = read_bits(self.idx_bits) if self.idx_bits > 0 else 0
                if not self.overflow_values:
                    val = 0
                else:
                    idx = min(idx, len(self.overflow_values) - 1)
                    val = self.overflow_values[idx]
            else:
                val = read_bits(self.k)
        return val
