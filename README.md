# TGW Simulator

A simple Transit Gateway + Private Hosted Zone simulator to understand AWS cross-account networking.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m tgw_sim
```

## Structure

- `tgw_sim/cli.py` handles command-line execution
- `tgw_sim/models.py` defines the simulated networking entities
- `tgw_sim/storage.py` manages persisted simulator state

## Notes

- This repo is intentionally lightweight and explanation-oriented.
- The current dependency footprint is minimal: `click` plus the standard library.
- Treat the simulator as a teaching and reasoning aid rather than a full AWS emulator.
