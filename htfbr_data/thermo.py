"""Derived thermochemistry from JANAF rows: interpolation, phase changes, vapour pressure."""
from __future__ import annotations

import math
import sqlite3

import numpy as np

from .chem import parse_formula

R = 8.314462618e-3  # kJ/(mol K), CODATA 2018


def _is_ion(formula: str) -> bool:
    return formula.rstrip().endswith(("+", "-"))


def enthalpy(con: sqlite3.Connection, species_id: int, T: float) -> float | None:
    """Absolute-scale enthalpy H(T) = dfH(298.15) + [H(T) - H(298.15)], kJ/mol; immune to reference-state switches."""
    h298, rel = interp(con, species_id, "dfH", 298.15), interp(con, species_id, "h_rel", T)
    return None if h298 is None or rel is None else h298 + rel


def find_species(con: sqlite3.Connection, formula: str, phase: str) -> int | None:
    target = parse_formula(formula)
    for r in con.execute("SELECT species_id, formula FROM species WHERE phase=?", (phase,)):
        if _is_ion(r["formula"]):
            continue
        try:
            if parse_formula(r["formula"]) == target:
                return r["species_id"]
        except ValueError:
            continue
    return None


def rows(con: sqlite3.Connection, species_id: int) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM thermo WHERE species_id=? ORDER BY row_index", (species_id,)).fetchall()


def interp(con: sqlite3.Connection, species_id: int, column: str, T: float) -> float | None:
    data = [(r["T_K"], r[column]) for r in rows(con, species_id) if r[column] is not None]
    if not data:
        return None
    Ts, vs = np.array([d[0] for d in data]), np.array([d[1] for d in data])
    if T < Ts.min() or T > Ts.max():
        return None
    # transition temperatures appear twice; np.interp needs increasing x, keep the last value at duplicates
    keep = np.append(np.diff(Ts) != 0, True)
    return float(np.interp(T, Ts[keep], vs[keep]))


def transition_T(con: sqlite3.Connection, species_id: int, keyword: str) -> float | None:
    for r in rows(con, species_id):
        if r["note"] and keyword.upper() in r["note"].upper():
            return r["T_K"]
    return None


def gas_oligomers(con: sqlite3.Connection, formula: str, max_k: int = 3) -> list[tuple[int, int]]:
    """(k, species_id) for gas species whose formula is k times `formula` (monomer, dimer, trimer)."""
    base, out = parse_formula(formula), []
    for r in con.execute("SELECT species_id, formula FROM species WHERE phase='g'"):
        if _is_ion(r["formula"]):
            continue
        try:
            c = parse_formula(r["formula"])
        except ValueError:
            continue
        for k in range(1, max_k + 1):
            if c == {el: n * k for el, n in base.items()}:
                out.append((k, r["species_id"]))
    return sorted(out)


def _total_p(con, gases, cond, T) -> float | None:
    g_cond = interp(con, cond, "dfG", T)
    if g_cond is None:
        return None
    total = 0.0
    for k, sid in gases:
        g = interp(con, sid, "dfG", T)
        if g is None:
            return None
        total += math.exp(-(g - k * g_cond) / (R * T))
    return total


def vapor_pressure_bar(con: sqlite3.Connection, formula: str, T: float) -> tuple[float | None, str]:
    """Total vapour pressure over the condensed (cr,l) phase, summing monomer, dimer and trimer gas
    species present in JANAF: p = sum_k exp(-(dfG(X_k, g) - k dfG(X, cr,l)) / RT).

    Above an element's tabulated boiling point (where JANAF switches the element reference to the gas)
    the value is extrapolated with Clausius-Clapeyron from the enthalpy of vaporisation at Tb.
    """
    gases, cond = gas_oligomers(con, formula), find_species(con, formula, "cr,l")
    if not gases or cond is None:
        return None, "missing gas or cr,l table"
    species = "+".join({1: "monomer", 2: "dimer", 3: "trimer"}[k] for k, _ in gases)
    bp = transition_T(con, cond, "FUGACITY")
    if bp is not None and T > bp + 1e-6:
        mono = dict(gases).get(1)
        dH = enthalpy(con, mono, bp) - enthalpy(con, cond, bp)
        p = math.exp(-dH / R * (1 / T - 1 / bp))
        return p, f"EXTRAPOLATED above Tb={bp:.0f} K: Clausius-Clapeyron, constant dHvap={dH:.1f} kJ/mol from JANAF"
    p = _total_p(con, gases, cond, T)
    if p is None:
        return None, f"{T:.0f} K outside table range"
    return p, f"JANAF dfG, {species}"


def boiling_point_K(con: sqlite3.Connection, formula: str) -> tuple[float | None, str]:
    cond = find_species(con, formula, "cr,l")
    if cond is not None and (bp := transition_T(con, cond, "FUGACITY")) is not None:
        return bp, "JANAF cr,l table: fugacity = 1 bar row"
    gases = gas_oligomers(con, formula)
    if not gases or cond is None:
        return None, "missing gas or cr,l table"
    Ts = [r["T_K"] for r in rows(con, cond)]
    prev = None
    for T in np.arange(300.0, max(Ts), 2.0):
        p = _total_p(con, gases, cond, T)
        if p is None:
            continue
        lnp = math.log(p)
        if prev is not None and prev[1] < 0 <= lnp:
            T0, l0 = prev
            species = "+".join({1: "monomer", 2: "dimer", 3: "trimer"}[k] for k, _ in gases)
            return T0 + (T - T0) * (-l0) / (lnp - l0), f"JANAF: T where total p ({species}) = 1 bar"
        prev = (T, lnp)
    return None, "no 1 bar crossing within table range"


def melting_point_K(con: sqlite3.Connection, formula: str) -> tuple[float | None, str]:
    cond = find_species(con, formula, "cr,l")
    if cond is None:
        return None, "missing cr,l table"
    T = transition_T(con, cond, "LIQUID")
    return (T, "JANAF cr,l table: crystal <--> liquid row") if T else (None, "no melting row in cr,l table")
