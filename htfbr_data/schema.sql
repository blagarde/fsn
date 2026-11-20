-- HT-FBR property database. Every number traces to a source and, where fetched, a raw artifact.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source (
    source_id   TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    publisher   TEXT,
    url         TEXT,
    version     TEXT,
    tier        TEXT CHECK (tier IN ('A', 'B', 'C')),  -- A evaluated/primary, B compiled handbook, C single paper or computed
    kind        TEXT,   -- nuclear-structure, nuclear-reaction, thermochemistry, thermophysical, phase-diagram, materials
    access      TEXT,   -- api, download, manual, licensed
    status      TEXT,   -- implemented, planned, manual, blocked
    license     TEXT,
    citation    TEXT,
    notes       TEXT
);

-- One row per raw file fetched (or zip member extracted). Re-fetches with new content get a new row.
CREATE TABLE IF NOT EXISTS artifact (
    artifact_id  INTEGER PRIMARY KEY,
    source_id    TEXT NOT NULL REFERENCES source (source_id),
    url          TEXT NOT NULL,
    member       TEXT NOT NULL DEFAULT '',
    sha256       TEXT NOT NULL,
    bytes        INTEGER,
    retrieved_at TEXT NOT NULL,
    local_path   TEXT NOT NULL,
    UNIQUE (url, member, sha256)
);

CREATE TABLE IF NOT EXISTS ingest_run (
    run_id       INTEGER PRIMARY KEY,
    ingester     TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    status       TEXT,
    rows         INTEGER,
    message      TEXT,
    code_version TEXT
);

-- Ground-state nuclide data (IAEA LiveChart / ENSDF).
CREATE TABLE IF NOT EXISTS nuclide (
    z               INTEGER NOT NULL,
    a               INTEGER NOT NULL,
    symbol          TEXT NOT NULL,
    abundance_pct   REAL,
    abundance_unc   REAL,
    stable          INTEGER NOT NULL,
    half_life_s     REAL,
    half_life_unc_s REAL,
    half_life_text  TEXT,
    decay_modes     TEXT,   -- JSON list of {mode, pct, unc}
    spin_parity     TEXT,
    atomic_mass_uu  REAL,   -- micro-u, as published
    atomic_mass_unc REAL,
    artifact_id     INTEGER REFERENCES artifact (artifact_id),
    PRIMARY KEY (z, a)
);

-- Thermochemical species and tables (NIST-JANAF).
CREATE TABLE IF NOT EXISTS species (
    species_id  INTEGER PRIMARY KEY,
    formula     TEXT NOT NULL,   -- as published, e.g. Al2O3
    phase       TEXT NOT NULL,   -- cr, l, g, cr,l, ref ...
    name        TEXT,
    cas         TEXT,
    table_id    TEXT NOT NULL UNIQUE,  -- e.g. JANAF Al-004
    artifact_id INTEGER REFERENCES artifact (artifact_id)
);

CREATE TABLE IF NOT EXISTS thermo (
    species_id INTEGER NOT NULL REFERENCES species (species_id),
    row_index  INTEGER NOT NULL,  -- transition temperatures appear twice in JANAF
    T_K        REAL NOT NULL,
    cp         REAL,   -- J/(K mol)
    s          REAL,   -- J/(K mol)
    gef        REAL,   -- -[G-H(298.15)]/T, J/(K mol)
    h_rel      REAL,   -- H-H(298.15), kJ/mol
    dfH        REAL,   -- kJ/mol
    dfG        REAL,   -- kJ/mol
    log_kf     REAL,
    note       TEXT,
    PRIMARY KEY (species_id, row_index)
);

-- Spectrum-averaged cross sections derived from evaluated libraries.
CREATE TABLE IF NOT EXISTS weighting (
    weighting_id TEXT PRIMARY KEY,   -- thermal_2200, watt_u235, ri_1overE ...
    description  TEXT NOT NULL,
    definition   TEXT NOT NULL,      -- exact formula and bounds
    reference    TEXT
);

CREATE TABLE IF NOT EXISTS xs_avg (
    z             INTEGER NOT NULL,
    a             INTEGER NOT NULL,
    library       TEXT NOT NULL,      -- source_id of the evaluation
    mt            INTEGER NOT NULL,
    reaction      TEXT NOT NULL,
    weighting_id  TEXT NOT NULL REFERENCES weighting (weighting_id),
    temperature_K REAL NOT NULL,
    value_b       REAL NOT NULL,
    method        TEXT NOT NULL,      -- e.g. NJOY2016 RECONR/BROADR via openmc.data
    artifact_id   INTEGER REFERENCES artifact (artifact_id),
    PRIMARY KEY (z, a, library, mt, weighting_id, temperature_K)
);

-- Generic property values, mainly hand-entered from handbooks and papers.
CREATE TABLE IF NOT EXISTS property (
    property_id INTEGER PRIMARY KEY,
    material    TEXT NOT NULL,
    quantity    TEXT NOT NULL,     -- controlled vocabulary in config/quantities.yaml
    value       REAL NOT NULL,
    unc         REAL,
    unc_kind    TEXT,              -- 1sigma, 2sigma, range, stated, none
    unit        TEXT NOT NULL,     -- as published
    value_si    REAL NOT NULL,
    unit_si     TEXT NOT NULL,
    T_K         REAL,
    P_Pa        REAL,
    phase       TEXT,
    conditions  TEXT,
    source_id   TEXT NOT NULL REFERENCES source (source_id),
    locator     TEXT NOT NULL,     -- page, table, equation or DOI fragment
    method      TEXT,              -- measured, evaluated, correlation, calculated
    artifact_id INTEGER REFERENCES artifact (artifact_id),
    entered_by  TEXT,
    entered_at  TEXT NOT NULL,
    notes       TEXT
);

-- Natural-element cross sections: abundance-weighted isotopes, only where every
-- naturally occurring isotope has an evaluation (coverage column says how much).
CREATE VIEW IF NOT EXISTS v_xs_natural AS
SELECT n.z, n.symbol, x.library, x.mt, x.reaction, x.weighting_id, x.temperature_K,
       SUM(n.abundance_pct / 100.0 * x.value_b) AS value_b,
       SUM(n.abundance_pct) AS coverage_pct
FROM nuclide n
JOIN xs_avg x ON x.z = n.z AND x.a = n.a
WHERE n.abundance_pct > 0
GROUP BY n.z, x.library, x.mt, x.weighting_id, x.temperature_K;
