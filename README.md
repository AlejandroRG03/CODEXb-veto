# CODEX-b Veto

Tools and pipelines for the CODEX-b Veto system, using VELO detector data to reject background events in real time.

## What's here

- **SimulationPipeline/** — `main.py` and `submit.condor` to generate MC signal/background samples pointing at CODEX-b, distributed via HTCondor.
- **DecFiles/** — DecFiles (`.dec`) describing physics events that fire in CODEX-b and CODEX-beta, used as input to Gauss.
- **GNN/** — Graph Neural Network pipeline for the veto decision: data preparation (graph construction from VELO clusters), the InteractionNetwork model itself, and PyTorch Lightning training code.
