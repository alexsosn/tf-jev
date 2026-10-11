# Design: auditable invisible Unicode in native Text-Fabric literals

## Contract
Retain `CorpusSchema.validate_value` as the authoritative membership check for string EQ/NE predicates; do not silently normalize, strip or rewrite source feature values. Add a narrow, documented reject-set for **audit-hostile format controls** in `compiler._escape`. Fail with a **constant generic** `CompileError("unrepresentable literal value")` without printing corpus text. Existing C0/DEL/surrogate and non-space whitespace checks remain. Explicitly allow script joiners/directional marks U+200C/U+200D/U+200E/U+200F **subject to native TF execution tests** rather than forbidding every `Cf`.

Safety-critical code runs *after exact corpus membership validation* and *before rendering any part of a native query*; a set with mixed safe/unsafe values fails atomically. The literal remains untouched before passing to native TF where permitted; only original TF syntax escapes for backslash, space and vertical bar are applied. No `ascii()` escaping is performed on native values (unlike model-facing `Option.description`).

## Tests / gates
- RED: attested U+202E/U+2066/U+200B/soft hyphen in synthetic TF corpus should raise CompileError; current compiler allows them.
- GREEN: successfully round-trip U+200C/U+200D/U+200E/U+200F and e+combining acute using native TF search (EQ and NE) compared to independent raw feature value equality and inequality.
- Boundary: a benign selected value must search correctly while another corpus node carries rejected controls; untrusted metadata must not poison selection. Reject a set containing any forbidden literal (not just an all-bad predicate).
- Native conformance: fail any TF native tokenizer mismatch rather than assuming Unicode policies imply exact matching.
- Review: independently verify the code's reject list against research and check actual TF native-result oracle, escaping correctness, no v2 held-out data and no model/text injection.

The issue is independent of parser #9 and historical BHSA benchmark #10. Only source compiler/tests/docs change. Run Python 3.11–3.13 Ruff, strict mypy, pytest, wheel distribution on the exact reviewed SHA before squash merge and issue closure.
