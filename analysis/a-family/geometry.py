"""Unit-cell volume fractions for the Family A homogenised neutronics (calc).

A2 reference (A2 page): square pitch 20 mm, tube bore 10 mm, wall 1.5 mm = 1.2 mm W (fuel side) +
0.3 mm AlN (Al side). Fuel fills the space between tubes. Alternative: 1.5 mm monolithic ZrB2.

A1 (assumed here, approx.): (U,Pu)N pellet radius 3.5 mm, 0.1 mm He gap (treated as void),
0.8 mm cladding (ZrB2, or 0.6 mm W + 0.2 mm AlN outside), triangular pitch 10.1 mm (p/d = 1.15),
open lattice without ducts or spacers.
"""
from math import pi, sqrt


def annulus(r1, r2):
    return pi * (r2 ** 2 - r1 ** 2)


def _a2():
    cell = 20.0 ** 2
    r_bore, r_aln, r_out = 5.0, 5.3, 6.5
    al = pi * r_bore ** 2 / cell
    aln = annulus(r_bore, r_aln) / cell
    w = annulus(r_aln, r_out) / cell
    fuel = 1 - pi * r_out ** 2 / cell
    return {
        "W/AlN": {"fuel": fuel, "W": w, "AlN": aln, "coolant": al},
        "ZrB2": {"fuel": fuel, "ZrB2": w + aln, "coolant": al},
    }


def _a1():
    p = 10.1
    cell = sqrt(3) / 2 * p ** 2
    rf, rg, rc = 3.5, 3.6, 4.4
    fuel = pi * rf ** 2 / cell
    gap = annulus(rf, rg) / cell
    clad = annulus(rg, rc) / cell
    cool = 1 - pi * rc ** 2 / cell
    w = annulus(rg, rg + 0.6) / cell
    aln = annulus(rg + 0.6, rc) / cell
    return {
        "ZrB2": {"fuel": fuel, "gap": gap, "ZrB2": clad, "coolant": cool},
        "W/AlN": {"fuel": fuel, "gap": gap, "W": w, "AlN": aln, "coolant": cool},
        "pin": {"r_fuel_mm": rf, "r_gap_mm": rg, "r_clad_mm": rc, "pitch_mm": p},
    }


A2_FRACTIONS = _a2()
A1_FRACTIONS = _a1()

if __name__ == "__main__":
    import json
    print(json.dumps({"A1": A1_FRACTIONS, "A2": A2_FRACTIONS}, indent=1))
