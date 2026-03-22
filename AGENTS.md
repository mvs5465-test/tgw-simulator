# AGENTS.md

Instructions for human + AI contributors in this repository.

## Product

- `tgw-simulator` is a small CLI simulator for AWS Transit Gateway plus Private Hosted Zone cross-account behavior.
- The repo is intentionally lightweight and explanation-oriented.

## Architecture

- `tgw_sim/cli.py` owns the command-line entry behavior.
- `tgw_sim/models.py` and `storage.py` hold the simulated state and persistence shape.
- `tgw_sim/__main__.py` supports `python -m tgw_sim`.

## Working Rules

- Keep the simulator simple enough to reason about.
- Prefer explicit domain modeling over clever abstractions.
- Preserve the educational/explanatory nature of the repo when adding features.

## Verification

- Run `python -m tgw_sim` for basic CLI sanity.
- If you add commands or state transitions, document them in the README in the same change.
