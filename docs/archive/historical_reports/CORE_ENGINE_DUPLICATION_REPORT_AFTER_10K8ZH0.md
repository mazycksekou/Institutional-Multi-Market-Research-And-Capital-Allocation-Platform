# Core Engine Duplication Report (After 10K8ZH0)

## Duplicated Logic

- `american_to_implied_probability` defined in `quant_engine.py` and in `src/core/math_utils.py`.
- `implied_probability_from_american` alias in both.
- `expected_value_per_unit` defined in both places.
- `kelly_fraction` / `suggested_stake` / `edge_percentage` / `no_vig_probabilities` appear in `quant_engine.py` and `src/core/math_utils.py`.

All such duplicates are intentional and kept for backward compatibility until a formal migration phase.
