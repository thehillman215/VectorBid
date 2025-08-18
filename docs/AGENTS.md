# Agents

## DataSynth Agent
- Owns `tools/pbs_synth/`.
- Generates deterministic synthetic PBS datasets.

## Parser Agent
- Owns `app/services/pbs_parser/`.
- Parses synthetic datasets into normalized contracts.

## Extension Rules
- Prefer pure functions and deterministic behavior.
- Keep I/O at the edges; models stay side-effect free.

## Developer Checklist
- Run `pre-commit run --files <changed>`.
- Execute `pytest -q` before committing.
- Update docs and tests alongside code.

## Self-Tasking
Agents may propose follow-up improvements here before implementing them.
