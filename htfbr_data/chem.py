"""Small chemistry helpers: formula parsing and element symbols."""
from __future__ import annotations

import re
from collections import Counter

SYMBOLS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
    "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm "
    "Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm"
).split()
Z_OF = {s: i + 1 for i, s in enumerate(SYMBOLS)}

_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")


def parse_formula(formula: str) -> Counter:
    """'Al2O3' or 'Al1N1' -> Counter({'Al': 2, 'O': 3}). Charges and phase tags are ignored."""
    core = re.sub(r"\(.*?\)", "", formula).rstrip("+-")
    counts: Counter = Counter()
    pos = 0
    for m in _TOKEN.finditer(core):
        if m.start() != pos:
            raise ValueError(f"cannot parse formula {formula!r}")
        el, n = m.group(1), m.group(2)
        if el not in Z_OF:
            raise ValueError(f"unknown element {el!r} in {formula!r}")
        counts[el] += float(n) if n else 1.0
        pos = m.end()
    if pos != len(core) or not counts:
        raise ValueError(f"cannot parse formula {formula!r}")
    return counts


def same_formula(a: str, b: str) -> bool:
    return parse_formula(a) == parse_formula(b)


def pretty(formula: str) -> str:
    """'Al2O3' style with 1s removed, in parse order."""
    return "".join(f"{el}{'' if n == 1 else int(n) if n == int(n) else n}" for el, n in parse_formula(formula).items())
