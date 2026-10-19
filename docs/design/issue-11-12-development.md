# Development and evidence record (#11/#12)

- Protocol/research committed first: `0b0f5a9`, before any live measurement or
  heldout request inspection. No parser, policy, prompt or compiler changes.
- Observed RED: missing `scripts.rule_baseline`; missing evaluator
  `end_to_end_success` (`KeyError`, 1 failed/10 passed); missing report helper;
  missing metering module. Tests committed before core implementation.
- Pairing adversary RED: negative prediction with `safe_negative=False` was
  incorrectly credited. Fix requires the integrity-checked flag; GREEN.
- Focused GREEN after implementation: 25 tests. Full offline implementation head:
  534 passed, 41 opt-in skipped. Ruff and strict mypy passed.
- Inference frozen source: `3abcf27`. Full development and heldout inference
  completed once for each system; no outcome-driven retries. Probe is separate.
- CI `39329554595` observed 6 failures/528 passes/41 skips on Python 3.12
  because fresh install selected TF 13.1.1. Pin research quality lane to 13.1.0;
  the Python 3.11–3.13 and wheel jobs then passed on `ff5cdfd`.
  Separate compatibility work is #45. Version/source gates were not weakened.
- Post-inference auditor coverage RED: expected gloss/pointed probes, got zero.
  Extend only the offline auditor to all three literal families and preserve
  original live artifacts byte-for-byte. Source `bfbfe3e`; five report tests
  GREEN. Supplementary real-BHSA audit is separate from the frozen live JSON.
- Replayed all 86 canonical native gold count/signature cases, 44 development
  plus 42 heldout. No benchmark edits or gold rewriting.
- Independent recomputation validates IDs/completeness, class counts, equivalent
  and safe-negative counts, end-to-end success, complete usage and model cost
  across all four public system/partition artifacts.
- Independently inspected all 26 emitted compiled rule structures: exact node
  type, feature/value conjunction and output column match intended atomic
  requests. Jev emitted no IR. See the explicit single-reviewer intent audit.
- Independent hostile metric probe: 23 malformed/missing/NaN/negative/bool/infinite
  metrics cannot obtain a passing recommendation.
- Final exact-head checks, raw annotation oracles and formal independent review
  are recorded on PR #44; no merge until all remaining gates pass.

The measured result is a no-go, not permission to tune against the exposed v2
heldout. Further development-only diagnosis and fresh evaluation are #46.

The supplementary actual-BHSA candidate audit recalled all 12 literal targets
(6 development, 6 heldout), verifying identical full schema identity to the
initial study. Original public live JSON files remain byte-identical to the
source-commit measurement output.
