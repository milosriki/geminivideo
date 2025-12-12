# Alignment Checklist for Geminivideo

Use this checklist to ensure configuration and logic alignment across all services.

## Before Release

- [ ] Run alignment checker: `python3 scripts/check_alignment.py`
- [ ] All tests pass: `python3 -m pytest tests/ -v`
- [ ] Security scan clean (CodeQL in CI)
- [ ] Review `ALIGNMENT_REPORT.md` for any issues

## After Configuration Changes

### When modifying `shared/config/weights.yaml`:
- [ ] Verify psychology_weights sum to 1.0
- [ ] Verify hook_weights sum to 1.0
- [ ] Verify technical_weights sum to 1.0
- [ ] Verify demographic_weights sum to 1.0
- [ ] Verify novelty_weights sum to 1.0
- [ ] Run: `python3 scripts/check_alignment.py`
- [ ] Run: `pytest tests/test_logic_alignment.py -v`

### When modifying `shared/config/scene_ranking.yaml`:
- [ ] Verify weights sum to 1.0
- [ ] Check all services reload config
- [ ] Run: `python3 scripts/check_alignment.py`
- [ ] Run: `pytest tests/test_logic_alignment.py -v`

### When modifying `shared/config/*.json`:
- [ ] Validate JSON format
- [ ] Check schema compatibility
- [ ] Test with affected services
- [ ] Run integration tests

## After Logic Changes

### When modifying scoring in `gateway-api`:
- [ ] Update tests if formula changed
- [ ] Verify composite weights still sum to 1.0
- [ ] Check alignment with drive-intel
- [ ] Run: `python3 scripts/check_alignment.py`
- [ ] Run: `pytest tests/test_ranking.py -v`

### When modifying ranking in `drive-intel`:
- [ ] Update tests if formula changed
- [ ] Verify ranking weights still sum to 1.0
- [ ] Check alignment with gateway-api
- [ ] Run: `python3 scripts/check_alignment.py`
- [ ] Run: `pytest tests/test_integration.py -v`

## Adding New Services

When adding a new service that uses scoring/ranking:

- [ ] Use `CONFIG_PATH` environment variable
- [ ] Load from `shared/config/` directory
- [ ] Implement fallback defaults
- [ ] Add to alignment checker
- [ ] Add integration tests
- [ ] Update documentation

## Validation Commands

```bash
# Quick alignment check
python3 scripts/check_alignment.py

# Run alignment tests
python3 -m pytest tests/test_logic_alignment.py -v

# Run all tests
python3 -m pytest tests/ -v

# Check specific service
cd services/gateway-api && npm test
cd services/drive-intel && pytest
```

## Weight Sum Formula

All weight configurations MUST satisfy:

```
sum(weights.values()) = 1.0 ± 0.01
```

### Current Weight Groups:
- **Psychology**: pain_point + transformation + urgency + authority + social_proof = 1.0
- **Hook**: has_number + has_question + motion_spike + first_3s_text = 1.0
- **Technical**: resolution + audio + lighting + stabilization = 1.0
- **Demographic**: persona_match + age_range + fitness_level + trigger_alignment = 1.0
- **Novelty**: semantic_uniqueness + visual_diversity = 1.0
- **Scene Ranking**: motion + object + text + transcript + novelty + technical = 1.0
- **Gateway Composite**: psychology*0.3 + hook*0.25 + technical*0.2 + demographic*0.15 + novelty*0.1 = 1.0

## Common Issues

### Issue: Weights don't sum to 1.0
**Solution:** Recalculate and normalize weights in config file, then run alignment checker

### Issue: Service not loading shared config
**Solution:** Check CONFIG_PATH environment variable, verify file paths are correct

### Issue: Alignment checker fails
**Solution:** Review error messages, check config file format, verify all required files exist

### Issue: Tests fail after config change
**Solution:** Update test expectations, verify logic changes are intentional

## Quick Reference

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Alignment | `python3 scripts/check_alignment.py` | 0 issues, 0 warnings |
| Tests | `pytest tests/test_logic_alignment.py -v` | 23/23 passed |
| Security | CodeQL in CI | 0 vulnerabilities |
| Config Files | Manual review | All YAML/JSON valid |

## Documentation

- Full technical details: `ALIGNMENT_REPORT.md`
- Quick summary: `VALIDATION_SUMMARY.md`
- This checklist: `.github/ALIGNMENT_CHECKLIST.md`

## Contact

For questions about alignment:
- Review alignment report
- Check test examples in `tests/test_logic_alignment.py`
- Review alignment checker code in `scripts/check_alignment.py`

---

Last Updated: December 12, 2025
