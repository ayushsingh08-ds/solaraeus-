## 6. Verification & Replication Commands

To reproduce all unit tests, adversarial suites, independent analytical checks, mutation sensitivity tests, and master evaluation runs:

```powershell
# 1. Run complete automated test suite (99 tests passing)
python -m pytest -o pythonpath=src -v

# 2. Run master independent scientific audit cleanup, provenance generation, & mutation suite
python examples/run_independent_audit.py

# 3. Run master publication validation suite (34 experiments, 130 trials, multi-trial stats, 9 plots)
python examples/run_publication_validation.py

# 4. Run mutation sensitivity unit tests specifically
python -m pytest -o pythonpath=src tests/test_mutation_audits.py -v

# 5. Run baseline comparative demonstration
python examples/compare_full_incremental.py
```

---

