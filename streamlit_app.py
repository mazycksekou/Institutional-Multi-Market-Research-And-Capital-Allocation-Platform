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


st.title("Betting Model Operator Dashboard")
st.caption("Paper/testing control room. This screen does not place real bets.")

settings = sidebar_inputs()
show_easy_dictionary()

menu = st.sidebar.radio(
    "Main Menu",
    [
        "Feature Ablation Lab",
        "Test One Sport",
        "Test All Sports",
        "Bankroll Settings",
        "Instructions",
    ],
)


if menu == "Operator Summary":
    st.header("Operator Summary")

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

        # Numeric‑safe copy for charts, Arrow‑safe copy for display
        numeric_table = pd.DataFrame(rows)
        table = df(rows)
        filtered = table.copy()
        if sport_filter != "All" and "sport" in numeric_table.columns:
            filtered = table[table["sport"].astype(str) == sport_filter]
        if market_filter != "All" and "market" in numeric_table.columns:
            filtered = table[table["market"].astype(str) == market_filter]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            if "sport" in numeric_table.columns:
                st.subheader("Paper bets by sport")
                st.bar_chart(numeric_table["sport"].fillna("UNKNOWN").astype(str).value_counts())
        with c2:
            if "market" in numeric_table.columns:
                st.subheader("Paper bets by bet type")
                st.bar_chart(numeric_table["market"].fillna("UNKNOWN").astype(str).value_counts())

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

        # ── Volatility Result Breakdown (if backtest result available) ────
        if isinstance(dashboard, dict):
            st.subheader("Volatility Result Breakdown")
            st.info("This shows whether low, medium, high, or unknown volatility produced better results.")
            default_sqlite = get_default_historical_sqlite_path()
            vol_breakdown = get_volatility_result_breakdown_for_dashboard(
                default_sqlite, projection_result=dashboard
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

    st.info(
        "Importable now: **Football‑Data CSV** (`football_data_uk`), "
        "**MLB JSON** (`arnav_mlb_odds_scraper`), "
        "**SBR‑style CSV/JSON** (`sportsbookreview_scraper`)."
    )


elif menu == "Import Historical Data":
    st.header("Import Historical Odds Data")

    import_source_options = get_historical_import_source_options()
    selected_source_key = st.selectbox(
        "Select an approved data source",
        options=[opt["source_key"] for opt in import_source_options],
        format_func=lambda k: next(
            (opt["source"] for opt in import_source_options if opt["source_key"] == k),
            k,
        ),
    )

    default_sqlite = get_default_historical_sqlite_path()
    db_path_input = st.text_input(
        "SQLite database path",
        value=default_sqlite,
        help="Path where the historical‑odds SQLite file lives or will be created.",
    )

    upload_col, local_col = st.columns(2)

    uploaded_file = upload_col.file_uploader(
        "Upload a CSV or JSON file",
        type=["csv", "json"],
        help=(
            "Choose a local file from your machine. "
            "No downloads or scraping happen here. You choose the local file."
        ),
    )

    local_path_input = local_col.text_input(
        "Or type an absolute path to a file already on the server",
        value="",
        placeholder="/absolute/path/to/file.csv",
    )

    if st.button("Import now", type="primary"):
        file_path = None
        source_file = None

        if uploaded_file is not None:
            # Save uploaded content to runtime directory
            content = uploaded_file.getvalue()
            filename = uploaded_file.name or "uploaded"
            save_result = save_historical_upload_for_import(
                selected_source_key, filename, content
            )
            file_path = save_result["path"]
            source_file = f"upload:{save_result['filename']}"
            st.success(f"Saved upload to {file_path}")
        elif local_path_input.strip():
            file_path = local_path_input.strip()
            source_file = local_path_input.strip()
        else:
            st.error("Provide a file either via upload or by typing a server path.")
            file_path = None

        if file_path:
            with st.spinner("Importing into SQLite..."):
                import_result = import_historical_file_to_sqlite_for_dashboard(
                    db_path_input,
                    selected_source_key,
                    file_path,
                    source_file=source_file,
                )
            st.json(import_result)
            if import_result.get("ok"):
                st.success(
                    f"✅ Imported {import_result['rows_inserted']} rows. "
                    f"Rejected {import_result['rows_rejected']} rows."
                )
            else:
                st.warning(
                    f"⚠️ Some rows were rejected ({import_result['rows_rejected']}). "
                    "Check the raw result above."
                )
    st.caption("No downloads or scraping happen here. You choose the local file.")


elif menu == "Data Quality Check":
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


elif menu == "Model Projection":
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

elif menu == "Feature Ablation Lab":
    st.header("Feature Ablation Lab")
    st.info("Feature Ablation Lab starts with all safe available fields, then lets operators remove fields to test what actually improves model performance.")
    st.info("Use the synthetic sandbox only for fake demo rows. Synthetic rows are not model evidence.")
    st.markdown("Test One Sport and Test All Sports are paper backtest/test flows, not real bets.")

    mode = st.radio("Mode", ["Single Sport", "All Sports"], key="fal_mode")
    default_sqlite = get_default_historical_sqlite_path()
    db_path_input = st.text_input("SQLite database path", value=default_sqlite, key="fal_db")

    sport_val = ""
    market_val = ""
    if mode == "Single Sport":
        sport_options = [item for item in get_available_profile_options() if item["value"] != "all_sports"]
        sport_labels = [item["label"] for item in sport_options]
        selected_label = st.selectbox("Sport", sport_labels, key="fal_sport")
        sport_val = next(item["value"] for item in sport_options if item["label"] == selected_label)
        market_val = st.text_input("Market filter (optional)", key="fal_market")

    initial_groups = get_ablation_field_groups_for_sport(sport_val, market_val)
    available_groups = [g["group_key"] for g in initial_groups.get("groups", [])]

    selected_groups = st.multiselect("Field Groups", options=available_groups, default=available_groups, key="fal_groups")
    all_selectable = initial_groups.get("all_selectable_fields", [])
    active_fields = st.multiselect("Active Fields", options=all_selectable, default=all_selectable, key="fal_active")
    removed_fields = st.multiselect("Removed Fields", options=all_selectable, default=[], key="fal_removed")
    st.caption("Never‑feature/leakage fields are excluded by the backend and not shown.")

    if st.button("Run Ablation Lab", type="primary", key="fal_run"):
        with st.spinner("Running feature ablation..."):
            snap = get_feature_ablation_lab_snapshot_for_dashboard(
                db_path_input,
                sport=sport_val or None,
                market=market_val or None,
                mode="all_sports" if mode == "All Sports" else "single_sport",
                selected_fields=active_fields if active_fields != all_selectable else None,
                removed_fields=removed_fields or None,
                selected_groups=selected_groups if selected_groups != available_groups else None,
            )
            st.session_state["_last_ablation_result"] = snap

        if not snap.get("ok"):
            st.error("Feature Ablation Lab failed.")
            for w in snap.get("warnings", []):
                st.warning(w)
            st.json(snap)
        else:
            # ── KPI cards ──────────────────────────────────────────
            perf = snap.get("performance", {}) or {}
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Decisions", perf.get("decisions", 0))
                st.metric("Net Return", perf.get("net_result", 0.0))
            with col_b:
                st.metric("ROI %", perf.get("roi_percent", 0.0))
                st.metric("Win Rate %", perf.get("win_rate_percent", 0.0))
            with col_c:
                st.metric("Avg Edge", snap.get("avg_edge", "N/A"))
                st.metric("Max Drawdown %", perf.get("max_drawdown_percent", "N/A"))
            with col_d:
                st.metric("Ready Status", "✅" if perf.get("ready", False) else "❌")
                st.metric("Sports", len(snap.get("included_sports", [])))

            # ── Plain‑English summary ──────────────────────────────
            included_sport_count = len(snap.get("included_sports", []))
            decisions = perf.get("decisions", 0)
            roi = perf.get("roi_percent", 0.0)
            summary_text = (
                f"Ablation tested {included_sport_count} sport(s) "
                f"with {decisions} decisions and ROI {roi:.2f}%. "
                f"Baseline comparison will appear after you save a baseline run "
                f"via Experiment History."
            )
            st.info(summary_text)

            # ── Field counts in expander ───────────────────────────
            active_count = len(snap.get("active_fields", []))
            removed_count = len(snap.get("removed_fields", []))
            with st.expander("Field Changes", expanded=False):
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    st.metric("Active Fields", active_count)
                with col_f2:
                    st.metric("Fields Added", max(0, active_count - removed_count))
                with col_f3:
                    st.metric("Fields Removed", removed_count)
                if active_count:
                    st.write("Active:", ", ".join(snap["active_fields"]))
                if removed_count:
                    st.write("Removed:", ", ".join(snap["removed_fields"]))

            # ── Tabs for detailed view ─────────────────────────────
            tab_sum, tab_fld, tab_cur, tab_cmp, tab_raw = st.tabs(
                ["Summary", "Field Impact", "Performance Curves",
                 "Comparison", "Raw Data"]
            )

            with tab_sum:
                st.subheader("Included Sports")
                inc = snap.get("included_sports", [])
                if inc:
                    st.write(", ".join(inc))
                else:
                    st.info("None")

                st.subheader("Excluded Sports")
                exc = snap.get("excluded_sports", [])
                if exc:
                    for e in exc:
                        st.error(
                            f"{e.get('sport_key','?')} – {e.get('reason','not ready')}"
                        )
                else:
                    st.info("None")

                st.subheader("Overall Performance")
                if perf:
                    metric_row(
                        [
                            ("Total rows", perf.get("total_rows", 0), ""),
                            ("Eligible rows", perf.get("eligible_rows", 0), ""),
                            ("Skipped rows", perf.get("skipped_rows", 0), ""),
                            ("Decisions", perf.get("decisions", 0), ""),
                            ("Skipped decisions", perf.get("skipped_decisions", 0), ""),
                            ("Settled count", perf.get("settled_count", 0), ""),
                            ("Wins", perf.get("wins", 0), ""),
                            ("Losses", perf.get("losses", 0), ""),
                            ("Pushes", perf.get("pushes", 0), ""),
                            ("Net result", perf.get("net_result", 0.0), ""),
                            ("ROI %", perf.get("roi_percent", 0.0), ""),
                            ("Win rate %", perf.get("win_rate_percent", 0.0), ""),
                        ]
                    )

                st.subheader("ROI by Sport")
                roi_sport = snap.get("roi_by_sport", {})
                if roi_sport:
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
                    st.dataframe(
                        df(roi_rows), use_container_width=True, hide_index=True
                    )
                else:
                    st.info("No ROI data.")

                for w in snap.get("warnings", []):
                    st.warning(w)

            with tab_fld:
                st.subheader("Active Fields")
                st.write(", ".join(snap.get("active_fields", [])))
                st.subheader("Removed Fields")
                st.write(", ".join(snap.get("removed_fields", [])))

            with tab_cur:
                curve_rows = snap.get("bankroll_curve", [])
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
                st.json(snap)

    with st.expander("Raw snapshot JSON", expanded=False):
        st.json({})

    # ── Collapsed sub‑sections for Phase 10H23B ──────
    with st.expander("Readiness Filter", expanded=False):
        st.subheader("Calibration‑Ready Strategy Filter")
        st.info("Calibration‑Ready Strategy Filter excludes sports and markets without enough data before calculating ROI.")
        st.markdown("Interactive controls may be re‑enabled in a future phase. For now, this section provides an overview.")

    with st.expander("Synthetic Line Movement Sandbox", expanded=False):
        st.info("Synthetic Line Movement Sandbox uses fake demo rows to preview the line movement pipeline without writing production data.")
        st.warning("Synthetic rows are fake demo data and must not be used as model evidence.")

    with st.expander("Line Movement Data Quality Check", expanded=False):
        st.info("Line Movement Data Quality Dashboard shows coverage, missing links, duplicate snapshots, sports, markets, books, and readiness before any real connector is added.")

    with st.expander("Saved Runs / Reports", expanded=False):
        st.subheader("Experiment History / Report Export")
        st.info("Calibration Report Export creates a Markdown review pack from a saved ablation or calibration run.")

elif menu == "Calibration‑Ready Strategy Filter":
    st.header("Calibration‑Ready Strategy Filter")
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


elif menu == "Experiment History":
    st.header("Experiment History")
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

# Experiment History saves ablation and calibration runs so operators can compare field changes, sport readiness, and ROI over time.

# Calibration Report Export creates a Markdown review pack from a saved ablation or calibration run.

# Historical Line Movement Readiness checks whether the local SQLite store is ready for time-series line movement data before any vendor connector is added.

# Vendor-Neutral Line Movement Import Contract defines the standard row shape future line movement sources must provide before any real connector is added.

# Vendor‑Neutral Line Movement Import Contract defines the standard row shape future line movement sources must provide before any real connector is added.

# Source Event Link Resolver maps future source rows to canonical event_id values before line movement features are used.

# As‑Of Line Movement Query Engine filters historical snapshots to only those available at or before a hypothetical bet time.

# Line Movement Data Quality Dashboard shows coverage, missing links, duplicate snapshots, sports, markets, books, and readiness before any real connector is added.

# STOP: Review this dashboard before adding any vendor, API, scraper, or paid data connector.
