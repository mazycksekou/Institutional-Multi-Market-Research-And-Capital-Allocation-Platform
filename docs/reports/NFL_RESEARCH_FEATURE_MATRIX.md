# NFL Research Feature Matrix

This matrix maps features to research, hypothesis, experiment, model, and future Worldview usefulness.

| Research Theme | Feature IDs | Research Usefulness | Hypothesis Usefulness | Experiment Usefulness | Model Usefulness | Worldview Usefulness |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline market efficiency | NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F009 NFL_F010 | high | high | high | high | high |
| Schedule fatigue | NFL_F011 NFL_F012 | high | high | high | medium | high |
| Weather effects | NFL_F013 NFL_F014 | high | high | high | medium | high |
| Availability and lineup | NFL_F015 NFL_F016 NFL_F017 NFL_F018 NFL_F035 | high | high | high | high | high |
| Team strength | NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 | high | high | high | high | high |
| Volatility and regression | NFL_F024 NFL_F025 | medium | high | medium | medium | medium |
| Unit matchups | NFL_F026 NFL_F027 NFL_F028 | high | high | medium | high | high |
| Special teams | NFL_F029 | medium | medium | medium | low to medium | medium |
| Officials | NFL_F030 NFL_F031 | medium | medium | medium | low to medium | medium |
| Coaching continuity | NFL_F032 NFL_F033 | high | high | high | medium | high |
| Player priors | NFL_F034 NFL_F036 NFL_F037 NFL_F038 | high later | high later | deferred | deferred | high later |
| Governance and explainability | NFL_F039 NFL_F040 NFL_F041 | high | high | high | governance | high |

## Worldview Use

The future Worldview layer should use this registry to:

- discover supported feature families
- identify missing prerequisites
- reject unsupported hypotheses
- request experiments only against fields with known timing and leakage status
- produce evidence packages tied to feature IDs and dependency versions
