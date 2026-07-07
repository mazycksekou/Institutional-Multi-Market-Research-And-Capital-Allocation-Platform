# NFL Streamlit Feature Matrix

This matrix defines where registry features should appear in the future dashboard.
It does not implement dashboard code.

| Streamlit Area | Feature IDs | Purpose |
| --- | --- | --- |
| Dataset readiness | NFL_F001 NFL_F002 NFL_F003 NFL_F004 | show whether the foundation dataset is complete |
| Provider readiness | NFL_F005 NFL_F006 NFL_F007 NFL_F008 NFL_F013 NFL_F015 NFL_F017 NFL_F030 | show which external or local source lanes are available |
| Feature readiness | NFL_F011 NFL_F012 NFL_F014 NFL_F016 NFL_F018 NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F033 NFL_F035 | show which P0 and P1 features are buildable |
| Backtest | NFL_F004 NFL_F008 NFL_F010 NFL_F040 | show replay inputs and settled outcomes |
| Calibration | NFL_F004 NFL_F010 NFL_F040 | show confidence and calibration evidence |
| ROI | NFL_F004 NFL_F008 NFL_F040 | show backtest performance after implementation |
| CLV | NFL_F008 NFL_F010 | show closing-line performance evidence |
| Research | NFL_F024 NFL_F025 NFL_F026 NFL_F027 NFL_F028 NFL_F029 NFL_F031 NFL_F034 NFL_F039 NFL_F041 | show optional experiments and findings |
| Diagnostics | NFL_F009 NFL_F014 NFL_F016 NFL_F039 NFL_F041 | explain which context drove feature relevance |
| Feature importance | NFL_F019 NFL_F020 NFL_F021 NFL_F022 NFL_F023 NFL_F026 NFL_F027 NFL_F039 | compare feature contribution after models exist |
| Explainability | NFL_F011 NFL_F012 NFL_F014 NFL_F016 NFL_F019 NFL_F020 NFL_F026 NFL_F027 NFL_F039 | explain model and no-trade decisions |
| No-trade reasons | NFL_F010 NFL_F014 NFL_F015 NFL_F016 NFL_F030 NFL_F040 | expose missing data, high leakage risk, poor calibration, or unsafe timing |
| Worldview experiment readiness | all registry features | show which hypotheses are supported, missing, or deferred |
