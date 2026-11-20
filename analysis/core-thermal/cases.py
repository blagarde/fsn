"""Reference core cases for the study (one per heat-transport family), and the sweep grid.

Temperatures are chosen per coolant to sit below its boiling point at the stated pressure
and in the range the design families target. Fuel and wall limits are physical (melting,
dissociation, creep margin); chemistry is deliberately ignored in this study.
"""
from core import CoreSpec

C = 273.15

CASES = {
    # classic SFR anchor: oxide pins in sodium, to check the model against known reactors
    "MOX-Na": CoreSpec("MOX pins / Na (SFR anchor)", fuel="UPuO2", pu=0.20, f_fuel=0.40, coolant="Na",
                       shape="cylinder", a_mm=3.5, wall_mm=0.5, wall="steel", h_gap=6000.0,
                       T_in=395 + C, T_out=545 + C, reflector=("steel", 7.6, 30.0), v_max=8.0,
                       T_wall_limit=700 + C, notes="SFR-class: anchors the model to known numbers"),
    # B-family-like: nitride pins in lead
    "UN-Pb": CoreSpec("(U,Pu)N pins / Pb", fuel="UPuN", pu=0.15, f_fuel=0.40, coolant="Pb",
                      shape="cylinder", a_mm=3.0, wall_mm=0.5, wall="Mo", h_gap=None,
                      T_in=900 + C, T_out=1200 + C, reflector=("Pb", 9.8, 50.0), v_max=3.0,
                      notes="Pb-bonded nitride pins, Mo cladding; v_max 3 m/s for lead (erosion, pumping)"),
    # gas-cooled: nitride particles in helium (S5/S8-like)
    "UN-He": CoreSpec("(U,Pu)N particles / He 70 bar", fuel="UPuN", pu=0.18, f_fuel=0.35, coolant="He70",
                      shape="sphere", a_mm=0.5, wall_mm=0.1, wall="SiC", h_gap=None,
                      T_in=600 + C, T_out=1100 + C, reflector=("SiC", 3.21, 50.0), v_max=60.0,
                      notes="coated nitride particles, He 7 MPa"),
    # A2-like: liquid U-Pu pool around Al-cooled W tubes (conduction-only fuel side)
    "UPu-Al-pool": CoreSpec("liquid U-Pu pool / Al in W tubes (A2-like)", fuel="UPu_liquid", pu=0.12, f_fuel=0.45,
                            coolant="Al", shape="annulus", a_mm=6.0, wall_mm=1.0, wall="W", nu_fuel=1.0,
                            T_in=1300 + C, T_out=1600 + C, reflector=("W", 19.0, 20.0), v_max=6.0,
                            T_fuel_limit=2100 + C, notes="fuel limit 2,100 C (Pu vapour, W attack set aside)"),
    # L7 radiatively coupled pool: fuel radiates across a vacuum gap to He-cooled tubes
    "UPu-rad-He": CoreSpec("liquid U-Pu pool, radiative gap to He tubes (L7-like)", fuel="UPu_liquid", pu=0.12,
                           f_fuel=0.45, coolant="He70", shape="annulus", a_mm=10.0, wall_mm=1.5, wall="Mo",
                           radiative=(0.8, 0.8), nu_fuel=1.0, T_in=900 + C, T_out=1300 + C,
                           reflector=("Mo", 10.0, 20.0), v_max=60.0, T_fuel_limit=2100 + C,
                           notes="emissivities 0.8 both sides (APPROX: coated surfaces); vacuum gap"),
    # L7 with aluminium in the tubes (the R-family variant the geometry agent is scoping)
    "UPu-rad-Al": CoreSpec("liquid U-Pu pool, radiative gap to Al tubes (L7-like)", fuel="UPu_liquid", pu=0.12,
                           f_fuel=0.45, coolant="Al", shape="annulus", a_mm=10.0, wall_mm=1.5, wall="W",
                           radiative=(0.8, 0.8), nu_fuel=1.0, T_in=1300 + C, T_out=1600 + C,
                           reflector=("W", 19.0, 20.0), v_max=6.0, T_fuel_limit=2100 + C,
                           notes="hotter coolant than the He variant, so less radiative driving force"),
    # liquid fuel circulating as its own coolant (A3/X-like): delayed-neutron loss
    "UPu-circ": CoreSpec("circulating liquid U-Pu (fuel is the coolant)", fuel="UPu_liquid", pu=0.12, f_fuel=0.60,
                         circulating=True, loop_to_core_volume=1.0, wall="W", T_in=1700 + C, T_out=2000 + C,
                         reflector=("W", 19.0, 20.0), notes="remaining 40 % taken as W structure"),
}

PU_GRID = [0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]
FFUEL_GRID = [0.25, 0.35, 0.45, 0.55]
