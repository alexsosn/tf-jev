# Design: explicit pinned and latest-supported TF lanes (#45)

1. Observe full-suite RED on actual TF 13.1.1 before test/CI corrections.
2. Synthetic saved tiny corpus fixtures record the actual installed TF version;
   immutable schema identity assertion compares with installed package metadata.
   These are fixture corrections, not changes to canonical BHSA evidence.
3. Source-drift/missing-source boundary tests explicitly simulate the pinned TF
   version to test that stage in isolation. Add a separate wrong-version test that
   proves canonical source reads and backend/model setup never occur afterward.
4. Keep existing Python 3.11/3.12/3.13 quality matrix explicitly pinned to TF 13.1.0.
   Add a latest-supported Python 3.12 lane that resolves the advertised
   `text-fabric>=13.1,<14` dependency and runs the complete suite/lint/mypy. Keep
   distribution smoke on the ordinary unconstrained package dependencies.
5. Validate native conformance on a real BHSA corpus under 13.1.1 and full offline
   tests under both runtimes. Explicit canonical benchmark attempts on 13.1.1
   must still reject version mismatch. No benchmark gold/source hash rewriting,
   model calls, parser changes or widening of package dependency range.
6. Exact final-head tests and logically independent adversarial review before
   merge; record actual versions and source-diff/native evidence. The compatibility
   result does not turn 13.1.1 into the pinned evidence version or certify all
   future 13.x releases; the floating CI lane detects subsequent changes.
