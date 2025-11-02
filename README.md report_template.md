# SE Project 2025 — Bit Packing Compression (Python)

Author: <Your Name> — M1 IA

## Overview
Bit-packing d’un tableau d’entiers avec :
- **Non-crossing** (aucun entier compressé ne traverse deux mots 32 bits)
- **Crossing** (bitstream continu, peut traverser les mots)
- Gestion **overflow area** (flag + index) pour valeurs très grosses
- Accès aléatoire `get(i)` sans décompresser tout
- **Factory** pour choisir le type
- **Benchmarks** + calcul du seuil de latence où la compression devient rentable

## Run
```bash
python src/main.py
