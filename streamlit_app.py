"""Local Streamlit operator dashboard.

Run:

    streamlit run streamlit_app.py

This UI is paper/testing only. It does not place real bets.
"""

from __future__ import annotations

from pathlib import Path

try:
    import pandas as pd
    import streamlit as st
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dashboard dependency. Install locally with: "
        "python -m pip install streamlit pandas"
    ) from exc


from automation_scheduler.streamlit_dashboard_data import (
    DATA_LIBRARY_PATHS,
    EASY_LABELS,
    REGRESSION_TACTICS,
    RISK_PRESETS,
    SAFE_DEFAULTS,
    build_bankroll_curve_rows,
    compact_counts,
    file_inventory,
    generate_latest_dashboard_outputs,
    get_available_profile_options,
    get_system_health_rows,
    load_canonical_rows_for_dashboard,
    load_dashboard_snapshot,
    parse_feature_weights,
    preview_path,
    run_model_test,
    simple_home_cards,
)
from automation_scheduler.historical_data_sources import (
    get_historical_data_source_rows,
    get_priority_import_sources,
    get_source_status_counts,
    get_model_testing_source_plan,
    source_is_projection_ready,
    summarize_source_registry,
)


st.set_page_config(
    page_title="Betting Model Operator Dashboard",
    page_icon="??",
    layout="wide",
)


def df(rows):
    return pd.DataFrame(list(rows or []))


def show_easy_dictionary() -> None:
    with st.expander("Simple word helper", expanded=False):
        rows = [{"field": key, "simple meaning": value} for key, value in sorted(EASY_LABELS.items())]
        st.dataframe(df(rows), use_container_width=True, hide_index=True)


def metric_row(items):
    columns = st.columns(max(1, len(items)))
    for column, (label, value, help_text) in zip(columns, items):
        column.metric(label, value, help=help_text)


def show_curve(curve_rows):
    rows = list(curve_rows or [])
    if not rows:
        st.info("No graph data yet.")
        return

    curve_df = df(rows)
    if "decision_index" in curve_df.columns and "bankroll" in curve_df.columns:
        st.line_chart(curve_df.set_index("decision_index")["bankroll"])

    with st.expander("Graph table", expanded=False):
        st.dataframe(curve_df, use_container_width=True, hide_index=True)


