# Data sources

No raw dataset is stored in Git. Paths below identify the audited inputs; no
authentication material is included.

## Original energetic cyclone dataset

- Path: `/Users/danilocoutodesouza/Documents/Programs_and_scripts/energetic_patterns_cyclones_south_atlantic/tracks_SAt_filtered/tracks_SAt_filtered_with_energetics.csv`
- Size: 180,778,076 bytes
- Modified: 2024-09-14 18:46:12 -0300
- SHA-256: `bf1059ab2f1896c6df942a290d7676bce701f6d3cbf7ac9193f5c6b51d63cc26`
- Shape from shell inspection: 631,009 data rows, 31 columns, 6,789 unique `track_id` values
- Header starts with `track_id,date,lon vor,lat vor,vor42,region,period` and contains the archived LEC reservoirs, conversions, boundary terms, tendencies and residuals.

The canonical legacy cache used by the maintained comparison is external:

- `/Users/danilocoutodesouza/Documents/Programs_and_scripts/paper_energy_patterns/data/energy_cache.parquet`
- 6,019,435 bytes
- SHA-256: `7a24617e56595737075a8f9975dd0018069196292eab32fd8f5ba2a49e25a16d`
- Validated population: 6,789 cyclones and 25,000 lifecycle rows

## Corrected data

- Host alias: `swell`
- Production root: `/p1-swell/danilocs/lec_climatology_corrected_v2`
- Inspected securely with the existing SSH configuration; no password file was read or printed.
- `population_manifest.csv`: 758,556 bytes, 3,820 rows; columns `track_id,start,end,n_timesteps,lifecycle_hours,track_sha256,phase_windows_sha256,download_envelope_degrees2,is_pilot`
- `lec_results/`: 103,140 files, 3,148,194,688 bytes at audit time
- `phase_windows/`: 3,820 files
- Corrected cache actually used by the validated comparison: `/p1-swell/danilocs/paper_energy_patterns/data/corrected/energy_cache_corrected.parquet`, 4,068,203 bytes, SHA-256 `c5efb8242e83aaa85ebd39cc12d5630fc0f70608775a67d32821dc0097d8d4d3`
- Validated corrected population: 3,820 cyclones and 15,829 lifecycle rows (15,280 primary-phase rows)

No remote data file was downloaded during this reorganization. Existing
validated figures and compact tables were reused.

## Fail-fast discrepancy recorded

The local processed track file named in the existing comparison provenance,
`/Users/danilocoutodesouza/Documents/Programs_and_scripts/paper_energy_patterns/data/tracks_SAt_filtered_with_energetics_processed.csv`, was found at 66,337,418 bytes with SHA-256
`84134a302ad369cb75af7858c57d838b204588e3957d6f5bfa05148b564544f4`.
The validated provenance expects SHA-256
`552a7a0f1218450834c6d34addbec6bc6dda18e1f2a3f21d663a71bccc636b1d`;
the file with that expected hash exists on `swell` at the documented path and
is 66,328,188 bytes. The local file was therefore not used and no figures were
regenerated from it.
