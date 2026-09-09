# External data inventory

No scientific dataset is committed to this repository. Paths are supplied on
the command line or through the documented environment variables.

| Dataset/product | Purpose | Variables/content | Period/resolution | Access/provenance |
|---|---|---|---|---|
| Atlantic extratropical cyclone tracks | Cyclone positions and population support | track ID, time, centre, vorticity | 1979–2020; original 1-hourly, selected at exact 3-hour times | Zenodo `10.5281/zenodo.18133432` |
| Archived article LEC results | Frozen lifecycle windows and legacy validation | integrated LEC terms, `periods.csv`, vertical terms | Per cyclone, 3-hourly | Zenodo `10.5281/zenodo.18243447` |
| `energy_cache.parquet` | Defines the authoritative 3,820-cyclone population and legacy paired values | Phase means of LEC terms | Lifecycle periods | External path; SHA-256 stored in run provenance |
| ERA5 pressure levels | Corrected LEC computation | `u`, `v`, `t`, `w`, `z` | Per cyclone; 3-hourly; 37 requested levels | Copernicus Climate Data Store; requests described by run config |
| Corrected run-root | State and validated per-cyclone outputs | config, provenance, manifest, SQLite, tracks, phase windows, ERA5 staging, LEC results | One production run | `/p1-swell/danilocs/lec_climatology_corrected_v2` on `swell` |

Credentials are read from a secure external inventory. They must never be
copied into this repository, logs, provenance, or documentation.

Derived caches can be rebuilt with scripts under
`scripts/lec_climatology_rerun/`. Small final comparison tables, figures and
reports may be versioned; large paired parquet tables remain ignored.
