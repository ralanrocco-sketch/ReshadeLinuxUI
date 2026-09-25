# Upstream installer provenance

- Project: [kevinlekiller/reshade-steam-proton](https://github.com/kevinlekiller/reshade-steam-proton)
- File: [reshade-linux.sh](https://github.com/kevinlekiller/reshade-steam-proton/blob/main/reshade-linux.sh)
- Downloaded from the upstream `main` branch on 2026-09-24.
- The upstream script's copyright and GPL-2.0-or-later notice are retained in the file.

The GUI currently feeds the script's expected install/uninstall answers through stdin. It does not modify the installer logic. Upstream script updates should be reviewed before replacing this vendored copy because its prompt order is part of the wrapper interface.

SHA-256 of the vendored script: `19dc7d5d602f963965dfd0327802e06c37f845133b5b2388f9b483c175e13921`.
