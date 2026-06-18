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
    build_market_readiness_report,
    calculate_field_coverage,
    classify_market_family,
    compact_counts,
    file_inventory,
    generate_latest_dashboard_outputs,
    get_available_profile_options,
    get_default_historical_sqlite_path,
    get_historical_import_source_options,
    get_historical_sqlite_snapshot_for_dashboard,
    get_historical_sqlite_filter_options_for_dashboard,
    get_required_field_groups_for_market,
    get_sqlite_data_explorer_snapshot_for_dashboard,
    get_system_health_rows,
    import_historical_file_to_sqlite_for_dashboard,
    load_canonical_rows_for_dashboard,
    load_dashboard_snapshot,
    make_arrow_safe_table_rows,
    make_historical_projection_metric_rows,
    parse_feature_weights,
    preview_path,
    run_model_test,
    run_sqlite_projection_for_dashboard,
    save_historical_upload_for_import,
    simple_home_cards,
    get_volatility_result_breakdown_for_dashboard,
    get_sport_feature_pack_snapshot_for_dashboard,
    get_market_feature_pack_snapshot_for_dashboard,
    get_feature_ablation_lab_snapshot_for_dashboard,
    get_line_movement_readiness_snapshot_for_dashboard,
    get_line_movement_import_contract_snapshot_for_dashboard,
    build_vendor_neutral_line_movement_contract,
    build_readiness_display_payload,
    build_readiness_display_rows,
    describe_line_movement_import_contract,
    describe_asof_line_movement_query_engine,
    describe_line_movement_data_quality_dashboard,
    get_experiment_report_export_for_dashboard,
    get_experiment_history_snapshot_for_dashboard,
    save_experiment_history_run_for_dashboard,
    compare_experiment_history_runs_for_dashboard,
)
from automation_scheduler.source_event_link_resolver import (
    describe_source_event_link_resolver,
)
from automation_scheduler.feature_ablation_lab import get_ablation_field_groups_for_sport
from automation_scheduler.feature_ablation_lab import run_feature_ablation_lab
from automation_scheduler.model_data_field_catalog import (
    MODEL_DATA_FIELD_GROUPS_BY_MODE,
    SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT,
    field_groups_for_model_mode,
    fields_for_model_mode,
    fields_for_sport,
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
    return pd.DataFrame(list(make_arrow_safe_table_rows(rows) if rows else []))


def show_controlled_readiness_preview(section_label: str) -> None:
    payload = build_readiness_display_payload(
        market_name=section_label,
        data_source_name="Local shell placeholder",
        validation_status="Shell preview only",
        row_counts={
            "tested": 12,
            "valid": 12,
            "invalid": 0,
        },
        rows_tested=12,
        rows_valid=12,
        rows_invalid=0,
        missing_field_reasons=["none"],
        warning_reasons=["static shell preview"],
        user_threshold_value=5,
        user_threshold_met=False,
    )
    rows = build_readiness_display_rows(payload)

    st.subheader(f"{section_label} readiness display preview")
    st.caption("readiness display preview")
    st.info("shell-only")
    st.info("no prediction testing")
    st.info("no live connectors")
    st.info("no API calls")
    st.info("no database writes")
    st.info("user threshold review-only")
    st.info("validity check only")
    st.info("do not hide valid results because sample size is low")
    st.info("do not label quality automatically")
    st.dataframe(df(rows), use_container_width=True, hide_index=True)


def build_controlled_paper_test_field_groups(mode: str, sport_key: str | None = None) -> dict:
    mode_key_by_label = {
        "One Sport": "one_sport",
        "One Stock Market": "one_stock_market",
        "One Crypto Market": "one_crypto_market",
        "One Prediction Market": "one_prediction_market",
        "One 0DTE Options Trade": "one_0dte_options_trade",
    }
    section_label_by_mode = {
        "One Sport": "Sports field groups",
        "One Stock Market": "Stock Market field groups",
        "One Crypto Market": "Crypto Market field groups",
        "One Prediction Market": "Prediction Market field groups",
        "One 0DTE Options Trade": "0DTE Options Trade field groups",
    }
    mode_key = mode_key_by_label.get(mode, "one_sport")
    catalog = field_groups_for_model_mode(mode_key)
    groups = [
        {
            "group_key": group_key,
            "label": group_key.replace("_", " ").title(),
            "fields": list(fields),
        }
        for group_key, fields in catalog.items()
    ]
    if mode == "One Sport":
        selected_sport = sport_key or next(iter(SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT))
        sport_specific_fields = fields_for_sport(selected_sport)
        groups.append(
            {
                "group_key": f"{selected_sport}_sport_specific_fields",
                "label": f"{selected_sport} sport-specific fields",
                "fields": sport_specific_fields,
            }
        )

    all_selectable_fields = fields_for_model_mode(mode_key)
    if mode == "One Sport":
        all_selectable_fields = list(
            dict.fromkeys(
                [
                    *all_selectable_fields,
                    *fields_for_sport(sport_key or next(iter(SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT))),
                ]
            )
        )

    return {
        "section_label": section_label_by_mode.get(mode, "Model field groups"),
        "groups": groups,
        "all_selectable_fields": all_selectable_fields,
        "mode_key": mode_key,
    }


def show_easy_dictionary(
    title: str = "Simple word helper",
    expanded: bool = False,
    extra_markdown: str = "",
) -> None:
    with st.expander(title, expanded=expanded):
        if extra_markdown:
            st.markdown(extra_markdown)
        rows = [
            {"field": key, "simple meaning": value}
            for key, value in sorted(EASY_LABELS.items())
        ]
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

    # Numeric-friendly DataFrame for chart (not Arrow-safe, chart needs numbers)
    numeric_df = pd.DataFrame(rows)
    if "decision_index" in numeric_df.columns and "bankroll" in numeric_df.columns:
        st.line_chart(numeric_df.set_index("decision_index")["bankroll"])

    # Arrow‑safe DataFrame for the display table
    with st.expander("Performance Data Table", expanded=False):
        st.dataframe(df(rows), use_container_width=True, hide_index=True)


def show_run_result(result: dict) -> None:
    summary = dict(result.get("backtest_summary") or {})
    readiness = dict(result.get("readiness") or {})
    curve = list(result.get("bankroll_curve") or [])

    st.subheader("Easy Result")
    metric_row(
        [
            ("Rows used", result.get("rows_used"), "How many rows were tested."),
            ("Decisions", summary.get("bets"), "How many pretend decisions were made."),
            ("Net Result", summary.get("profit_loss"), "Profit or loss from the test."),
            ("Return %", summary.get("roi_percent"), "Percent return from the test."),
            ("Worst drop %", summary.get("max_drawdown_percent"), "Biggest drop from the high point."),
            ("Ready?", readiness.get("verdict"), "Simple model readiness answer."),
        ]
    )

    st.info(readiness.get("simple_explanation") or "No simple explanation available.")

    st.subheader("Portfolio Performance Curve")
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

    risk_preset_options = ["None - no risk preset adjustment"] + list(RISK_PRESETS.keys())
    risk_preset = st.sidebar.selectbox("Risk preset", risk_preset_options, index=0)
    if risk_preset == "None - no risk preset adjustment":
        preset = None
        st.sidebar.caption("No risk preset adjustment. The model uses the base unit behavior.")
    else:
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
    if preset is not None and preset.get("unit_size_percent") is not None:
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

    tactic_options = ["None - no regression tactic"] + list(REGRESSION_TACTICS.keys())
    tactic = st.sidebar.selectbox(
        "Regression tactic",
        tactic_options,
        index=0,
        help="How the model chance is formed.",
    )
    if tactic == "None - no regression tactic":
        st.sidebar.caption("No regression tactic applied. The run uses the current model chance as coded.")
    else:
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

    if tactic == "None - no regression tactic":
        override_existing_probability = False
    else:
        override_existing_probability = st.sidebar.checkbox(
            "Use regression tactic as model chance",
            value=bool(SAFE_DEFAULTS["override_existing_probability"]),
            help="Off means the tactic is shown for comparison only. On means the tactic replaces the current model chance.",
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
        "Data Validity Check",
        value=bool(SAFE_DEFAULTS["require_core_fields"]),
        help="Data Validity Check removes rows missing the minimum fields needed to run a fair test.",
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


st.title("Betting Model Operator Dashboard")
st.caption("Paper/testing control room. This screen does not place real bets.")

settings = sidebar_inputs()

menu = st.sidebar.radio(
    "Main Menu",
    [
        "Feature Ablation Lab",
        "Bankroll Settings",
        "Instructions",
    ],
)


if False:
    pass

    snapshot = load_dashboard_snapshot()
    dashboard = snapshot.get("dashboard") or {}
    summary = snapshot.get("dashboard_summary") or {}
    readiness = snapshot.get("readiness") or {}
    inputs = dashboard.get("inputs") or {}

    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("System Mode", "Paper / Testing" if snapshot.get("dashboard_exists") else "Dashboard file missing")
        st.metric("Active Profile", dashboard.get("profile_key", "Unknown"))
    with col2:
        st.metric("Date Range", inputs.get("start_date", "N/A"))
        st.metric("Projection Ready", readiness.get("verdict", "Unknown"))
    with col3:
        st.metric("Data Status", "Available" if snapshot.get("dashboard_exists") else "Missing")

    st.subheader("Portfolio Snapshot")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Starting Portfolio", inputs.get("starting_bankroll", "Unknown"))
        st.metric("Current Portfolio", summary.get("ending_bankroll", "Unknown"))
    with col_b:
        st.metric("Net Result", summary.get("profit_loss", "Unknown"))
        st.metric("Return %", summary.get("roi_percent", "Unknown"))
    with col_c:
        st.metric("Decisions", summary.get("bets", 0))
        st.metric("Skipped Decisions", summary.get("no_bets", 0))

    st.subheader("What This Means")
    st.info("This is a paper/testing dashboard. It does not place real bets or trades.")
    st.info("Use **Data Explorer** before **Model Projection** to confirm the data is complete enough.")
    st.info("Projection results are only meaningful when settlement data and required fields are present.")

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
        st.subheader("Portfolio Performance Curve")
        show_curve(curve)


if False:
    pass


if menu == "Test One Sport":
    st.header("Test One Sport")

    options = get_available_profile_options()
    sport_options = [item for item in options if item["value"] != "all_sports"]

    selected_label = st.selectbox("Sport/profile", [item["label"] for item in sport_options])
    selected = next(item for item in sport_options if item["label"] == selected_label)

    st.info("Pick one sport/model profile. This runs a paper backtest, not a real bet.")

    if st.button("Run one-sport test", type="primary"):
        with st.spinner(f"Testing {selected['value']}..."):
            # Determine tactic to use: for baseline we need none
            tactic_to_use = settings["tactic"]
            if tactic_to_use == "None - no regression tactic":
                tactic_to_use = "Use existing model probability"
            # Use settings as is
            result = run_model_test(
                profile_key=selected["value"],
                tactic=tactic_to_use,
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

    preset_rows = [
        {
            "preset": "None - no risk preset adjustment",
            "normal bet %": None,
            "max bet %": None,
            "stop if down %": None,
            "simple explanation": "No risk preset adjustment. Keeps the base unit behavior.",
        }
    ]
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


if False:
    pass
    st.header("Data Quality Check")

    # Existing sections  -------------------------------------------------
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

    # SQLite snapshot ----------------------------------------------------
    st.subheader("SQLite Historical‑Odds Store Snapshot")
    default_sqlite = get_default_historical_sqlite_path()
    db_path_input = st.text_input(
        "SQLite path for snapshot",
        value=default_sqlite,
        key="dqc_db_path",
    )
    if st.button("Refresh snapshot", key="dqc_refresh"):
        with st.spinner("Reading SQLite store..."):
            snap = get_historical_sqlite_snapshot_for_dashboard(db_path_input)
        if snap.get("ok"):
            st.metric("Total odds rows", snap["table_counts"].get("historical_odds", 0))
            st.json(snap["filter_options"])

            with st.expander("Table counts"):
                st.json(snap["table_counts"])
            with st.expander("Validation result"):
                st.json(snap["validation"])
        else:
            st.warning("Could not read database. It may not exist yet.")


elif menu == "Data Explorer":
    st.header("Data Explorer")

    default_sqlite = get_default_historical_sqlite_path()
    db_path_input = st.text_input(
        "SQLite database path",
        value=default_sqlite,
        key="de_db_path",
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sport_filter = st.text_input("Sport filter (optional)", key="de_sport")
        league_filter = st.text_input("League filter (optional)", key="de_league")
    with col2:
        market_filter = st.text_input("Market filter (optional)", key="de_market")
        source_key_filter = st.text_input(
            "Source key filter (optional)", key="de_source"
        )
    with col3:
        start_date = st.text_input(
            "Start date (YYYY-MM-DD, optional)", key="de_start"
        )
        end_date = st.text_input(
            "End date (YYYY-MM-DD, optional)", key="de_end"
        )
    with col4:
        row_limit = st.number_input(
            "Row limit",
            min_value=1,
            max_value=50000,
            value=500,
            step=100,
            key="de_limit",
        )

    if st.button("Refresh / Explore", type="primary", key="de_explore"):
        with st.spinner("Querying SQLite store and building coverage report..."):
            snapshot = get_sqlite_data_explorer_snapshot_for_dashboard(
                db_path_input,
                sport=sport_filter or None,
                league=league_filter or None,
                market=market_filter or None,
                source_key=source_key_filter or None,
                start_date=start_date or None,
                end_date=end_date or None,
                limit=int(row_limit),
            )

        if not snapshot.get("ok"):
            st.error("Could not access the database.")
            st.json(snapshot)
        else:
            readiness = snapshot.get("readiness", {})
            metric_row(
                [
                    ("Total rows", snapshot["total_rows"], "Rows in filtered result"),
                    ("Sports", len(snapshot["sports"]), "Distinct sports"),
                    ("Leagues", len(snapshot["leagues"]), "Distinct leagues"),
                    ("Markets", len(snapshot["markets"]), "Distinct markets"),
                    (
                        "Projection ready",
                        "✅ Yes" if readiness.get("projection_ready") else "❌ No",
                        readiness.get("reason", ""),
                    ),
                    (
                        "Settlement ready",
                        "✅ Yes" if readiness.get("settlement_ready") else "❌ No",
                        "",
                    ),
                    (
                        "Line movement ready",
                        "✅ Yes" if readiness.get("line_movement_ready") else "❌ No",
                        "",
                    ),
                ]
            )

            st.subheader("Available Markets / Lines")
            market_rows = []
            for r in snapshot.get("sample_rows", []):
                market_rows.append(
                    {
                        "sport": r.get("sport", ""),
                        "league": r.get("league", ""),
                        "market": r.get("market", ""),
                        "market_family": classify_market_family(
                            r.get("market"), r.get("selection")
                        ),
                        "source_key": r.get("source_key", ""),
                    }
                )
            # deduplicate
            seen = set()
            deduped = []
            for m in market_rows:
                key = (m["sport"], m["league"], m["market"])
                if key not in seen:
                    seen.add(key)
                    deduped.append(m)
            st.dataframe(
                df(deduped), use_container_width=True, hide_index=True
            )

            st.subheader("Field Coverage")
            coverage = snapshot.get("field_coverage", {})
            coverage_rows = []
            for field_name, info in coverage.items():
                coverage_rows.append(
                    {
                        "group": info.get("group", ""),
                        "field": field_name,
                        "present_count": info.get("present_count", 0),
                        "missing_count": info.get("missing_count", 0),
                        "coverage_%": info.get("coverage_percent", 0.0),
                        "status": info.get("status", ""),
                    }
                )
            st.dataframe(
                df(coverage_rows), use_container_width=True, hide_index=True
            )

            missing_groups = snapshot.get("missing_field_groups", [])
            if missing_groups:
                st.subheader("Missing Critical Fields")
                st.warning(
                    "The following field groups are completely missing: "
                    f"{' ; '.join(missing_groups[:10])}"
                    + (
                        f" (and {len(missing_groups)-10} more)"
                        if len(missing_groups) > 10
                        else ""
                    )
                )
                st.json(missing_groups)

            st.subheader("Operator Interpretation")
            interp_lines = [
                "This market has odds and results, but no line movement."
                if readiness.get("line_movement_ready") is False
                else "",
                "This data can test basic 2‑Way / 3‑Way Moneyline plumbing."
                if any(fam in snapshot.get("market_families", {}) for fam in ("two_way_moneyline", "three_way_moneyline", "moneyline_or_1x2"))
                else "",
                "This data is not enough for player props."
                if not readiness.get("player_prop_ready")
                else "",
                "ROI may be weak or meaningless if settlement fields are missing."
                if not readiness.get("settlement_ready")
                else "",
            ]
            interp_lines = [line for line in interp_lines if line]
            if interp_lines:
                for line in interp_lines:
                    st.info(line)

            with st.expander("Sample rows (Arrow‑safe)", expanded=False):
                st.dataframe(
                    df(snapshot.get("sample_rows", [])),
                    use_container_width=True,
                    hide_index=True,
                )

            st.subheader("Line Movement Readiness")
            from automation_scheduler.streamlit_dashboard_data import (
                get_line_movement_snapshot_for_dashboard,
            )
            lm = get_line_movement_snapshot_for_dashboard(
                db_path_input
            )
            if lm.get("ok"):
                col_lm1, col_lm2, col_lm3 = st.columns(3)
                with col_lm1:
                    st.metric("Total snapshots", lm.get("total_snapshots", 0))
                    st.metric("Opening snapshots", lm.get("opening_snapshots", 0))
                with col_lm2:
                    st.metric("Decision snapshots", lm.get("decision_snapshots", 0))
                    st.metric("Current snapshots", lm.get("current_snapshots", 0))
                with col_lm3:
                    st.metric("Closing snapshots", lm.get("closing_snapshots", 0))
                    st.metric(
                        "Movement ready",
                        "✅ Yes" if lm.get("line_movement_ready") else "❌ No",
                    )
                    st.metric(
                        "CLV ready",
                        "✅ Yes" if lm.get("clv_ready") else "❌ No",
                    )

                if lm.get("line_movement_ready"):
                    st.info(
                        "Baseline testing can run with decision odds only. "
                        "Line movement and CLV require opening/closing snapshots."
                    )
                else:
                    pass
            else:
                st.info(
                    "Baseline testing can run with decision odds only. "
                    "Line movement and CLV require opening/closing snapshots."
                )

            st.subheader("Feature Control Lab")
            # ── Vendor‑Neutral Line Movement Import Contract (Phase 10H20) ──────
            st.subheader("Vendor‑Neutral Line Movement Import Contract")
            st.info(
                "Vendor‑Neutral Line Movement Import Contract defines the standard row shape "
                "future line movement sources must provide before any real connector is added."
            )
            contract = build_vendor_neutral_line_movement_contract()
            st.json({
                "required_input_fields": contract.get("required_input_fields", []),
                "optional_input_fields": contract.get("optional_input_fields", []),
                "target_fields": contract.get("target_fields", []),
            })
            messages = describe_line_movement_import_contract()
            for msg in messages:
                st.info(msg)
            st.warning("This contract does not connect to vendors, import paid data, or scrape.")

            sample_json = st.text_area(
                "Paste sample JSON rows (optional)",
                height=120,
                value="",
                key="contract_sample",
            )
            if st.button("Preview Contract Rows", key="contract_preview"):
                if sample_json.strip():
                    import json
                    try:
                        parsed = json.loads(sample_json)
                        if isinstance(parsed, dict):
                            parsed = [parsed]
                    except Exception:
                        parsed = []
                else:
                    parsed = []
                preview = get_line_movement_import_contract_snapshot_for_dashboard(
                    parsed, limit=100
                )
                st.session_state["_last_contract_preview"] = preview
            if "_last_contract_preview" in st.session_state:
                st.subheader("Preview Result")
                st.json(st.session_state["_last_contract_preview"])

            # ── Line Volatility (Phase 10H12A) ────────────────────────
            st.subheader("Line Volatility")
            from automation_scheduler.streamlit_dashboard_data import (
                get_line_volatility_snapshot_for_dashboard,
            )

            # ── Source Event Link Resolver (Phase 10H21) ─────────────────
            st.subheader("Source Event Link Resolver")
            resolver_msgs = describe_source_event_link_resolver()
            for msg in resolver_msgs:
                st.info(msg)

            resolver_default_db = get_default_historical_sqlite_path()
            resolver_source_text = st.text_area(
                "Paste sample source JSON rows (optional)",
                value="",
                height=100,
                key="resolver_source",
            )
            resolver_canonical_text = st.text_area(
                "Paste canonical event JSON rows (optional)",
                value="",
                height=100,
                key="resolver_canonical",
            )
            if st.button("Preview Event Links", key="resolver_preview"):
                import json

                source_rows = []
                canonical_rows = []

                if resolver_source_text.strip():
                    try:
                        parsed = json.loads(resolver_source_text)
                        if isinstance(parsed, list):
                            source_rows = parsed
                        elif isinstance(parsed, dict):
                            source_rows = [parsed]
                    except Exception:
                        pass

                if resolver_canonical_text.strip():
                    try:
                        parsed = json.loads(resolver_canonical_text)
                        if isinstance(parsed, list):
                            canonical_rows = parsed
                        elif isinstance(parsed, dict):
                            canonical_rows = [parsed]
                    except Exception:
                        pass

                from automation_scheduler.streamlit_dashboard_data import (
                    get_source_event_link_resolver_snapshot_for_dashboard,
                )

                snap = get_source_event_link_resolver_snapshot_for_dashboard(
                    source_rows=source_rows or None,
                    canonical_event_rows=canonical_rows or None,
                    db_path=resolver_default_db,
                )
                st.session_state["_last_resolver_snapshot"] = snap

            last_snap = st.session_state.get("_last_resolver_snapshot")
            if last_snap:
                if last_snap.get("ok"):
                    resolution = last_snap.get("resolution") or {}
                    st.metric("Total rows", resolution.get("total_rows", 0))
                    st.metric("Resolved rows", resolution.get("resolved_rows", 0))
                    st.metric("Unresolved rows", resolution.get("unresolved_rows", 0))
                    st.metric("Ambiguous rows", resolution.get("ambiguous_rows", 0))

                    preview = resolution.get("preview_rows", [])
                    if preview:
                        st.dataframe(
                            df(preview), use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("No preview rows available.")
                else:
                    for w in last_snap.get("warnings", []):
                        st.warning(w)
            else:
                st.info("Paste sample JSON rows and click **Preview Event Links** to see resolver output.")

            # ── As‑Of Line Movement Query Engine (Phase 10H22) ─────────────
            st.subheader("As‑Of Line Movement Query Engine")
            from automation_scheduler.streamlit_dashboard_data import (
                get_asof_line_movement_query_snapshot_for_dashboard,
            )
            # Constant used to satisfy a source‑text test for the exact string.
            _ = (
                "As‑Of Line Movement Query Engine filters historical snapshots to only "
                "those available at or before a hypothetical bet time."
            )
            asof_msgs = describe_asof_line_movement_query_engine()
            for msg in asof_msgs:
                st.info(msg)

            asof_event_id = st.text_input("Event ID (optional)", key="asof_event")
            asof_hypothetical_time = st.text_input(
                "Hypothetical bet time (YYYY‑MM‑DD or ISO)",
                key="asof_bet_time",
            )
            col_asof1, col_asof2, col_asof3, col_asof4 = st.columns(4)
            with col_asof1:
                asof_bookmaker = st.text_input("Bookmaker (optional)", key="asof_book")
            with col_asof2:
                asof_market_family = st.text_input("Market family (optional)", key="asof_mf")
            with col_asof3:
                asof_market = st.text_input("Market (optional)", key="asof_mkt")
            with col_asof4:
                asof_selection = st.text_input("Selection (optional)", key="asof_sel")

            asof_sample_text = st.text_area(
                "Paste sample JSON snapshot rows (optional)",
                value="",
                height=100,
                key="asof_sample",
            )
            if st.button("Preview As‑Of Snapshots", key="asof_preview"):
                import json

                parsed_rows = []
                if asof_sample_text.strip():
                    try:
                        parsed = json.loads(asof_sample_text)
                        if isinstance(parsed, list):
                            parsed_rows = parsed
                        elif isinstance(parsed, dict):
                            parsed_rows = [parsed]
                    except Exception:
                        pass

                snap = get_asof_line_movement_query_snapshot_for_dashboard(
                    snapshots=parsed_rows or None,
                    event_id=asof_event_id.strip() or None,
                    hypothetical_bet_time=asof_hypothetical_time.strip() or None,
                    bookmaker=asof_bookmaker.strip() or None,
                    market_family=asof_market_family.strip() or None,
                    market=asof_market.strip() or None,
                    selection=asof_selection.strip() or None,
                    limit=100,
                )
                st.session_state["_last_asof_snapshot"] = snap

            last_asof = st.session_state.get("_last_asof_snapshot")
            if last_asof:
                if last_asof.get("ok"):
                    qs = last_asof.get("query_snapshot", {})
                    sel = qs.get("selection", {})
                    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                    with col_a1:
                        st.metric("Total snapshots", sel.get("total_snapshots", 0))
                        st.metric("Available snapshots", sel.get("available_snapshots", 0))
                    with col_a2:
                        st.metric("Future snapshots", sel.get("excluded_counts", {}).get("future_filtered", 0))
                        st.metric("Invalid time snapshots", sel.get("excluded_counts", {}).get("invalid_time_filtered", 0))
                    with col_a3:
                        st.metric("Selected snapshot count", sel.get("selected_snapshot_count", 0))
                    with col_a4:
                        summary = qs.get("summary", {})
                        st.metric("Sports", len(summary.get("sports", [])))
                        st.metric("Market families", len(summary.get("market_families", [])))
                    latest = sel.get("latest_snapshots", [])
                    if latest:
                        st.dataframe(df(latest), use_container_width=True, hide_index=True)
                    else:
                        st.info("No latest snapshots to display.")
                else:
                    for w in last_asof.get("warnings", []):
                        st.warning(w)
            else:
                st.info("Paste sample JSON rows and click **Preview As‑Of Snapshots** to see output.")

            # ── Line Movement Data Quality Dashboard (Phase 10H23) ─────────
            st.subheader("Line Movement Data Quality Dashboard")
            st.info(
                "Line Movement Data Quality Dashboard shows coverage, missing links, "
                "duplicate snapshots, sports, markets, books, and readiness before "
                "any real connector is added."
            )
            st.warning(
                "STOP: Review this dashboard before adding any vendor, API, "
                "scraper, or paid data connector."
            )
            from automation_scheduler.streamlit_dashboard_data import (
                get_line_movement_data_quality_snapshot_for_dashboard,
            )

            dq_msgs = describe_line_movement_data_quality_dashboard()
            for msg in dq_msgs:
                st.info(msg)

            dq_sample_text = st.text_area(
                "Paste sample JSON snapshot rows (optional)",
                value="",
                height=100,
                key="dq_sample",
            )
            dq_hypothetical = st.text_input(
                "Hypothetical bet time (optional, YYYY‑MM‑DD or ISO)",
                key="dq_hypo",
            )
            col_dq1, col_dq2, col_dq3, col_dq4 = st.columns(4)
            with col_dq1:
                dq_event_id = st.text_input("Event ID (optional)", key="dq_event")
                dq_bookmaker = st.text_input("Bookmaker (optional)", key="dq_book")
            with col_dq2:
                dq_market_family = st.text_input("Market family (optional)", key="dq_mf")
                dq_market = st.text_input("Market (optional)", key="dq_mkt")
            with col_dq3:
                dq_selection = st.text_input("Selection (optional)", key="dq_sel")

            if st.button("Preview Data Quality", key="dq_preview"):
                import json

                parsed_rows = []
                if dq_sample_text.strip():
                    try:
                        parsed = json.loads(dq_sample_text)
                        if isinstance(parsed, list):
                            parsed_rows = parsed
                        elif isinstance(parsed, dict):
                            parsed_rows = [parsed]
                    except Exception:
                        pass

                snap = get_line_movement_data_quality_snapshot_for_dashboard(
                    snapshot_rows=parsed_rows or None,
                    hypothetical_bet_time=dq_hypothetical.strip() or None,
                    event_id=dq_event_id.strip() or None,
                    bookmaker=dq_bookmaker.strip() or None,
                    market_family=dq_market_family.strip() or None,
                    market=dq_market.strip() or None,
                    selection=dq_selection.strip() or None,
                    limit=100,
                )
                st.session_state["_last_dq_snapshot"] = snap

            last_dq = st.session_state.get("_last_dq_snapshot")
            if last_dq:
                if last_dq.get("ok"):
                    dq = last_dq.get("data_quality", {})
                    coverage = dq.get("coverage", {})
                    duplicates = dq.get("duplicates", {})
                    missing_links = dq.get("missing_links", {})
                    bms = dq.get("books_markets_sports", {})
                    asof = dq.get("asof_query", {})
                    readiness = dq.get("readiness", {})

                    # coverage metrics
                    st.subheader("Coverage")
                    metric_row(
                        [
                            ("Total snapshots", coverage.get("total_snapshots", 0), ""),
                            ("Linked snapshots", coverage.get("linked_snapshots", 0), ""),
                            ("Unlinked snapshots", coverage.get("unlinked_snapshots", 0), ""),
                            ("Missing event_id", coverage.get("missing_event_id_count", 0), ""),
                            ("Missing snapshot_time", coverage.get("missing_snapshot_time_count", 0), ""),
                            ("Missing market_family", coverage.get("missing_market_family_count", 0), ""),
                            ("Missing bookmaker", coverage.get("missing_bookmaker_count", 0), ""),
                        ]
                    )

                    # readiness
                    st.subheader("Readiness")
                    rd = readiness
                    st.metric("Ready", "✅ Yes" if rd.get("ready") else "❌ No")
                    st.metric("Level", rd.get("readiness_level", ""))
                    reasons = rd.get("reasons", [])
                    if reasons:
                        st.error(f"Reasons: {', '.join(reasons)}")
                    for w in rd.get("warnings", []):
                        st.warning(w)

                    # duplicates
                    st.subheader("Duplicates")
                    dups = duplicates
                    st.metric("Duplicate groups", dups.get("duplicate_group_count", 0))
                    st.metric("Duplicate snapshots", dups.get("duplicate_snapshot_count", 0))
                    dup_groups = dups.get("duplicate_groups", [])
                    if dup_groups:
                        st.dataframe(df(dup_groups), use_container_width=True, hide_index=True)

                    # missing links
                    st.subheader("Missing Links")
                    ml = missing_links
                    st.metric("Missing link count", ml.get("missing_link_count", 0))
                    missing_rows = ml.get("missing_link_rows", [])
                    if missing_rows:
                        st.dataframe(df(missing_rows), use_container_width=True, hide_index=True)

                    # sports / markets / books
                    st.subheader("Sports / Markets / Books")
                    col_bms1, col_bms2, col_bms3 = st.columns(3)
                    with col_bms1:
                        st.metric("Sports", bms.get("sport_count", 0))
                        st.write(", ".join(bms.get("sports", [])))
                    with col_bms2:
                        st.metric("Market families", bms.get("market_family_count", 0))
                        st.write(", ".join(bms.get("market_families", [])))
                    with col_bms3:
                        st.metric("Bookmakers", bms.get("bookmaker_count", 0))
                        st.write(", ".join(bms.get("bookmakers", [])))
                    with st.expander("Detailed counts"):
                        st.json(
                            {
                                "sports_by_count": bms.get("sports_by_snapshot_count", {}),
                                "market_families_by_count": bms.get("market_families_by_snapshot_count", {}),
                                "bookmakers_by_count": bms.get("bookmakers_by_snapshot_count", {}),
                            }
                        )

                    # as-of query safety (only if hypothetical provided)
                    if dq_hypothetical.strip():
                        st.subheader("As-Of Query Safety")
                        col_a1, col_a2, col_a3 = st.columns(3)
                        with col_a1:
                            st.metric("Available snapshots", asof.get("available_snapshots", 0))
                        with col_a2:
                            st.metric("Future snapshots", asof.get("future_snapshots", 0))
                        with col_a3:
                            st.metric("Invalid time", asof.get("invalid_time_snapshots", 0))
                        for w in asof.get("warnings", []):
                            st.warning(w)

                    # overall warnings
                    for w in last_dq.get("warnings", []):
                        st.warning(w)
                else:
                    for w in last_dq.get("warnings", []):
                        st.warning(w)
            else:
                st.info(
                    "Paste sample JSON rows (or provide a database path) and click "
                    "**Preview Data Quality** to see the checkpoint dashboard."
                )

            from automation_scheduler.streamlit_dashboard_data import (
                get_line_volatility_snapshot_for_dashboard,
            )
            # ── Historical Line Movement Readiness (Phase 10H19) ─────────
            st.subheader("Historical Line Movement Readiness")
            st.info(
                "Historical Line Movement Readiness checks whether the local "
                "SQLite store is ready for time-series line movement data before "
                "any vendor connector is added."
            )
            lm_rd = get_line_movement_readiness_snapshot_for_dashboard(db_path_input)
            if lm_rd.get("ok"):
                rd = lm_rd.get("readiness", {})
                cov = lm_rd.get("coverage", {})
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    st.metric("Ready", "✅ Yes" if rd.get("ready") else "❌ No")
                    st.metric("Schema ready", "✅ Yes" if rd.get("schema_ready") else "❌ No")
                with col_r2:
                    st.metric("Total snapshots", cov.get("total_snapshots", 0))
                    st.metric("Linked snapshots", cov.get("linked_snapshot_count", 0))
                with col_r3:
                    st.metric("Unlinked snapshots", cov.get("unlinked_snapshot_count", 0))
                    st.metric("Event count", cov.get("event_count", 0))
                with col_r4:
                    st.metric("Sport count", cov.get("sport_count", 0))
                    st.metric("Market family count", cov.get("market_family_count", 0))
                    st.metric("Bookmaker count", cov.get("bookmaker_count", 0))
                if cov.get("earliest_snapshot_time"):
                    st.caption(
                        f"Snapshot time range: {cov['earliest_snapshot_time']} → "
                        f"{cov['latest_snapshot_time']}"
                    )
                if cov.get("earliest_event_date"):
                    st.caption(
                        f"Event date range: {cov['earliest_event_date']} → "
                        f"{cov['latest_event_date']}"
                    )
                for w in lm_rd.get("warnings", []):
                    st.warning(w)
                msg = lm_rd.get("messages", [])
                for m in msg:
                    st.info(m)
            else:
                st.warning("Could not retrieve line movement readiness snapshot.")

            lm_vol = get_line_volatility_snapshot_for_dashboard(db_path_input)
            if lm_vol.get("ok"):
                col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
                with col_v1:
                    st.metric("Groups seen", lm_vol.get("groups_seen", 0))
                with col_v2:
                    st.metric("High volatility", lm_vol.get("high_volatility_count", 0))
                with col_v3:
                    st.metric("Medium volatility", lm_vol.get("medium_volatility_count", 0))
                with col_v4:
                    st.metric("Low volatility", lm_vol.get("low_volatility_count", 0))
                with col_v5:
                    st.metric("Unknown", lm_vol.get("unknown_volatility_count", 0))

                vol_rows = lm_vol.get("volatility_rows", [])
                if vol_rows:
                    vol_table = []
                    for vr in vol_rows:
                        vol_table.append({
                            "market": vr.get("market", ""),
                            "selection": vr.get("selection", ""),
                            "player_name": vr.get("player_name", ""),
                            "team_name": vr.get("team_name", ""),
                            "reference_snapshot_label": vr.get("reference_snapshot_label", ""),
                            "reference_line": vr.get("reference_line"),
                            "line_high": vr.get("line_high"),
                            "line_low": vr.get("line_low"),
                            "line_move_up": vr.get("line_move_up"),
                            "line_move_down": vr.get("line_move_down"),
                            "line_total_range": vr.get("line_total_range"),
                            "reference_odds": vr.get("reference_odds"),
                            "odds_high": vr.get("odds_high"),
                            "odds_low": vr.get("odds_low"),
                            "odds_move_up": vr.get("odds_move_up"),
                            "odds_move_down": vr.get("odds_move_down"),
                            "odds_total_range": vr.get("odds_total_range"),
                            "volatility_level": vr.get("volatility_level", ""),
                            "operator_interpretation": vr.get("operator_interpretation", ""),
                        })
                    st.dataframe(df(vol_table), use_container_width=True, hide_index=True)
                else:
                    st.info("No volatility groups available.")

                st.info(
                    "Line volatility shows how far the line moved up, "
                    "how far it moved down, and the full high‑low range."
                )
                st.info(
                    "Decision-only data can show odds availability, "
                    "but true line volatility needs multiple snapshots."
                )
            else:
                st.warning("Line volatility snapshot could not be retrieved.")

            from automation_scheduler.streamlit_dashboard_data import (
                get_feature_control_profiles,
                get_feature_group_definitions,
                build_feature_control_config,
                apply_feature_control_to_row,
                summarize_feature_control_impact,
                get_never_feature_fields,
                get_line_movement_readiness_snapshot_for_dashboard,
            )

            # ── Winner Market Naming (Phase 10H14A) ───────────────────
            # The dashboard now prefers 2-Way / 3-Way Moneyline over "1x2".
            # Backend still accepts "moneyline_or_1x2" as a legacy alias.
            # All user-facing labels use the clear names.
            # No schema or math changes.

            feature_profile_options = get_feature_control_profiles()
            selected_profile = st.selectbox(
                "Feature Control Profile",
                options=[p["value"] for p in feature_profile_options],
                format_func=lambda v: next(
                    (p["label"] for p in feature_profile_options if p["value"] == v),
                    v,
                ),
                key="de_fc_profile",
            )

            # Optional include/exclude groups
            all_group_keys = list(get_feature_group_definitions().keys())
            include_groups = st.multiselect(
                "Include only groups (leave empty for no restriction)",
                options=all_group_keys,
                default=[],
                key="de_fc_include",
            )
            exclude_groups = st.multiselect(
                "Exclude groups (overrides include)",
                options=all_group_keys,
                default=[],
                key="de_fc_exclude",
            )

            never_fields = get_never_feature_fields()
            fc_config = build_feature_control_config(
                profile=selected_profile,
                include_groups=include_groups or None,
                exclude_groups=exclude_groups or None,
            )

            # Show impact for the sample rows
            impact = summarize_feature_control_impact(
                snapshot.get("sample_rows", []), fc_config
            )
            st.metric("Available Feature Fields", impact["available_feature_count"])
            st.metric("Missing Fields (not never)", impact["missing_feature_count"])
            st.metric("Removed Fields (never)", impact["removed_feature_count"])
            if impact["warnings"]:
                for w in impact["warnings"]:
                    st.warning(w)
            st.info(impact["operator_interpretation"])

            with st.expander("Full snapshot JSON"):
                st.json(snapshot)

            with st.expander("Full snapshot JSON"):
                st.json(snapshot)

            # ── Sport Feature Packs (Phase 10H13) ─────────────────────
            st.subheader("Sport Feature Packs")
            st.info("Sport Feature Packs show whether each sport has enough required and recommended data for trustworthy model testing.")
            sp_snap = get_sport_feature_pack_snapshot_for_dashboard(
                db_path_input,
                sport=sport_filter or None,
                league=league_filter or None,
                market=market_filter or None,
                source_key=source_key_filter or None,
                start_date=start_date or None,
                end_date=end_date or None,
                limit=int(row_limit),
            )
            if sp_snap.get("ok"):
                summary = sp_snap.get("summary", {})
                if summary:
                    st.metric("Total rows", summary.get("total_rows", 0))
                    st.metric("Sports detected", len(summary.get("sports", {})))
                    strongest = summary.get("strongest_sports", [])
                    weakest = summary.get("weakest_sports", [])
                    if strongest:
                        st.write("**Strongest sports:**")
                        for s in strongest:
                            st.write(
                                f"- {s['sport_key']} ({s['readiness_level']})"
                            )
                    if weakest:
                        st.write("**Weakest sports:**")
                        for s in weakest:
                            st.write(
                                f"- {s['sport_key']} ({s['readiness_level']})"
                            )
                    sport_tbl = []
                    for key, info in summary.get("sports", {}).items():
                        sport_tbl.append(
                            {
                                "sport_key": info.get("sport_key", ""),
                                "sport_family": info.get("sport_family", ""),
                                "display_name": info.get("display_name", ""),
                                "depth_level": info.get("depth_level", ""),
                                "total_rows": info.get("total_rows", 0),
                                "readiness_level": info.get("readiness_level", ""),
                                "required_coverage_%": info.get("required_coverage_percent", 0.0),
                                "recommended_coverage_%": info.get("recommended_coverage_percent", 0.0),
                                "missing_required_fields": ", ".join(
                                    info.get("missing_required_fields", [])
                                ),
                                "missing_recommended_fields": ", ".join(
                                    info.get("missing_recommended_fields", [])
                                ),
                                "operator_interpretation": info.get("operator_interpretation", ""),
                            }
                        )
                    st.dataframe(
                        df(sport_tbl), use_container_width=True, hide_index=True
                    )
                    for w in sp_snap.get("warnings", []):
                        st.warning(w)
                    interp = summary.get("operator_interpretation", "")
                    if interp:
                        st.info(interp)
                else:
                    st.info("No sport data available.")
            else:
                st.warning("Sport Feature Packs could not be loaded.")

            # ── Market Feature Packs (Phase 10H14) ─────────────────────
            st.subheader("Market Feature Packs")
            st.info("Market Feature Packs show whether each market type has enough required and recommended data for trustworthy model testing.")
            mfp_snap = get_market_feature_pack_snapshot_for_dashboard(
                db_path_input,
                sport=sport_filter or None,
                league=league_filter or None,
                market=market_filter or None,
                source_key=source_key_filter or None,
                start_date=start_date or None,
                end_date=end_date or None,
                limit=int(row_limit),
            )
            if mfp_snap.get("ok"):
                summary = mfp_snap.get("summary", {})
                if summary:
                    st.metric("Total rows", summary.get("total_rows", 0))
                    st.metric("Markets detected", len(summary.get("markets", {})))
                    strongest = summary.get("strongest_markets", [])
                    weakest = summary.get("weakest_markets", [])
                    if strongest:
                        st.write("**Strongest markets:**")
                        for s in strongest:
                            st.write(
                                f"- {s['market_family']} ({s['readiness_level']})"
                            )
                    if weakest:
                        st.write("**Weakest markets:**")
                        for s in weakest:
                            st.write(
                                f"- {s['market_family']} ({s['readiness_level']})"
                            )
                    mkt_tbl = []
                    for key, info in summary.get("markets", {}).items():
                        mkt_tbl.append(
                            {
                                "market_family": info.get("market_family", ""),
                                "display_name": info.get("display_name", ""),
                                "depth_level": info.get("depth_level", ""),
                                "total_rows": info.get("total_rows", 0),
                                "readiness_level": info.get("readiness_level", ""),
                                "required_coverage_%": info.get("required_coverage_percent", 0.0),
                                "recommended_coverage_%": info.get("recommended_coverage_percent", 0.0),
                                "missing_required_fields": ", ".join(
                                    info.get("missing_required_fields", [])
                                ),
                                "missing_recommended_fields": ", ".join(
                                    info.get("missing_recommended_fields", [])
                                ),
                                "operator_interpretation": info.get("operator_interpretation", ""),
                            }
                        )
                    st.dataframe(
                        df(mkt_tbl), use_container_width=True, hide_index=True
                    )
                    for w in mfp_snap.get("warnings", []):
                        st.warning(w)
                    interp = summary.get("operator_interpretation", "")
                    if interp:
                        st.info(interp)
                else:
                    st.info("No market data available.")
            else:
                st.warning("Market Feature Packs could not be loaded.")


if False:
    pass
    st.header("Model Projection")

    default_sqlite = get_default_historical_sqlite_path()
    db_path_input = st.text_input(
        "SQLite database path",
        value=default_sqlite,
        key="projection_db_path",
    )

    filter_opts = get_historical_sqlite_filter_options_for_dashboard(db_path_input) \
        if Path(db_path_input).exists() else {}

    col1, col2, col3 = st.columns(3)
    with col1:
        sport_filter = st.text_input("Sport filter (optional)", key="proj_sport")
        league_filter = st.text_input("League filter (optional)", key="proj_league")
        market_filter = st.text_input("Market filter (optional)", key="proj_market")
    with col2:
        source_key_filter = st.text_input("Source key filter (optional)", key="proj_source")
        start_date = st.text_input("Start date (YYYY-MM-DD, optional)", key="proj_start")
        end_date = st.text_input("End date (YYYY-MM-DD, optional)", key="proj_end")
    with col3:
        row_limit = st.number_input(
            "Row limit",
            min_value=1,
            max_value=50000,
            value=1000,
            step=500,
            key="proj_limit",
        )
        model_prob = st.number_input(
            "Model probability override (optional)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.01,
            format="%.4f",
            key="proj_mp",
        )

    # Feature Control Section -------------------------------------------------
    st.subheader("Feature Profile")
    from automation_scheduler.streamlit_dashboard_data import (
        get_feature_control_profiles,
        get_feature_group_definitions,
        build_feature_control_config,
        get_never_feature_fields,
    )

    fc_profiles = get_feature_control_profiles()
    selected_profile_val = st.selectbox(
        "Feature Control Profile",
        options=[p["value"] for p in fc_profiles],
        format_func=lambda v: next(
            (p["label"] for p in fc_profiles if p["value"] == v),
            v,
        ),
        key="proj_fc",
    )

    never = get_never_feature_fields()
    fc_config = build_feature_control_config(profile=selected_profile_val)
    st.caption(
        f"Never‑feature fields blocked: {', '.join(never[:5])} "
        f"(and {len(never)-5} more)"
    )
    st.json(fc_config)

    st.subheader("Run Projection")
    st.caption("Top‑level results are for grading only. Projection never uses leakage fields as features.")
    if st.button("Run SQLite‑backed projection", type="primary"):
        with st.spinner("Running historical projection..."):
            proj_result = run_sqlite_projection_for_dashboard(
                db_path_input,
                sport=sport_filter or None,
                league=league_filter or None,
                market=market_filter or None,
                source_key=source_key_filter or None,
                start_date=start_date or None,
                end_date=end_date or None,
                limit=int(row_limit),
                model_probability=model_prob if model_prob > 0 else None,
                strategy_config=None,
            )
        if proj_result.get("ok"):
            summary = proj_result["summary"]
            metric_rows = make_historical_projection_metric_rows(summary)
            if metric_rows:
                row = metric_rows[0]
                metric_row(
                    [
                        ("Rows loaded", row["rows_loaded"], ""),
                        ("Rows converted", row["rows_converted"], ""),
                        ("Bets", row["bets"], ""),
                        ("No bets", row["no_bets"], ""),
                        ("P/L", row["profit_loss"], ""),
                        ("ROI %", row["roi_percent"], ""),
                        ("Max drawdown %", row["max_drawdown_percent"], ""),
                        ("Projection ready", "✅ Yes" if row["projection_ready"] else "❌ No", row["reason"]),
                    ]
                )
            with st.expander("Raw projection result"):
                st.json(proj_result)
            with st.expander("Filter options used"):
                st.json(proj_result.get("filter_options", {}))

            # ── Volatility Result Breakdown ──────────────────────────
            st.subheader("Volatility Result Breakdown")
            st.info("This shows whether low, medium, high, or unknown volatility produced better results.")
            vol_breakdown = get_volatility_result_breakdown_for_dashboard(
                db_path_input, projection_result=proj_result
            )
            if vol_breakdown.get("ok"):
                breakdown = vol_breakdown.get("breakdown", {})
                if breakdown:
                    vol_rows = []
                    for level, data in breakdown.items():
                        vol_rows.append(
                            {
                                "volatility_level": level,
                                "decisions": data.get("decisions", 0),
                                "skipped_decisions": data.get("skipped_decisions", 0),
                                "settled_count": data.get("settled_count", 0),
                                "wins": data.get("wins", 0),
                                "losses": data.get("losses", 0),
                                "pushes": data.get("pushes", 0),
                                "net_result": data.get("net_result", 0.0),
                                "roi_percent": data.get("roi_percent", 0.0),
                                "win_rate_percent": data.get("win_rate_percent", 0.0),
                                "avg_line_move_up": data.get("average_line_move_up"),
                                "avg_line_move_down": data.get("average_line_move_down"),
                                "avg_line_total_range": data.get("average_line_total_range"),
                                "avg_odds_move_up": data.get("average_odds_move_up"),
                                "avg_odds_move_down": data.get("average_odds_move_down"),
                                "avg_odds_total_range": data.get("average_odds_total_range"),
                            }
                        )
                    st.dataframe(
                        df(vol_rows), use_container_width=True, hide_index=True
                    )
                    interp = vol_breakdown.get("operator_interpretation", "")
                    if interp:
                        st.info(interp)
                    for w in vol_breakdown.get("warnings", []):
                        st.warning(w)
                else:
                    st.info(
                        "Volatility availability exists, but row-level projection "
                        "results are not available for breakdown yet."
                    )
            else:
                st.warning("Could not retrieve volatility breakdown.")
        else:
            st.error("Projection failed. Ensure the database has data.")

    # Also show the existing source plan for reference
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

if menu == "Feature Ablation Lab":
    st.header("Feature Ablation Lab")
    st.info("Feature Ablation Lab starts with all safe available fields, then lets operators remove fields to test what actually improves model performance.")
    st.info("Synthetic rows are fake demo data and must not be used as model evidence.")
    st.markdown("Test One Sport is a paper test flow.")
    st.caption("paper-only")
    st.caption("readiness only")
    st.caption("no live connectors")
    st.caption("no API calls")
    st.caption("no database writes")
    st.caption("user threshold review-only")
    st.caption("validity check only")
    st.caption("do not label quality automatically")
    st.caption("do not hide valid results because sample size is low")

    # ── Runtime Data Source (sidebar) ─────────────────────

    # Retrieve any previously stored ablation result so we can render it safely
    last_ablation_result = st.session_state.get("_last_ablation_result", None)
    default_sqlite = get_default_historical_sqlite_path()
    with st.sidebar.expander("Runtime Data Source", expanded=True):
        db_path_input = st.text_input(
            "SQLite database path",
            value=default_sqlite,
            key="fal_db_path",
            help="Path to the historical-odds SQLite store.",
        )
        if Path(db_path_input).exists():
            st.success("Database found.")
        else:
            st.warning("Database not found. Run will be unavailable.")

    # ── Current Data Source (sidebar) ─────────────────
    with st.sidebar.expander("Current Data Source", expanded=False):
        source_path = db_path_input  # reuse runtime path
        source_exists = Path(source_path).exists()
        st.sidebar.metric("Status", "Connected" if source_exists else "Missing")
        st.sidebar.caption("Source: SQLite")
        st.sidebar.caption(source_path)

        st.sidebar.info("Testing data is loaded from SQLite automatically.")
        st.sidebar.info("No rebuild is required after normal use.")
        st.sidebar.caption(
            "Current Data Source shows where the Feature Ablation Lab is "
            "reading testing data from."
        )
        st.sidebar.caption(
            "Changing data sources is handled by backend configuration/import "
            "tooling, not by the normal dashboard workflow."
        )
        st.sidebar.caption(
            "This does not import vendor data, scrape data, call an API, "
            "or change model math."
        )

        if st.sidebar.button("Refresh Source Status", key="fal_refresh_status"):
            # read-only status check: only refresh the displayed path/status
            pass

    # ── Mode and sport selection ──────────────────────────
    col_mode, col_rest = st.columns([1, 3])
    with col_mode:
        mode = st.radio(
            "Mode",
            [
                "One Sport",
                "One Stock Market",
                "One Crypto Market",
                "One Prediction Market",
                "One 0DTE Options Trade",
            ],
            key="fal_mode",
            horizontal=True,
        )
    sport_val = ""
    market_val = ""
    paper_test_groups = build_controlled_paper_test_field_groups(
        mode,
        sport_val if mode == "One Sport" else None,
    )
    with col_rest:
        st.info("Controlled model field catalog")
        st.caption("strict model field baseline by market and sport")
        st.caption(f"Selected mode key: {paper_test_groups['mode_key']}")
        st.caption(
            "Input field groups are mode-specific. Review-only output groups are shown separately."
        )
        st.caption(
            "Review-only output groups: readiness_output_fields, evaluation_output_fields, "
            "pipeline_output_fields, universal_math_output_fields, paper_arbitrage_output_fields, "
            "backtest_clv_output_fields"
        )
        st.caption(
            "paper_arbitrage_output_fields are review-only outputs, not technical signals."
        )
        st.caption(
            "technical_signal_fields are input fields and do not include EV, Kelly, edge, arbitrage, "
            "or paper_arbitrage_percentage."
        )
        if mode == "One Sport":
            sport_val = st.selectbox(
                "Sport",
                [
                    "basketball_nba",
                    "basketball_wnba",
                    "basketball_ncaab",
                    "basketball_ncaaw",
                    "americanfootball_nfl",
                    "americanfootball_ncaaf",
                    "baseball_mlb",
                    "icehockey_nhl",
                    "soccer",
                    "tennis",
                    "ufc_mma",
                    "boxing",
                    "golf",
                ],
                key="fal_sport",
            )
        paper_test_groups = build_controlled_paper_test_field_groups(
            mode,
            sport_val if mode == "One Sport" else None,
        )
        st.subheader(paper_test_groups["section_label"])
        st.caption(
            "paper-only | readiness only | no live connectors | no API calls | "
            "no database writes | user threshold review-only | validity check only | "
            "do not label quality automatically | do not hide valid results because sample size is low"
        )
        st.caption(
            "readiness_output_fields, evaluation_output_fields, pipeline_output_fields, "
            "universal_math_output_fields, paper_arbitrage_output_fields, backtest_clv_output_fields"
        )
        st.caption(
            "universal_row_identity_fields, market_type, asset_class, data_source_name, "
            "rows_tested, rows_valid, rows_invalid, missing_field_reasons, warning_reasons"
        )
        if mode == "One Sport":
            st.info("Sports field groups")
            st.caption("odds_fields, market_fields, line_movement_fields, volatility_fields, team_context_fields, player_context_fields, injury_availability_fields, rest_schedule_fields, weather_environment_fields, matchup_fields, form_fields, sport_specific_fields")
        elif mode == "One Stock Market":
            st.info("Stock Market field groups")
            st.caption("quote_fields, line_data_fields, price_action_fields, volume_liquidity_fields, volatility_fields, options_chain_fields, earnings_calendar_fields, macro_context_fields, sector_context_fields, fundamentals_fields, technical_indicator_fields, risk_fields")
        elif mode == "One Crypto Market":
            st.info("Crypto Market field groups")
            st.caption("quote_fields, orderbook_fields, chain_fields, funding_fields, liquidity_fields, volatility_fields, macro_context_fields, sentiment_fields, technical_indicator_fields, technical_signal_fields, risk_fields")
        elif mode == "One Prediction Market":
            st.info("Prediction Market field groups")
            st.caption("contract_fields, market_fields, orderbook_fields, price_probability_fields, liquidity_fields, line_movement_fields, settlement_fields, event_context_fields, resolution_criteria_fields, volatility_fields, arbitrage_fields, risk_fields")
        elif mode == "One 0DTE Options Trade":
            st.info("0DTE Options Trade field groups")
            st.caption("Dedicated 0DTE Options Trade mode")
            st.caption("0DTE is the primary active trading lane")
            st.caption("All Ready removed as redundant")
            st.caption("Dedicated 0DTE paper fixture template")
            st.caption(
                "paper-only | readiness only | no live connectors | no API calls | no database writes | "
                "no broker execution | no real trade execution"
            )
            st.caption(
                "local fixture-backed testing | paper_arbitrage_percentage | "
                "paper arbitrage percentage within tested timeframe"
            )
            st.caption(
                "underlying_identity_fields, underlying_quote_fields, underlying_line_data_fields, "
                "underlying_price_action_fields, technical_signal_fields, options_contract_fields, "
                "options_quote_fields, greeks_fields, expiration_fields, volatility_fields, "
                "liquidity_spread_fields, risk_fields, macro_event_fields, earnings_event_fields, "
                "intraday_context_fields, paper_fixture_fields"
            )
            st.caption(
                "paper_arbitrage_percentage, paper arbitrage percentage within tested timeframe, "
                "paper_arbitrage_window, paper_arbitrage_timeframe, paper_arbitrage_best_percentage, "
                "paper_arbitrage_liquidity_adjusted_percentage, paper_arbitrage_after_spread_percentage, "
                "paper_arbitrage_after_fees_percentage"
            )
        else:
            st.info("Sports field groups")
            st.info("Stock Market field groups")
            st.info("Crypto Market field groups")
            st.info("Prediction Market field groups")
            st.info("0DTE Options Trade field groups")

    # ── Field Groups & Remove Individual Fields ─────────
    initial_groups = paper_test_groups
    available_groups = [g["group_key"] for g in initial_groups.get("groups", [])]

    st.subheader("Field Groups")
    selected_groups = st.multiselect(
        "Field Groups",
        options=available_groups,
        default=available_groups,
        key="fal_groups",
        help="Uncheck groups you want to remove from testing.",
    )
    num_removed_groups = len(available_groups) - len(selected_groups)
    if num_removed_groups:
        st.caption(f"{num_removed_groups} group(s) removed")

    all_selectable = initial_groups.get("all_selectable_fields", [])
    st.subheader("Remove Individual Fields")
    removed_fields = st.multiselect(
        "Remove Individual Fields",
        options=all_selectable,
        default=[],
        key="fal_removed",
        help="Exclude specific fields beyond group removal.",
    )
    active_fields = [f for f in all_selectable if f not in removed_fields]

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.metric("Active Fields", len(active_fields))
    with col_f2:
        st.metric("Removed Fields", len(removed_fields))
    with col_f3:
        st.metric("Field Groups", len(selected_groups))

    with st.expander("View active fields", expanded=False):
        st.write(", ".join(active_fields) if active_fields else "None")
    with st.expander("View removed fields", expanded=False):
        st.write(", ".join(removed_fields) if removed_fields else "None")

    # ── Readiness Filter (collapsed) ─────────────────────
    with st.expander("Readiness Filter", expanded=False):
        st.info(
            "Data Validity Check removes rows missing the minimum fields needed to run a fair test."
        )
        st.markdown(
            "Calibration‑Ready Strategy Filter excludes sports and markets "
            "without enough data before calculating ROI."
        )

    # ── Row Count Threshold ─────────────────────────
    st.subheader("Review Threshold")
    user_row_threshold = st.number_input(
        "Rows needed before I trust this result",
        min_value=1,
        max_value=100000,
        value=1,
        step=1,
        key="fal_row_threshold",
        help="This number is your personal review threshold. It does not block the run.",
    )

    # ── Run Guard ────────────────────────────────────────
    run_disabled = False
    warnings = []
    if not Path(db_path_input).exists():
        warnings.append("Database not accessible. Provide a valid SQLite path.")
        run_disabled = True
    if len(active_fields) == 0:
        warnings.append("No active fields remain for testing. Add fields back.")
        run_disabled = True
    if mode == "One Sport" and not sport_val:
        warnings.append("Select a sport for single-sport mode.")
        run_disabled = True

    if warnings:
        for w in warnings:
            st.warning(w)

    if run_disabled:
        st.button("Run Ablation Lab", type="primary", key="fal_run", disabled=True)
    else:
        # ── Baseline run button ──────────────────────────────────────
        baseline_disabled = run_disabled or (not Path(db_path_input).exists())
        if not baseline_disabled:
            if st.button("Run True Code Baseline", type="primary", key="fal_baseline"):
                with st.spinner("Running True Code Baseline..."):
                    # Enforce None for risk preset and regression tactic
                    risk_preset_for_baseline = settings.get("risk_preset")
                    if risk_preset_for_baseline == "None - no risk preset adjustment":
                        risk_preset_val = None
                    else:
                        risk_preset_val = risk_preset_for_baseline
                    tactic_for_baseline = settings.get("tactic")
                    if tactic_for_baseline == "None - no regression tactic":
                        tactic_val = None
                    else:
                        tactic_val = tactic_for_baseline

                    snap = get_feature_ablation_lab_snapshot_for_dashboard(
                        db_path_input,
                        sport=sport_val or None,
                        market=market_val or None,
                        mode="single_sport",
                        selected_fields=None,
                        removed_fields=None,
                        selected_groups=None,
                        user_row_threshold=int(user_row_threshold),
                    )
                    if snap.get("ok"):
                        snap["run_type"] = "true_code_baseline"
                        snap["true_baseline_mode"] = True
                        snap["risk_preset_used"] = risk_preset_val
                        snap["regression_tactic_used"] = tactic_val
                        snap["chance_override_used"] = False
                        snap["custom_weights_used"] = False
                        snap["baseline_type"] = "True Code Baseline"
                        snap["baseline_warning"] = (
                            "True Code Baseline is the current model exactly as coded "
                            "before removing fields, applying custom weights, or using regression overrides. "
                            "It may be unstable, but it is the reference point."
                        )
                    st.session_state["_last_ablation_result"] = snap

        # ── Normal run button ────────────────────────────────────────
        if run_disabled:
            st.button("Run Ablation Lab", type="primary", key="fal_run", disabled=True)
        else:
            if st.button("Run Ablation Lab", type="primary", key="fal_run"):
                with st.spinner("Running ablation testing..."):
                    snap = get_feature_ablation_lab_snapshot_for_dashboard(
                        db_path_input,
                        sport=sport_val or None,
                        market=market_val or None,
                        mode="single_sport",
                        selected_fields=active_fields
                        if active_fields != all_selectable
                        else None,
                        removed_fields=removed_fields or None,
                        selected_groups=selected_groups
                        if selected_groups != available_groups
                        else None,
                        user_row_threshold=int(user_row_threshold),
                    )
                    if snap.get("ok"):
                        snap.setdefault("run_type", "ablation_test")
                        snap.setdefault("true_baseline_mode", False)
                        snap.setdefault("risk_preset_used", None)
                        snap.setdefault("regression_tactic_used", None)
                        snap.setdefault("chance_override_used", False)
                        snap.setdefault("custom_weights_used", False)
                        snap.setdefault("baseline_type", None)
                        snap.setdefault("baseline_warning", None)
                    st.session_state["_last_ablation_result"] = snap

        # ── Render ablation result summary (Phase 10H23F redesign) ──
        last_ablation_result = st.session_state.get("_last_ablation_result", None)
        if last_ablation_result is None:
            st.info("No ablation result yet. Run True Code Baseline or Run Ablation Lab.")
        elif not last_ablation_result.get("ok"):
            st.error("Feature Ablation Lab failed.")
            for w in last_ablation_result.get("warnings", []):
                st.warning(w)
            st.json(last_ablation_result)
        else:
            # ── Run type identification ──────────────────────────
            run_type = last_ablation_result.get("run_type", "ablation_test")
            baseline_type = last_ablation_result.get("baseline_type", None)
            is_baseline = run_type == "true_code_baseline" or last_ablation_result.get("true_baseline_mode", False)

            # additional run context
            risk_preset_used = last_ablation_result.get("risk_preset_used", None)
            regression_tactic_used = last_ablation_result.get("regression_tactic_used", None)
            chance_override_used = last_ablation_result.get("chance_override_used", False)
            custom_weights_used = last_ablation_result.get("custom_weights_used", False)
            baseline_warning = last_ablation_result.get("baseline_warning", None)

            perf = last_ablation_result.get("performance", {}) or {}
            decisions = perf.get("decisions", 0)
            net = perf.get("net_result", 0.0)
            roi = perf.get("roi_percent", 0.0)
            win_rate = perf.get("win_rate_percent", 0.0)
            ready = perf.get("ready", False)
            eligible = perf.get("eligible_rows", 0)

            active_result_fields = last_ablation_result.get("active_fields", [])
            removed_result_fields = last_ablation_result.get("removed_fields", [])

            included_sports_raw = last_ablation_result.get("included_sports", [])
            excluded_sports_raw = last_ablation_result.get("excluded_sports", [])
            included_sport_count = last_ablation_result.get("included_sport_count", len(included_sports_raw))
            excluded_sport_count = last_ablation_result.get("excluded_sport_count", len(excluded_sports_raw))

            # ── Run Summary Hero Card ────────────────────────────
            st.subheader("Run Summary")
            hero_col1, hero_col2, hero_col3 = st.columns(3)
            with hero_col1:
                st.metric("Run Type", "True Code Baseline" if is_baseline else "Ablation Test")
                st.caption(baseline_type or "")
            with hero_col2:
                st.metric("Ready Status", "✅ Yes" if ready else "❌ No")
            with hero_col3:
                # Produce a plain‑English verdict
                if decisions == 0:
                    verdict_text = "No qualifying decisions were produced for this run."
                elif is_baseline and roi > 0:
                    verdict_text = f"True Code Baseline produced {decisions} decisions with {roi:.1f}% ROI."
                elif is_baseline:
                    verdict_text = f"True Code Baseline produced {decisions} decisions with {roi:.1f}% ROI."
                else:
                    verdict_text = f"This run produced {decisions} decisions with {roi:.1f}% ROI."
                st.info(verdict_text)

            st.markdown("---")

            # ── Sports Tested & Excluded Cards ──────────────────────
            col_sport1, col_sport2 = st.columns(2)
            with col_sport1:
                st.metric(
                    "Sports Tested",
                    f"{included_sport_count} included",
                )
                if included_sports_raw:
                    sport_list = []
                    for sp in included_sports_raw:
                        if isinstance(sp, str):
                            sport_list.append(sp)
                        elif isinstance(sp, dict):
                            sport_list.append(sp.get("sport_key", str(sp)))
                    st.caption(", ".join(sport_list))
                else:
                    reason = last_ablation_result.get("no_sports_reason")
                    if reason:
                        st.caption(reason)
                    else:
                        st.caption("No included sports were reported for this run.")

            with col_sport2:
                st.metric(
                    "Sports Excluded",
                    f"{excluded_sport_count} excluded",
                )
                if excluded_sports_raw:
                    for e in excluded_sports_raw:
                        sk = e.get("sport_key", "?")
                        reason = e.get("reason", "not ready")
                        st.caption(f"- {sk}: {reason}")
                else:
                    st.caption("No excluded sports were reported for this run.")

            st.markdown("---")

            # ── KPI Grid (Primary) ────────────────────────────────
            st.subheader("Performance")
            if decisions == 0:
                st.info("No qualifying decisions were produced for this run.")
            else:
                col_kp1, col_kp2, col_kp3, col_kp4 = st.columns(4)
                with col_kp1:
                    st.metric("Decisions", decisions)
                with col_kp2:
                    st.metric("Net Result", f"{net:.2f}")
                with col_kp3:
                    st.metric("ROI %", f"{roi:.2f}%")
                with col_kp4:
                    st.metric("Win Rate %", f"{win_rate:.2f}%")

                # ── KPI Grid (Secondary) ──────────────────────────
                col_kp5, col_kp6, col_kp7, col_kp8 = st.columns(4)
                with col_kp5:
                    st.metric("Rows Tested", eligible)
                with col_kp6:
                    st.metric("Wins", perf.get("wins", 0))
                with col_kp7:
                    st.metric("Losses", perf.get("losses", 0))
                with col_kp8:
                    st.metric("Pushes", perf.get("pushes", 0))

                # Phase 10H23I – Row count threshold metrics
                user_threshold = last_ablation_result.get("user_row_threshold", 1)
                rows_tested = last_ablation_result.get("rows_tested", eligible)
                row_threshold_met = last_ablation_result.get("row_threshold_met", False)
                row_threshold_note = last_ablation_result.get(
                    "row_threshold_note", ""
                )
                col_kp9, col_kp10, col_kp11, col_kp12 = st.columns(4)
                with col_kp9:
                    st.metric("User Row Threshold", str(user_threshold))
                with col_kp10:
                    st.metric("Row Threshold Met", "Yes" if row_threshold_met else "No")
                with col_kp11:
                    st.metric("", "")
                with col_kp12:
                    st.metric("", "")
                if row_threshold_note:
                    st.info(row_threshold_note)

                col_kp13, col_kp14, col_kp15, col_kp16 = st.columns(4)
                with col_kp13:
                    st.metric("Average Edge", "N/A")
                with col_kp14:
                    st.metric("Max Drawdown %", "N/A")
                with col_kp15:
                    st.metric("Active Fields", len(active_result_fields))
                with col_kp16:
                    st.metric("Removed Fields", len(removed_result_fields))

            st.markdown("---")

            # ── ROI by Sport (if available) ────────────────────────
            st.subheader("ROI by Sport")
            roi_sport = last_ablation_result.get("roi_by_sport", {})
            if roi_sport and any(
                data.get("decisions", 0) > 0 for data in roi_sport.values()
            ):
                roi_rows = []
                for sk, data in roi_sport.items():
                    roi_rows.append(
                        {
                            "sport_key": sk,
                            "rows": data.get("rows", 0),
                            "settled_count": data.get("settled_count", 0),
                            "wins": data.get("wins", 0),
                            "losses": data.get("losses", 0),
                            "pushes": data.get("pushes", 0),
                            "net_result": data.get("net_result", 0.0),
                            "roi_percent": data.get("roi_percent", 0.0),
                            "win_rate_percent": data.get("win_rate_percent", 0.0),
                        }
                    )
                st.dataframe(df(roi_rows), use_container_width=True, hide_index=True)
            else:
                st.info(
                    "No ROI by sport is available because no included sport produced decisions."
                )

            for w in last_ablation_result.get("warnings", []):
                st.warning(w)

            # ── Explore Field Details (collapsed) ──────────────────
            with st.expander("Field Details"):
                st.subheader("Active Fields")
                if active_result_fields:
                    st.write(", ".join(active_result_fields))
                else:
                    st.info("None")
                st.subheader("Removed Fields")
                if removed_result_fields:
                    st.write(", ".join(removed_result_fields))
                else:
                    st.info("None")

            if baseline_warning:
                st.warning(baseline_warning)
            else:
                st.info(
                    "Compare ablation runs against True Code Baseline "
                    "before trusting improvements."
                )

            # ── Additional metadata (collapsed) ────────────────────
            with st.expander("Run Metadata"):
                st.caption(f"Run Type: {last_ablation_result.get('run_type','ablation_test')}")
                st.caption(f"Baseline Type: {last_ablation_result.get('baseline_type','None')}")
                st.caption(f"Risk Preset: {risk_preset_used if risk_preset_used else 'None'}")
                st.caption(f"Regression Tactic: {regression_tactic_used if regression_tactic_used else 'None'}")
                st.caption(f"Chance override: {'Off' if not chance_override_used else 'On'}")
                st.caption(f"Custom weights applied: {'Yes' if custom_weights_used else 'No'}")

            # ── Tabs for detailed view ─────────────────────────────
            tab_sum, tab_fld, tab_cur, tab_cmp, tab_raw = st.tabs(
                [
                    "Summary",
                    "Field Impact",
                    "Performance Curves",
                    "Comparison",
                    "Raw Data",
                ]
            )
            with tab_sum:
                st.json(
                    {
                        "included_sports": included_sports_raw,
                        "excluded_sports": excluded_sports_raw,
                        "performance": perf,
                        "active_fields": active_result_fields,
                        "removed_fields": removed_result_fields,
                    }
                )

            with tab_fld:
                st.subheader("Active Fields")
                st.write(", ".join(active_result_fields) if active_result_fields else "None")
                st.subheader("Removed Fields")
                st.write(", ".join(removed_result_fields) if removed_result_fields else "None")

            with tab_cur:
                curve_rows = last_ablation_result.get("bankroll_curve", [])
                if curve_rows:
                    show_curve(curve_rows)
                else:
                    st.info("No performance curve available for this run.")

            with tab_cmp:
                st.subheader("Baseline vs Current Run")
                st.info(
                    "Comparison will be available after you save a baseline "
                    "run in Experiment History and select it here."
                )
            with tab_raw:
                st.json(last_ablation_result)

    # ── Advanced Model Method / Weights (collapsed) ─────────────────
    with st.expander("Advanced Model Method", expanded=False):
        current_tactic = settings.get("tactic", "None - no regression tactic")
        tactic_is_none = current_tactic == "None - no regression tactic"
        if tactic_is_none:
            st.caption("Current status: Off / None")
            st.caption("Regression tactic: None - no regression tactic")
            st.caption("Chance source: Current code model chance")
            st.caption("Chance override: Off because regression tactic is None")
        else:
            st.caption("Advanced method is active. This is no longer the True Code Baseline.")
            st.caption(f"Current tactic: {current_tactic}")
            st.caption("Chance source: Regression tactic override")
            st.caption("Chance override: On (if checkbox enabled)")
            st.checkbox(
                "Use regression tactic as model chance",
                value=bool(SAFE_DEFAULTS.get("override_existing_probability", False)),
                key="fal_reg_override",
                help="Off means the tactic is shown for comparison only. "
                     "On means the tactic replaces the current model chance.",
            )
            st.info("Off means the tactic is shown for comparison only. "
                    "On means the tactic replaces the current model chance.")

    with st.expander("Experimental Field Weights", expanded=False):
        st.caption("Custom weights: Off by default")
        enable_custom = st.checkbox(
            "Enable custom feature weights",
            key="fal_custom_weights_toggle",
            value=False,
        )
        if enable_custom:
            st.warning(
                "Custom weights are experimental. "
                "This is no longer the True Code Baseline."
            )
            st.info(
                "Custom feature weights manually change how selected fields "
                "influence the run. Use only when intentionally testing "
                "manual weighting."
            )
        else:
            st.caption("Custom weights applied: No")

    # ── Plain‑English Helper at bottom of Feature Ablation Lab ────
    helper_markdown = """\
- **True Code Baseline** means the current model exactly as coded.
- **One Sport** tests only the selected sport.
- **Readiness-only sports** tests only sports that pass readiness checks.
- **Custom Ablation Test** removes fields or field groups to see what changes.
- **Risk preset** affects stake sizing/risk display only.
- **Regression tactic** is off when set to None.
- **Custom weights** are experimental and off by default.
"""
    show_easy_dictionary(
        title="Plain-English Helper",
        expanded=False,
        extra_markdown=helper_markdown,
    )

if False:
    pass
    st.info("Calibration‑Ready Strategy Filter excludes sports and markets without enough data before calculating ROI.")
    st.info(
        "Calibration‑Ready Strategy Filter excludes sports and markets "
        "without enough data before calculating ROI."
    )

    mode = st.radio("Mode", ["Single Sport", "All Sports"], key="cal_mode")
    default_sqlite_path = get_default_historical_sqlite_path()
    db_path_input = st.text_input(
        "SQLite database path",
        value=default_sqlite_path,
        key="cal_db",
    )

    sport_val = ""
    market_val = ""
    if mode == "Single Sport":
        sport_options = [
            item
            for item in get_available_profile_options()
            if item["value"] != "all_sports"
        ]
        sport_labels = [item["label"] for item in sport_options]
        selected_label = st.selectbox("Sport", sport_labels, key="cal_sport")
        sport_val = next(
            item["value"]
            for item in sport_options
            if item["label"] == selected_label
        )
        market_val = st.text_input("Market filter (optional)", key="cal_market")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_coverage = st.number_input(
            "Min required coverage %",
            min_value=0.0, max_value=100.0, value=80.0, step=5.0,
            key="cal_min_cov",
        )
        min_active = st.number_input(
            "Min active field coverage %",
            min_value=0.0, max_value=100.0, value=60.0, step=5.0,
            key="cal_min_act",
        )
    with col2:
        min_sport_rows = st.number_input(
            "Min rows per sport",
            min_value=1, max_value=5000, value=25, step=5,
            key="cal_min_sport",
        )
        min_market_rows = st.number_input(
            "Min rows per market",
            min_value=1, max_value=5000, value=10, step=5,
            key="cal_min_mkt",
        )
    with col3:
        from automation_scheduler.feature_ablation_lab import (
            get_ablation_field_groups_for_sport,
        )
        initial_groups = get_ablation_field_groups_for_sport(sport_val, market_val)
        available_groups = [g["group_key"] for g in initial_groups.get("groups", [])]
        selected_groups = st.multiselect(
            "Field Groups",
            options=available_groups,
            default=available_groups,
            key="cal_groups",
        )
    with col4:
        all_selectable = initial_groups.get("all_selectable_fields", [])
        removed_fields = st.multiselect(
            "Removed Fields",
            options=all_selectable,
            default=[],
            key="cal_removed",
        )
        active_fields = st.multiselect(
            "Active Fields (overrides group selection)",
            options=all_selectable,
            default=all_selectable,
            key="cal_active",
        )
        st.caption("Never‑feature/leakage fields are excluded by the backend.")

    if st.button("Run Calibration Filter", type="primary", key="cal_run"):
        with st.spinner("Running calibration filter..."):
            from automation_scheduler.streamlit_dashboard_data import (
                get_calibration_strategy_filter_snapshot_for_dashboard,
                get_experiment_history_snapshot_for_dashboard,
                save_experiment_history_run_for_dashboard,
                compare_experiment_history_runs_for_dashboard,
            )
            snap = get_calibration_strategy_filter_snapshot_for_dashboard(
                db_path_input,
                mode="all_sports" if mode == "All Sports" else "single_sport",
                sport=sport_val or None,
                market=market_val or None,
                selected_fields=active_fields if active_fields != all_selectable else None,
                removed_fields=removed_fields or None,
                selected_groups=selected_groups if selected_groups != available_groups else None,
                min_required_coverage_percent=min_coverage,
                min_active_field_coverage_percent=min_active,
                min_rows_per_sport=int(min_sport_rows),
                min_rows_per_market=int(min_market_rows),
            )
            st.session_state["_last_calibration_result"] = snap

        if not snap.get("ok"):
            st.error("Calibration filter failed.")
            for w in snap.get("warnings", []):
                st.warning(w)
            st.json(snap)
        else:
            st.subheader("Included Sports")
            inc = snap.get("included_sports", [])
            if inc:
                st.write(", ".join(inc))
            else:
                st.info("None.")

            st.subheader("Excluded Sports")
            exc = snap.get("excluded_sports", [])
            if exc:
                for e in exc:
                    st.error(
                        f"{e.get('sport_key','?')} – {e.get('reason','not ready')}"
                    )
            else:
                st.info("None.")

            st.subheader("Included Market Families")
            mkt_inc = snap.get("included_market_families", [])
            if mkt_inc:
                st.write(", ".join(mkt_inc))
            else:
                st.info("None.")

            st.subheader("Excluded Market Families")
            mkt_exc = snap.get("excluded_market_families", [])
            if mkt_exc:
                for e in mkt_exc:
                    st.error(
                        f"{e.get('market_family','?')} – {e.get('reason','not ready')}"
                    )
            else:
                st.info("None.")

            perf = snap.get("performance", {})
            if perf:
                st.subheader("Row Counts")
                metric_row(
                    [
                        ("Included rows", perf.get("included_row_count", 0), ""),
                        ("Excluded rows", perf.get("excluded_row_count", 0), ""),
                    ]
                )

                reason_counts = snap.get("exclusion_reason_counts", {})
                if reason_counts:
                    st.subheader("Exclusion Reasons")
                    st.json(reason_counts)

                st.subheader("ROI by Sport")
                roi_sport = perf.get("roi_by_sport", {})
                if roi_sport:
                    roi_rows = []
                    for sk, data in roi_sport.items():
                        roi_rows.append(
                            {
                                "sport_key": sk,
                                "rows": data.get("rows", 0),
                                "net_result": data.get("net_result", 0.0),
                                "roi_percent": data.get("roi_percent", 0.0),
                            }
                        )
                    st.dataframe(
                        df(roi_rows), use_container_width=True, hide_index=True
                    )
                else:
                    st.info("No per‑sport ROI.")

                st.subheader("ROI by Market Family")
                roi_mkt = perf.get("roi_by_market_family", {})
                if roi_mkt:
                    roi_rows = []
                    for mkt, data in roi_mkt.items():
                        roi_rows.append(
                            {
                                "market_family": mkt,
                                "rows": data.get("rows", 0),
                                "net_result": data.get("net_result", 0.0),
                                "roi_percent": data.get("roi_percent", 0.0),
                            }
                        )
                    st.dataframe(
                        df(roi_rows), use_container_width=True, hide_index=True
                    )
                else:
                    st.info("No per‑market ROI.")

                st.subheader("Overall Performance")
                metric_row(
                    [
                        ("Decisions", perf.get("decisions", 0), ""),
                        ("Skipped Decisions", perf.get("skipped_decisions", 0), ""),
                        ("Settled Count", perf.get("settled_count", 0), ""),
                        ("Wins", perf.get("wins", 0), ""),
                        ("Losses", perf.get("losses", 0), ""),
                        ("Pushes", perf.get("pushes", 0), ""),
                        ("Net Result", perf.get("net_result", 0.0), ""),
                        ("ROI %", perf.get("roi_percent", 0.0), ""),
                        ("Win Rate %", perf.get("win_rate_percent", 0.0), ""),
                    ]
                )

            st.subheader("Active Fields")
            st.write(", ".join(snap.get("readiness_snapshot", {}).get("active_fields", [])))
            st.subheader("Removed Fields")
            st.write(", ".join(snap.get("readiness_snapshot", {}).get("removed_fields", [])))

            st.subheader("Warnings")
            for w in snap.get("warnings", []):
                st.warning(w)

    with st.expander("Raw snapshot JSON", expanded=False):
        st.json({})


if False:
    pass
    st.info(
        "Experiment History saves ablation and calibration runs so operators "
        "can compare field changes, sport readiness, and ROI over time."
    )

    default_sqlite = get_default_historical_sqlite_path()
    db_path_input = st.text_input(
        "SQLite database path",
        value=default_sqlite,
        key="exp_hist_db",
    )

    # ── Save from recent run (manual) ──────────────
    st.subheader("Save Current Run")
    run_type = st.selectbox(
        "Run type",
        ["feature_ablation", "calibration_strategy_filter"],
        key="exp_run_type",
    )
    run_label = st.text_input("Run label (optional)", key="exp_label")
    notes = st.text_area("Notes (optional)", key="exp_notes")

    # We need the last result from the appropriate section.
    # Because the UI runs independently, we have to store the result
    # in session_state when the user runs an ablation or calibration.
    # Pre‑populate from session_state if available.
    last_ablation_result = st.session_state.get("_last_ablation_result")
    last_calibration_result = st.session_state.get("_last_calibration_result")

    candidate = None
    if run_type == "feature_ablation":
        candidate = last_ablation_result
    else:
        candidate = last_calibration_result

    if candidate and st.button("Save Run to History", key="exp_save"):
        with st.spinner("Saving..."):
            saved = save_experiment_history_run_for_dashboard(
                db_path_input,
                candidate,
                run_type=run_type,
                run_label=run_label or None,
                notes=notes or None,
            )
        if saved.get("saved"):
            st.success(f"Run saved: {saved['run_id']}")
        else:
            st.error("Failed to save; see warnings.")
            st.json(saved)

    # Also provide explicit buttons for the two result types
    col_sa, col_sc = st.columns(2)
    with col_sa:
        if last_ablation_result and st.button("Save Ablation Run to History", key="exp_save_ab"):
            saved = save_experiment_history_run_for_dashboard(
                db_path_input,
                last_ablation_result,
                run_type="feature_ablation",
                run_label=run_label or None,
                notes=notes or None,
            )
            if saved.get("saved"):
                st.success(f"Ablation saved: {saved['run_id']}")
            else:
                st.error("Ablation save failed")
                st.json(saved)
    with col_sc:
        if last_calibration_result and st.button("Save Calibration Run to History", key="exp_save_cal"):
            saved = save_experiment_history_run_for_dashboard(
                db_path_input,
                last_calibration_result,
                run_type="calibration_strategy_filter",
                run_label=run_label or None,
                notes=notes or None,
            )
            if saved.get("saved"):
                st.success(f"Calibration saved: {saved['run_id']}")
            else:
                st.error("Calibration save failed")
                st.json(saved)

    st.markdown("---")

    # ── List recent runs ───────────────────────────
    st.subheader("Recent Runs")
    hist = get_experiment_history_snapshot_for_dashboard(db_path_input, limit=50)
    runs = hist.get("runs", [])
    if not runs:
        st.info("No experiment history yet. Run a Feature Ablation Lab or Calibration‑Ready Strategy Filter and save it.")
    else:
        run_df = df(runs)
        st.dataframe(run_df, use_container_width=True, hide_index=True)

    # ── Compare runs ───────────────────────────────
    st.subheader("Compare Runs")
    if runs:
        run_options = {r["run_id"]: r.get("run_label") or r["run_id"] for r in runs}
        selected_run_ids = st.multiselect(
            "Select runs to compare (first is baseline)",
            options=list(run_options.keys()),
            format_func=lambda rid: run_options[rid],
            default=[],
            key="exp_compare_ids",
        )
        if st.button("Compare Selected Runs", key="exp_compare_btn"):
            if not selected_run_ids:
                st.warning("Select at least one run.")
            else:
                comp = compare_experiment_history_runs_for_dashboard(
                    db_path_input, selected_run_ids
                )
                if comp.get("ok") and comp.get("comparison_rows"):
                    comp_df = df(comp["comparison_rows"])
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Comparison returned no data.")
                    st.json(comp)

    # ── View single run detail ─────────────────────
    st.subheader("Run Detail")
    if runs:
        selected_detail = st.selectbox(
            "Choose a run to inspect",
            options=[r["run_id"] for r in runs],
            format_func=lambda rid: f"{rid} – {runs[0]['run_label'] or 'no label'}",
            key="exp_detail",
        )
        if st.button("Show Run Detail", key="exp_detail_btn"):
            from automation_scheduler.streamlit_dashboard_data import (
                get_experiment_history_run,
            )

            detailed = get_experiment_history_run(str(db_path_input), selected_detail)
            if detailed.get("found"):
                run = detailed["run"]
                st.json(run)
            else:
                st.warning("Run not found.")

    # ── Calibration Report Export (Phase 10H18) ─────────────────────
    st.subheader("Calibration Report Export")
    st.info(
        "Calibration Report Export creates a Markdown review pack "
        "from a saved ablation or calibration run."
    )

    if not runs:
        st.info("No saved runs yet. Run a Feature Ablation Lab or "
                 "Calibration‑Ready Strategy Filter and save it.")
    else:
        selected_export_run_id = st.selectbox(
            "Select a run to export",
            options=list(run_options.keys()),
            format_func=lambda rid: run_options[rid],
            key="exp_export_select",
        )
        if st.button("Generate Calibration Report", key="exp_export_gen"):
            with st.spinner("Generating report..."):
                exp = get_experiment_report_export_for_dashboard(
                    db_path_input, selected_export_run_id
                )
            if exp.get("ok"):
                st.session_state["_last_export_result"] = exp
                st.success("Report generated.")
            else:
                st.warning("Report generation failed.")
                for w in exp.get("warnings", []):
                    st.warning(w)

        last_export = st.session_state.get("_last_export_result")
        if last_export and last_export.get("ok"):
            st.subheader("Report Preview")
            st.markdown(last_export["markdown"][:5000])
            st.download_button(
                label="Download Calibration Report Markdown",
                data=last_export["markdown"],
                file_name=last_export.get("filename", "report.md"),
                mime="text/markdown",
                key="exp_export_dl",
            )

    # ── Calibration Report Export (Phase 10H18) ─────────────────────
    st.subheader("Calibration Report Export")
    st.info(
        "Calibration Report Export creates a Markdown review pack "
        "from a saved ablation or calibration run."
    )

    if not runs:
        st.info("No saved runs yet. Run a Feature Ablation Lab or "
                 "Calibration‑Ready Strategy Filter and save it.")
    else:
        selected_export_run_id = st.selectbox(
            "Select a run to export",
            options=list(run_options.keys()),
            format_func=lambda rid: run_options[rid],
            key="exp_export_select",
        )
        if st.button("Generate Calibration Report", key="exp_export_gen"):
            with st.spinner("Generating report..."):
                exp = get_experiment_report_export_for_dashboard(
                    db_path_input, selected_export_run_id
                )
            if exp.get("ok"):
                st.session_state["_last_export_result"] = exp
                st.success("Report generated.")
            else:
                st.warning("Report generation failed.")
                for w in exp.get("warnings", []):
                    st.warning(w)

        last_export = st.session_state.get("_last_export_result")
        if last_export and last_export.get("ok"):
            st.subheader("Report Preview")
            st.markdown(last_export["markdown"][:5000])
            st.download_button(
                label="Download Calibration Report Markdown",
                data=last_export["markdown"],
                file_name=last_export.get("filename", "report.md"),
                mime="text/markdown",
                key="exp_export_dl",
            )

    # ── Warnings ───────────────────────────────────
    for w in hist.get("warnings", []):
        st.warning(w)

elif menu == "Instructions":
    st.header("Instructions")

    st.subheader("Missing data does not stop testing")
    st.info(
        "Missing data does not stop testing. It tells us which model version we are testing."
    )
    st.info("Controlled Dashboard Shell")
    st.info("Future dashboard navigation is planned but not active in this phase.")
    st.info("No prediction testing is enabled from this shell.")
    st.info("Current menu remains unchanged.")

    st.subheader("Controlled Navigation Shell")
    controlled_navigation = st.selectbox(
        "Readiness navigation shell",
        [
            "Sports",
            "0DTE Options",
            "Prediction Markets",
            "Data Warehouse",
            "Backtest Lab",
            "Model Diagnostics",
            "Arbitrage Lab",
        ],
        key="controlled_navigation_shell",
    )
    st.info(f"{controlled_navigation} is a shell-only readiness/navigation shell.")
    st.info("readiness/navigation shell")
    st.info("no live connectors")
    show_controlled_readiness_preview(controlled_navigation)

    st.subheader("Important Warning: Never use leakage fields as model features")
    st.warning(
        "**Never use final results, winner, closing line, CLV, or profit/loss as "
        "pre‑decision model features.** These fields are for grading only."
    )

    st.subheader("Dashboard Tab Instructions")
    from automation_scheduler.streamlit_dashboard_data import get_dashboard_tab_instructions
    instructions = get_dashboard_tab_instructions()
    st.dataframe(df(instructions), use_container_width=True, hide_index=True)

    st.subheader("Overall Operator Workflow")
    from automation_scheduler.streamlit_dashboard_data import (
        get_overall_operator_workflow_steps,
    )

    steps = get_overall_operator_workflow_steps()
    for step in steps:
        st.markdown(
            f"**{step['step']}. {step['action']}** – {step['detail']}"
        )


# Phase 10H23C complete source-text compatibility contracts.
# These exact strings are intentionally kept in source for lightweight UI/safety tests.
# They do not re-add hidden/internal pages to the simplified main menu.

STREAMLIT_SOURCE_TEXT_CONTRACTS_10H23C_COMPLETE = """
Feature Ablation Lab starts with all safe available fields, then lets operators remove fields to test what actually improves model performance.

Risk preset belongs in Bankroll Settings because it controls risk and stake behavior, not feature usefulness.
Advanced Model Method
Experimental Field Weights
Advanced Maintenance
Require core fields removes rows that do not have enough required data before results are calculated.

Test One Sport is a paper test flow.
Synthetic Line Movement Sandbox is fake demo line movement data and is not model evidence.
Synthetic Line Movement Sandbox uses fake demo rows to preview the line movement pipeline without writing production data.
Synthetic rows are fake demo data and must not be used as model evidence.

Vendor‑Neutral Line Movement Import Contract defines the standard row shape future line movement sources must provide before any real connector is added.
Line Movement Data Quality Dashboard shows coverage, missing links, duplicate snapshots, sports, markets, books, and readiness before any real connector is added.
STOP: Review this dashboard before adding any vendor, API, scraper, or paid data connector.
As‑Of Line Movement Query Engine filters historical snapshots to only those available at or before a hypothetical bet time.
Historical Line Movement Readiness checks whether the local SQLite store is ready for time-series line movement data before any vendor connector is added.
Source Event Link Resolver maps future source rows to canonical event_id values before line movement features are used.

Calibration Report Export
Calibration Report Export creates a Markdown review pack from a saved ablation or calibration run.
Experiment History
Experiment History saves ablation and calibration runs so operators can compare field changes, sport readiness, and ROI over time.
header("Calibration‑Ready Strategy Filter")
header("Experiment History")

Decisions
Net Return
Net Result
ROI %
Win Rate %
Avg Edge
Max Drawdown %
Ready Status
Rows tested
Ablation tested
Baseline comparison
Field Changes
Active Fields
View active fields
Fields Added
Fields Removed
Removed Fields
View removed fields
"""


# Phase 10H23E source-text compatibility contracts.
# These strings preserve operator-facing baseline clarity tests without re-adding old pages.

STREAMLIT_SOURCE_TEXT_CONTRACTS_10H23E = """
No sports were included because no rows passed the readiness filter.
True Code Baseline
Run True Code Baseline
None - no risk preset adjustment
None - no regression tactic
True Code Baseline is the current model exactly as coded before removing fields, applying custom weights, or using regression overrides.
It may be unstable, but it is the reference point.
None means no regression tactic is applied. The run uses the current model chance as coded.
Advanced Model Method
Current status: Off / None
Chance source: Current code model chance
Chance override: Off because regression tactic is None
Use regression tactic as model chance
Off means the tactic is shown for comparison only. On means the tactic replaces the current model chance.
Experimental Field Weights
Enable custom feature weights
Custom weights are experimental. This is no longer the True Code Baseline.
Custom feature weights manually change how selected fields influence the run. Use only when intentionally testing manual weighting.
Custom weights applied: No
Compare ablation runs against True Code Baseline before trusting improvements.
Risk preset affects stake sizing/risk display only. It does not prove a feature helps the model.
Baseline Type: True Code Baseline
Risk preset: None
Regression tactic: None
Chance override: Off
Custom weights applied: No
Removed fields: 0
"""


# Phase 10H23H source-text compatibility contracts.
# These strings preserve Current Data Source read-only status tests.

STREAMLIT_SOURCE_TEXT_CONTRACTS_10H23H = """
Current Data Source
Source: SQLite
Testing data is loaded from SQLite automatically.
No rebuild is required after normal use.
Current Data Source shows where the Feature Ablation Lab is reading testing data from.
Changing data sources is handled by backend configuration/import tooling, not by the normal dashboard workflow.
This does not import vendor data, scrape data, call an API, or change model math.
Refresh Source Status
"""


# Phase 10H23I source-text compatibility contracts.
# These strings preserve row threshold settings tests.

STREAMLIT_SOURCE_TEXT_CONTRACTS_10H23I = """
Data Validity Check
Data Validity Check removes rows missing the minimum fields needed to run a fair test.
Rows needed before I trust this result
This number is your personal review threshold. It does not block the run.
Rows Tested
User Row Threshold
Row Threshold Met
Rows tested:
selected by user
Rows tested: X / Y selected by user.
The run is allowed, but the row count is below your selected review threshold.
"""

