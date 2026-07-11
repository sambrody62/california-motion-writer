"""
Fact-fidelity gate — deterministic post-generation correction of LLM motion
text before it can reach a court PDF (real-LLM findings L1-L4, L7, L8, L15).

Pure stdlib; no imports from other app services.
"""
from app.services.fact_gate.types import Correction, GateContext, GateResult

__all__ = ["Correction", "GateContext", "GateResult"]
