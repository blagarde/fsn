"""Homogenised core compositions for B1-B6 (volume fractions; all approx. screening assumptions)."""
from bfam import (ENRICH, NAT, fuel_nitride, fuel_carbide, fuel_chloride, lithium, lead, helium, nb1zr,
                  molybdenum, tungsten, w_enriched, sic, void, cermet)

# Each entry: T_rep (K), coolant index for void worth, builder(x, **variant) -> [(material, vol frac)]
DESIGNS = {
    "B1": dict(
        title="Li-7-cooled (U,Pu)N pins, Nb-1Zr cladding",
        T_rep=1500.0, coolant_index=2,
        assumptions="fuel (U,Pu)N 40% at 13.0 g/cm3 (N-15 99.9%); Nb-1Zr cladding 15% at 8.57; "
                    "Li 40% at 0.45 g/cm3 (Li-7 99.99%); gap/plenum void 5%",
        build=lambda x, n15=ENRICH["N15"], li7=ENRICH["Li7"]: [
            (fuel_nitride(x, n15=n15), 0.40), (nb1zr(), 0.15), (lithium(li7), 0.40), (void(), 0.05)],
        variants={"natural N": dict(n15=NAT["N15"]), "Li-7 99.9%": dict(li7=0.999),
                  "natural Li": dict(li7=NAT["Li7"])},
    ),
    "B2": dict(
        title="Pb-cooled (U,Pu)N pins, SiC/SiC cladding",
        T_rep=1300.0, coolant_index=2,
        assumptions="fuel (U,Pu)N 40% at 13.0 g/cm3 (N-15 99.9%); SiC/SiC cladding 12% at 2.9; "
                    "Pb 45% at 10.0 g/cm3; gap void 3%",
        build=lambda x, n15=ENRICH["N15"], clad="SiC": [
            (fuel_nitride(x, n15=n15), 0.40), (sic() if clad == "SiC" else molybdenum(), 0.12),
            (lead(), 0.45), (void(), 0.03)],
        variants={"natural N": dict(n15=NAT["N15"]), "Mo cladding": dict(clad="Mo")},
    ),
    "B3-C": dict(
        title="He-cooled (U,Pu)C, SiC/SiC cladding and structure",
        T_rep=1500.0, coolant_index=2,
        assumptions="fuel (U,Pu)C 30% at 12.3 g/cm3; SiC/SiC 15% at 2.9; He 55% at 7 MPa, 1,400 K "
                    "(2.4 kg/m3, ideal gas)",
        build=lambda x: [(fuel_carbide(x), 0.30), (sic(), 0.15), (helium(), 0.55)],
        variants={},
    ),
    "B3-N": dict(
        title="He-cooled (U,Pu)N, SiC/SiC cladding and structure",
        light=True, T_rep=1500.0, coolant_index=2,
        assumptions="fuel (U,Pu)N 30% at 13.0 g/cm3 (N-15 99.9%); SiC/SiC 15% at 2.9; He 55% at 7 MPa, 1,400 K",
        build=lambda x, n15=ENRICH["N15"]: [(fuel_nitride(x, n15=n15), 0.30), (sic(), 0.15), (helium(), 0.55)],
        variants={"natural N": dict(n15=NAT["N15"])},
    ),
    "B4": dict(
        title="NaCl-(U,Pu)Cl3 circulating fuel salt (core region all salt)",
        T_rep=1200.0, coolant_index=None,
        assumptions="core = 100% salt, 60 NaCl - 40 (U,Pu)Cl3 mol%, 3.3 g/cm3 (approx.); Cl-37 99%",
        build=lambda x, cl37=ENRICH["Cl37"]: [(fuel_chloride(x, cl37=cl37), 1.0)],
        variants={"natural Cl": dict(cl37=NAT["Cl37"])},
    ),
    "B4-natCl": dict(
        title="NaCl-(U,Pu)Cl3 fuel salt with natural chlorine",
        light=True, T_rep=1200.0, coolant_index=None,
        assumptions="as B4 with natural Cl (24.2% Cl-37)",
        build=lambda x: [(fuel_chloride(x, cl37=NAT["Cl37"]), 1.0)],
        variants={},
    ),
    "B5-W": dict(
        title="Pb-cooled UN-W cermet block (natural W)",
        T_rep=1500.0, coolant_index=1,
        assumptions="cermet 60% (UN 60 vol% at 13.5 g/cm3 + W 40 vol% at 19.3); Pb 35% at 10.0; void 5%",
        build=lambda x, wvec=None: [(cermet(x, tungsten(wvec)), 0.60), (lead(), 0.35), (void(), 0.05)],
        variants={},
    ),
    "B5-W184": dict(
        title="Pb-cooled UN-W cermet, W-184 enriched to 95% (approx.)",
        light=True, T_rep=1500.0, coolant_index=1, assumptions="as B5-W, W 95% W-184",
        build=lambda x: [(cermet(x, tungsten(w_enriched("W184"), name="W184")), 0.60), (lead(), 0.35), (void(), 0.05)],
        variants={},
    ),
    "B5-W186": dict(
        title="Pb-cooled UN-W cermet, W-186 enriched to 95% (approx.)",
        light=True, T_rep=1500.0, coolant_index=1, assumptions="as B5-W, W 95% W-186",
        build=lambda x: [(cermet(x, tungsten(w_enriched("W186"), name="W186")), 0.60), (lead(), 0.35), (void(), 0.05)],
        variants={},
    ),
    "B5-Mo": dict(
        title="Pb-cooled UN-Mo cermet block (natural Mo)",
        light=True, T_rep=1500.0, coolant_index=1,
        assumptions="cermet 60% (UN 60 vol% at 13.5 + Mo 40 vol% at 10.2); Pb 35% at 10.0; void 5%",
        build=lambda x: [(cermet(x, molybdenum()), 0.60), (lead(), 0.35), (void(), 0.05)],
        variants={},
    ),
    "B6": dict(
        title="Li heat-pipe monolith, (U,Pu)N in Mo block",
        T_rep=1500.0, coolant_index=2,
        assumptions="fuel (U,Pu)N 60% at 13.0 (N-15 99.9%); Mo block and heat-pipe walls 25% at 10.2; "
                    "Li liquid in wicks 3% at 0.45 (Li-7 99.99%); vapour space and gaps 12% (void)",
        build=lambda x, li7=ENRICH["Li7"]: [(fuel_nitride(x), 0.60), (molybdenum(), 0.25),
                                            (lithium(li7), 0.03), (void(), 0.12)],
        variants={"natural Li": dict(li7=NAT["Li7"])},
    ),
}
