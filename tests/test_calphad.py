"""CALPHAD ingester: assessed-system detection, duplicate parameters, melting points (no network)."""
import pytest

pytest.importorskip("pycalphad")
from pycalphad import Database

from htfbr_data.ingest import calphad

# Toy unary: liquid and solid with G_liq - G_sol = 10000 - 10 T  ->  melts at exactly 1000 K
UNARY = """
ELEMENT VA VACUUM 0 0 0 !
ELEMENT AL FCC_A1 26.98 0 0 !
TYPE_DEFINITION % SEQ * !
PHASE LIQUID % 1 1 !
CONSTITUENT LIQUID :AL: !
PHASE FCC_A1 % 1 1 !
CONSTITUENT FCC_A1 :AL: !
PARAMETER G(FCC_A1,AL;0) 1 -20000-30*T; 6000 N !
PARAMETER G(LIQUID,AL;0) 1 -10000-40*T; 6000 N !
"""

BINARY = UNARY.replace("ELEMENT AL FCC_A1 26.98 0 0 !", "ELEMENT AL FCC_A1 26.98 0 0 !\nELEMENT ZR HCP_A3 91.22 0 0 !") \
    .replace("CONSTITUENT LIQUID :AL: !", "CONSTITUENT LIQUID :AL,ZR: !") + """
PHASE AL3ZR % 2 3 1 !
CONSTITUENT AL3ZR :AL:ZR: !
PARAMETER G(LIQUID,ZR;0) 1 -30000; 6000 N !
PARAMETER G(LIQUID,AL,ZR;0) 1 -50000; 6000 N !
PARAMETER G(AL3ZR,AL:ZR;0) 1 -40000; 6000 N !
PARAMETER G(LIQUID,AL;0) 1 -10000-40*T; 6000 N !
PARAMETER G(LIQUID,ZR;0) 1 -31000; 6000 N !
"""


def test_melting_point_from_gibbs_crossing():
    mp = calphad.melting_points(Database(UNARY), ["Al"])
    assert mp["Al"] == pytest.approx(1000.0, abs=0.6)


def test_duplicate_parameters_are_detected_and_removed():
    dbf = Database(BINARY)
    same, conflict = calphad.dedupe_parameters(dbf)
    assert same == 1 and conflict == 1  # G(LIQUID,AL) repeated identically; G(LIQUID,ZR) repeated with a new value
    assert len([p for p in dbf._parameters.all() if p["phase_name"] == "LIQUID"
                and len(p["constituent_array"][0]) == 1 and str(p["constituent_array"][0][0]) == "AL"]) == 1


def test_assessed_systems_from_g_interactions_and_compounds():
    systems = calphad.assessed_systems(Database(BINARY))
    assert "Al-Zr" in systems
    assert systems["Al-Zr"]["liquid"] is True                 # G(LIQUID,AL,ZR) counts as an interaction
    assert "AL3ZR" in systems["Al-Zr"]["phases"]              # compound end-member counts too
    assert all("-" in k for k in systems)