def show_run_result(result: dict) -> None:
    summary = dict(result.get("backtest_summary") or {})
    readiness = dict(result.get("readiness") or {})
    curve = list(result.get("bankroll_curve") or [])

    st.subheader("Easy Result")
    metric_row(
        [
            ("Rows used", result.get("rows_used"), "How many rows were tested."),
            ("Bets", summary.get("bets"), "How many pretend bets were made."),
            ("Money won/lost", summary.get("profit_loss"), "Profit or loss from the test."),
            ("Return %", summary.get("roi_percent"), "Percent return from the test."),
            ("Worst drop %", summary.get("max_drawdown_percent"), "Biggest drop from the high point."),
            ("Ready?", readiness.get("verdict"), "Simple model readiness answer."),
        ]
    )

    st.info(readiness.get("simple_explanation") or "No simple explanation available.")

    st.subheader("Money Up/Down Graph")
    show_curve(curve)

    tab1, tab2, tab3, tab4 = st.tabs(["Counts", "Decisions", "Settings", "Raw JSON"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write("Sports")
            st.dataframe(
                df([{"sport": k, "count": v} for k, v in dict(summary.get("sport_counts") or {}).items()]),
                use_container_width=True,
                hide_index=True,
            )
        with c2:
            st.write("Markets")
            st.dataframe(
                df([{"market": k, "count": v} for k, v in dict(summary.get("market_counts") or {}).items()]),
                use_container_width=True,
                hide_index=True,
            )
        with c3:
            st.write("Profiles")
            st.dataframe(
                df([{"profile": k, "count": v} for k, v in dict(summary.get("profile_counts") or {}).items()]),
                use_container_width=True,
                hide_index=True,
            )

    with tab2:
        st.dataframe(df(curve), use_container_width=True, hide_index=True)

    with tab3:
        st.json(result.get("inputs") or {})
        st.json(result.get("strategy_config") or {})

    with tab4:
        st.json(result)


def sidebar_inputs():
    st.sidebar.header("Test Settings")

    risk_preset = st.sidebar.selectbox("Risk preset", list(RISK_PRESETS.keys()), index=1)
    preset = RISK_PRESETS[risk_preset]
    st.sidebar.caption(preset["explanation"])

    starting_bankroll = st.sidebar.number_input(
        "Starting money",
        min_value=1.0,
        value=float(SAFE_DEFAULTS["starting_bankroll"]),
        step=100.0,
        help="Pretend money to start the paper test.",
    )

    default_unit = float(SAFE_DEFAULTS["unit_size"])
    if preset.get("unit_size_percent") is not None:
        default_unit = max(1.0, round(starting_bankroll * float(preset["unit_size_percent"]) / 100.0, 2))

    unit_size = st.sidebar.number_input(
        "Normal bet size",
        min_value=0.01,
        value=float(default_unit),
        step=1.0,
        help="Pretend amount for each normal bet.",
    )

    max_rows = st.sidebar.number_input(
        "Max rows to test",
        min_value=1,
        max_value=250000,
        value=int(SAFE_DEFAULTS["max_rows"]),
        step=500,
        help="More rows means a bigger test.",
    )

    tactic = st.sidebar.selectbox(
        "Regression tactic",
        list(REGRESSION_TACTICS.keys()),
        index=2,
        help="How the model chance is formed.",
    )
    st.sidebar.caption(REGRESSION_TACTICS[tactic]["friendly"])

    intercept = st.sidebar.slider(
        "Starting chance",
        min_value=0.01,
        max_value=0.99,
        value=float(SAFE_DEFAULTS["intercept"]),
        step=0.01,
        help="Starting chance before features move it.",
    )

    probability_floor = st.sidebar.slider(
        "Lowest chance allowed",
        min_value=0.0,
        max_value=0.5,
        value=float(SAFE_DEFAULTS["probability_floor"]),
        step=0.01,
    )

    probability_ceiling = st.sidebar.slider(
        "Highest chance allowed",
        min_value=0.5,
        max_value=1.0,
        value=float(SAFE_DEFAULTS["probability_ceiling"]),
        step=0.01,
    )

    override_existing_probability = st.sidebar.checkbox(
        "Let tactic replace old model chance",
        value=bool(SAFE_DEFAULTS["override_existing_probability"]),
    )

    feature_weight_text = st.sidebar.text_area(
        "Custom feature weights",
        value="",
        help='Optional. Example: pace_edge=0.05, injury_edge=-0.02 or {"pace_edge": 0.05}',
    )

    force_rebuild = st.sidebar.checkbox(
        "Rebuild dataset",
        value=bool(SAFE_DEFAULTS["force_rebuild_dataset"]),
        help="Re-scan local artifacts and rebuild canonical dataset.",
    )

    require_core_fields = st.sidebar.checkbox(
        "Require core fields",
        value=bool(SAFE_DEFAULTS["require_core_fields"]),
        help="Strict mode. Usually leave off during early paper testing.",
    )

    return {
        "risk_preset": risk_preset,
        "starting_bankroll": starting_bankroll,
        "unit_size": unit_size,
        "max_rows": int(max_rows),
        "tactic": tactic,
        "intercept": intercept,
        "probability_floor": probability_floor,
        "probability_ceiling": probability_ceiling,
        "override_existing_probability": override_existing_probability,
        "feature_weights": parse_feature_weights(feature_weight_text),
        "force_rebuild_dataset": force_rebuild,
        "require_core_fields": require_core_fields,
    }


st.title("?? Betting Model Operator Dashboard")
st.caption("Paper/testing control room. This screen does not place real bets.")

settings = sidebar_inputs()
show_easy_dictionary()

menu = st.sidebar.radio(
    "Main Menu",
    [
        "Operator Summary",
        "Data Library",
        "Paper Bets",
        "Backtest Dashboard",
        "Test One Sport",
        "Test All Sports",
        "Bankroll Settings",
        "Regression Tactics",
        "System Health",
        "Data Source Library",
        "Import Historical Data",
        "Data Quality Check",
        "Model Projection",
    ],
)


if menu == "Home / Explain Like I'm 8":
    st.header("Operator Summary")

    snapshot = load_dashboard_snapshot()
    cards = simple_home_cards(snapshot)

    metric_row(
        [
            ("System", cards["Is the system safe?"], "Paper/test mode status."),
            ("Start money", cards["How much money did the test start with?"], "Pretend starting money."),
            ("End money", cards["How much money did the test end with?"], "Pretend ending money."),
            ("Graph", cards["Did the graph go up or down?"], "Did the bankroll go up or down?"),
            ("Profile", cards["What sport/profile was tested?"], "Sport/model setup."),
            ("Ready?", cards["Is this ready or not ready?"], "Simple readiness answer."),
        ]
    )

    if not snapshot.get("dashboard_exists"):
        st.warning("Dashboard file is missing. Click the button below to generate it.")

    if st.button("Generate latest dashboard now", type="primary"):
        with st.spinner("Generating latest dashboard JSON and Markdown..."):
            result = generate_latest_dashboard_outputs(
                tactic=settings["tactic"],
                profile_key="all_sports",
                starting_bankroll=settings["starting_bankroll"],
                unit_size=settings["unit_size"],
                max_rows=settings["max_rows"],
                intercept=settings["intercept"],
                feature_weights=settings["feature_weights"],
                probability_floor=settings["probability_floor"],
                probability_ceiling=settings["probability_ceiling"],
                override_existing_probability=settings["override_existing_probability"],
                force_rebuild_dataset=settings["force_rebuild_dataset"],
                require_core_fields=settings["require_core_fields"],
            )
        st.success("Dashboard files generated.")
        st.json(result)

    dashboard = snapshot.get("dashboard") or {}
    curve = dashboard.get("bankroll_curve") or []
    if curve:
        st.subheader("Money Up/Down Graph")
        show_curve(curve)


elif menu == "Data Library":
    st.header("Data Library")

    inventory = file_inventory()
    st.dataframe(df(inventory), use_container_width=True, hide_index=True)

    labels = list(DATA_LIBRARY_PATHS.keys())
    selected = st.selectbox("Choose a file to read", labels)
    preview_limit = st.number_input("Preview rows", min_value=1, max_value=5000, value=200, step=100)

    path = DATA_LIBRARY_PATHS[selected]
    preview = preview_path(path, limit=int(preview_limit))

    st.caption(str(path))

    if not preview["exists"]:
        st.warning(preview["warning"])
    elif preview["kind"] == "md":
        st.markdown(preview["text"])
    else:
        rows = preview["rows"]
        st.dataframe(df(rows), use_container_width=True, hide_index=True)

    with st.expander("Raw view", expanded=False):
        st.json(preview["raw"])


elif menu == "Paper Bets":
    st.header("Paper Bets")

    source_label = st.selectbox(
        "Paper/review source",
        ["Paper Ledger Latest", "Review Queue Latest", "Review Queue Full"],
    )
    source_path = DATA_LIBRARY_PATHS[source_label]
    preview = preview_path(source_path, limit=1000)

    rows = list(preview["rows"] or [])
    table = df(rows)

    if table.empty:
        st.warning("No rows found.")
    else:
        sport_filter = st.selectbox("Sport filter", ["All"] + sorted(str(x) for x in table.get("sport", pd.Series(dtype=str)).dropna().unique()))
        market_filter = st.selectbox("Bet type filter", ["All"] + sorted(str(x) for x in table.get("market", pd.Series(dtype=str)).dropna().unique()))

        filtered = table.copy()
        if sport_filter != "All" and "sport" in filtered.columns:
            filtered = filtered[filtered["sport"].astype(str) == sport_filter]
        if market_filter != "All" and "market" in filtered.columns:
            filtered = filtered[filtered["market"].astype(str) == market_filter]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            if "sport" in filtered.columns:
                st.subheader("Paper bets by sport")
                st.bar_chart(filtered["sport"].fillna("UNKNOWN").astype(str).value_counts())
        with c2:
            if "market" in filtered.columns:
                st.subheader("Paper bets by bet type")
                st.bar_chart(filtered["market"].fillna("UNKNOWN").astype(str).value_counts())

    with st.expander("Raw source JSON", expanded=False):
        st.json(preview["raw"])


elif menu == "Backtest Dashboard":
    st.header("Backtest Dashboard")

    snapshot = load_dashboard_snapshot()

    if not snapshot.get("dashboard_exists"):
        st.warning("Latest dashboard JSON is missing. Generate it here.")
        if st.button("Generate dashboard files", type="primary"):
            with st.spinner("Generating dashboard..."):
                result = generate_latest_dashboard_outputs(
                    tactic=settings["tactic"],
                    profile_key="all_sports",
                    starting_bankroll=settings["starting_bankroll"],
                    unit_size=settings["unit_size"],
                    max_rows=settings["max_rows"],
                    intercept=settings["intercept"],
                    feature_weights=settings["feature_weights"],
                    probability_floor=settings["probability_floor"],
                    probability_ceiling=settings["probability_ceiling"],
                    override_existing_probability=settings["override_existing_probability"],
                    force_rebuild_dataset=settings["force_rebuild_dataset"],
                    require_core_fields=settings["require_core_fields"],
                )
            st.success("Dashboard generated.")
            st.json(result)
    else:
        dashboard = snapshot["dashboard"]
        show_run_result(dashboard)

    st.subheader("Canonical Schema Preview")
    schema_preview = preview_path(DATA_LIBRARY_PATHS["Canonical Schema Report"], limit=200)
    st.dataframe(df(schema_preview["rows"]), use_container_width=True, hide_index=True)

    with st.expander("Raw schema report", expanded=False):
        st.json(schema_preview["raw"])


elif menu == "Test One Sport":
    st.header("Test One Sport")

    options = get_available_profile_options()
    sport_options = [item for item in options if item["value"] != "all_sports"]

    selected_label = st.selectbox("Sport/profile", [item["label"] for item in sport_options])
    selected = next(item for item in sport_options if item["label"] == selected_label)

    st.info("Pick one sport/model profile. This runs a paper backtest, not a real bet.")

    if st.button("Run one-sport test", type="primary"):
        with st.spinner(f"Testing {selected['value']}..."):
            result = run_model_test(
                profile_key=selected["value"],
                tactic=settings["tactic"],
                starting_bankroll=settings["starting_bankroll"],
                unit_size=settings["unit_size"],
                max_rows=settings["max_rows"],
                intercept=settings["intercept"],
                feature_weights=settings["feature_weights"],
                probability_floor=settings["probability_floor"],
                probability_ceiling=settings["probability_ceiling"],
                override_existing_probability=settings["override_existing_probability"],
                force_rebuild_dataset=settings["force_rebuild_dataset"],
                require_core_fields=settings["require_core_fields"],
                model_id=f"streamlit-{selected['value']}",
            )
        st.success("One-sport test complete.")
        show_run_result(result)


elif menu == "Test All Sports":
    st.header("Test All Sports")

    mode = st.selectbox("All-sports mode", ["all_sports", "all_sports + sport_specific profiles"])

    profile_key = "all_sports"
    tactic = settings["tactic"]
    if mode == "all_sports":
        tactic = "All-sports regression"

    if st.button("Run all-sports test", type="primary"):
        with st.spinner("Testing all sports..."):
            result = run_model_test(
                profile_key=profile_key,
                tactic=tactic,
                starting_bankroll=settings["starting_bankroll"],
                unit_size=settings["unit_size"],
                max_rows=settings["max_rows"],
                intercept=settings["intercept"],
                feature_weights=settings["feature_weights"],
                probability_floor=settings["probability_floor"],
                probability_ceiling=settings["probability_ceiling"],
                override_existing_probability=settings["override_existing_probability"],
                force_rebuild_dataset=settings["force_rebuild_dataset"],
                require_core_fields=settings["require_core_fields"],
                model_id="streamlit-all-sports",
            )
        st.success("All-sports test complete.")
        show_run_result(result)


elif menu == "Bankroll Settings":
    st.header("Bankroll Settings")

    st.write("These settings are for paper testing. They do not place real bets.")

    preset_rows = []
    for name, preset in RISK_PRESETS.items():
        preset_rows.append(
            {
                "preset": name,
                "normal bet %": preset.get("unit_size_percent"),
                "max bet %": preset.get("max_stake_percent"),
                "stop if down %": preset.get("max_drawdown_stop_percent"),
                "simple explanation": preset.get("explanation"),
            }
        )

    st.dataframe(df(preset_rows), use_container_width=True, hide_index=True)

    st.subheader("Current Settings")
    st.json(
        {
            "risk_preset": settings["risk_preset"],
            "starting_bankroll": settings["starting_bankroll"],
            "unit_size": settings["unit_size"],
            "max_rows": settings["max_rows"],
        }
    )


elif menu == "Regression Tactics":
    st.header("Regression Tactics")

    tactic_rows = []
    for name, item in REGRESSION_TACTICS.items():
        tactic_rows.append(
            {
                "tactic": name,
                "mode": item.get("mode"),
                "profile_scope": item.get("profile_scope", ""),
                "simple explanation": item.get("friendly"),
            }
        )

    st.dataframe(df(tactic_rows), use_container_width=True, hide_index=True)

    st.subheader("Current Regression Settings")
    st.json(
        {
            "tactic": settings["tactic"],
            "intercept": settings["intercept"],
            "probability_floor": settings["probability_floor"],
            "probability_ceiling": settings["probability_ceiling"],
            "override_existing_probability": settings["override_existing_probability"],
            "feature_weights": settings["feature_weights"],
        }
    )

    st.info("Intercept is the starting chance. Feature weights move the chance up or down. Floor and ceiling keep the chance from getting silly.")


elif menu == "System Health":
    st.header("System Health")

    rows = get_system_health_rows()
    st.dataframe(df(rows), use_container_width=True, hide_index=True)

    st.subheader("Available Sport/Profile Options")
    st.dataframe(df(get_available_profile_options()), use_container_width=True, hide_index=True)

    st.subheader("File Inventory")
    st.dataframe(df(file_inventory()), use_container_width=True, hide_index=True)


elif menu == "Data Source Library":
    st.header("Historical Data Source Registry")
    rows = get_historical_data_source_rows(include_rejected=True)
    if rows:
        st.dataframe(df(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No sources registered.")
    with st.expander("Status counts"):
        counts = get_source_status_counts()
        st.json(counts)


elif menu == "Import Historical Data":
    st.header("Import Historical Odds Data")
    st.warning(
        "Importing of historical data has not been implemented yet. "
        "Importers will be created in **Phase 10H5** (canonical historical odds importers). "
        "After that, SQLite store will be implemented in **Phase 10H6**."
    )
    st.info(
        "No downloads, scraping, or SQLite writes happen here. "
        "This screen will activate once importers are ready."
    )


elif menu == "Data Quality Check":
    st.header("Data Quality Check")
    st.subheader("File Inventory")
    inventory = file_inventory()
    if inventory:
        st.dataframe(df(inventory), use_container_width=True, hide_index=True)
    else:
        st.info("No inventory loaded.")

    st.subheader("Schema Preview")
    schema_preview = preview_path(DATA_LIBRARY_PATHS.get("Canonical Schema Report"), limit=200)
    if schema_preview and schema_preview.get("exists"):
        st.dataframe(df(schema_preview["rows"]), use_container_width=True, hide_index=True)
    else:
        st.info("Schema report not yet available.")


elif menu == "Model Projection":
    st.header("Model Projection")
    snapshot = load_dashboard_snapshot()
    cards = simple_home_cards(snapshot)
    metric_row([
        ("System", cards.get("Is the system safe?" , "Unknown")),
        ("Start money", cards.get("How much money did the test start with?","-")),
        ("End money", cards.get("How much money did the test end with?","-")),
        ("Ready?", cards.get("Is this ready or not ready?","-")),
    ])

    plan_text = get_model_testing_source_plan()
    st.markdown(plan_text)

    st.subheader("Priority Import Sources")
    priority = get_priority_import_sources()
    if priority:
        st.dataframe(df(priority), use_container_width=True, hide_index=True)
    else:
        st.info("No priority sources defined.")

    summary = summarize_source_registry()
    st.json(summary)
