import os
import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FundForge AI Terminal",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PREDICTION_FILE = os.path.join(
    BASE_DIR,
    "predictions",
    "MUFAP",
    "MUFAP_NAV_PREDICTIONS.csv"
)

HORIZONS = [
    "15D",
    "30D",
    "90D",
    "180D",
    "270D",
    "365D",
    "730D",
    "1095D"
]

TICKER_HORIZON = "30D"


# ============================================================
# CUSTOM CSS — DARK TERMINAL THEME
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0b0f1a;
    }

    /* -------------------------------------------------- */
    /* TITLE                                                */
    /* -------------------------------------------------- */

    .brand-row {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 4px;
    }

    .brand-icon {
        font-size: 40px;
    }

    .main-title {
        font-size: 44px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .subtitle {
        font-size: 16px;
        color: #94a3b8;
        margin-bottom: 22px;
        margin-top: 2px;
    }

    /* -------------------------------------------------- */
    /* ROTATING AMC TICKER                                  */
    /* -------------------------------------------------- */

    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: #10152599;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px 0;
        margin-bottom: 26px;
    }

    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        animation: ticker-scroll 30s linear infinite;
    }

    .ticker-wrap:hover .ticker-move {
        animation-play-state: paused;
    }

    .ticker-item {
        display: inline-block;
        padding: 0 28px;
        font-size: 15px;
        font-weight: 600;
        color: #e2e8f0;
    }

    .ticker-amc {
        opacity: 0.65;
        font-weight: 500;
        margin-right: 6px;
    }

    .ticker-fund {
        margin-right: 6px;
    }

    .ticker-up {
        color: #22c55e;
    }

    .ticker-down {
        color: #ef4444;
    }

    @keyframes ticker-scroll {
        0%   { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }

    /* -------------------------------------------------- */
    /* SECTION LABELS                                       */
    /* -------------------------------------------------- */

    .section-label {
        text-align: center;
        color: #94a3b8;
        letter-spacing: 2px;
        font-size: 14px;
        font-weight: 700;
        margin: 26px 0 14px 0;
        text-transform: uppercase;
    }

    /* -------------------------------------------------- */
    /* PILL BUTTONS (AMC / FUND / HORIZON selectors)        */
    /* -------------------------------------------------- */

    div[data-testid="stButton"] button {
        border-radius: 999px !important;
        padding: 14px 10px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        width: 100%;
        transition: all 0.15s ease-in-out;
    }

    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #131a2b !important;
        border: 1px solid #27324a !important;
        color: #cbd5e1 !important;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6, #22d3ee) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.45);
    }

    /* -------------------------------------------------- */
    /* CTA BUTTON                                            */
    /* -------------------------------------------------- */

    .cta-wrap {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 10px;
    }

    /* -------------------------------------------------- */
    /* BREADCRUMB / BACK LINK                                */
    /* -------------------------------------------------- */

    .crumb {
        color: #64748b;
        font-size: 14px;
        margin-bottom: 6px;
    }

    .metric-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(148,163,184,0.2);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_predictions():

    if not os.path.exists(PREDICTION_FILE):

        return None

    df = pd.read_csv(
        PREDICTION_FILE
    )

    return df


df = load_predictions()


# ============================================================
# CHECK FILE
# ============================================================

if df is None:

    st.error(
        f"Prediction file not found:\n\n"
        f"{PREDICTION_FILE}"
    )

    st.stop()


if df.empty:

    st.error(
        "Prediction file is empty."
    )

    st.stop()


# ============================================================
# COMMON DATA CLEANING
# ============================================================

if "Latest_Date" in df.columns:

    df["Latest_Date"] = pd.to_datetime(
        df["Latest_Date"],
        errors="coerce"
    )


if "Current_NAV" in df.columns:

    df["Current_NAV"] = pd.to_numeric(
        df["Current_NAV"],
        errors="coerce"
    )


for horizon in HORIZONS:

    prediction_column = (
        f"Predicted_NAV_{horizon}"
    )

    change_column = (
        f"Change_NAV_{horizon}_Percent"
    )

    if prediction_column in df.columns:

        df[prediction_column] = pd.to_numeric(
            df[prediction_column],
            errors="coerce"
        )

    if change_column in df.columns:

        df[change_column] = pd.to_numeric(
            df[change_column],
            errors="coerce"
        )


if "AMC" in df.columns:

    df["AMC"] = df["AMC"].astype(str).str.strip()


# ============================================================
# SESSION STATE
# ============================================================

if "selected_amc" not in st.session_state:
    st.session_state.selected_amc = None

if "selected_fund" not in st.session_state:
    st.session_state.selected_fund = None

if "selected_fund_id" not in st.session_state:
    st.session_state.selected_fund_id = None


def pick_amc(amc_name):
    st.session_state.selected_amc = amc_name
    st.session_state.selected_fund = None
    st.session_state.selected_fund_id = None


def pick_fund(fund_name, fund_id):
    st.session_state.selected_fund = fund_name
    st.session_state.selected_fund_id = fund_id


def clear_amc():
    st.session_state.selected_amc = None
    st.session_state.selected_fund = None
    st.session_state.selected_fund_id = None


def clear_fund():
    st.session_state.selected_fund = None
    st.session_state.selected_fund_id = None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="brand-row">'
    '<div class="brand-icon">📈</div>'
    '<div class="main-title">FundForge AI Terminal</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered MUFAP Mutual Fund NAV Prediction Dashboard'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# ROTATING TOP BAR — BEST FUND PER AMC (30D PROFIT)
# ============================================================

def render_amc_ticker(data):

    change_column = f"Change_NAV_{TICKER_HORIZON}_Percent"

    if "AMC" not in data.columns or change_column not in data.columns:
        return

    best_rows = []

    for amc_name, group in data.groupby("AMC"):

        group_valid = group.dropna(subset=[change_column])

        if group_valid.empty:
            continue

        best = group_valid.loc[
            group_valid[change_column].idxmax()
        ]

        best_rows.append(best)

    if not best_rows:
        return

    best_df = pd.DataFrame(best_rows).sort_values(
        change_column, ascending=False
    )

    items_html = ""

    for _, row in best_df.iterrows():

        change_value = row[change_column]

        css_class = "ticker-up" if change_value >= 0 else "ticker-down"

        arrow = "▲" if change_value >= 0 else "▼"

        fund_name = str(row.get("Fund", "N/A"))

        items_html += (
            f'<span class="ticker-item">'
            f'<span class="ticker-amc">{row["AMC"]}:</span>'
            f'<span class="ticker-fund">{fund_name}</span>'
            f'<span class="{css_class}">{arrow} {change_value:+.2f}%</span>'
            f'</span>'
        )

    ticker_html = (
        f'<div class="ticker-wrap">'
        f'<div class="ticker-move">{items_html}{items_html}</div>'
        f'</div>'
    )

    st.markdown(ticker_html, unsafe_allow_html=True)


render_amc_ticker(df)


# ============================================================
# CTA BUTTON
# ============================================================

st.markdown('<div class="cta-wrap">', unsafe_allow_html=True)

cta_col1, cta_col2 = st.columns([3, 1])

with cta_col2:

    if st.button(
        "🚀 LAUNCH FUND EXPLORER",
        type="primary",
        use_container_width=True
    ):
        clear_amc()

st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR (SECONDARY PAGES)
# ============================================================

st.sidebar.title("FundForge")

st.sidebar.markdown("### Navigation")

page = st.sidebar.radio(
    "Select",
    [
        "Fund Explorer",
        "Dashboard",
        "Market Rankings",
        "Prediction Table"
    ]
)

if page != "Fund Explorer":
    clear_amc()


# ============================================================
# FUND EXPLORER  (SELECT COMPANY -> SELECT FUND -> RESULTS)
# ============================================================

if page == "Fund Explorer":

    if "AMC" not in df.columns:

        st.error(
            "This dataset does not contain an 'AMC' column."
        )

        st.stop()

    amc_list = sorted(
        df["AMC"].dropna().astype(str).unique().tolist()
    )

    # --------------------------------------------------------
    # STEP 1 — SELECT COMPANY
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-label">Select Company</div>',
        unsafe_allow_html=True
    )

    amc_cols = st.columns(4)

    for index, amc_name in enumerate(amc_list):

        with amc_cols[index % 4]:

            is_selected = (
                st.session_state.selected_amc == amc_name
            )

            if st.button(
                amc_name,
                key=f"amc_{amc_name}",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                pick_amc(amc_name)
                st.rerun()

    # --------------------------------------------------------
    # STEP 2 — SELECT FUND (only after AMC picked)
    # --------------------------------------------------------

    if st.session_state.selected_amc:

        amc_df = df[
            df["AMC"] == st.session_state.selected_amc
        ].copy()

        st.markdown(
            f'<div class="crumb">Company: '
            f'<b>{st.session_state.selected_amc}</b></div>',
            unsafe_allow_html=True
        )

        if st.button("← Back to Companies"):
            clear_amc()
            st.rerun()

        st.markdown(
            '<div class="section-label">Select Fund</div>',
            unsafe_allow_html=True
        )

        if amc_df.empty:

            st.warning("No funds available for this AMC.")

            st.stop()

        fund_options = (
            amc_df[["Fund", "FundID"]]
            .dropna(subset=["Fund"])
            .astype(str)
            .drop_duplicates()
            .sort_values("Fund")
        )

        fund_cols = st.columns(3)

        for index, row in enumerate(fund_options.itertuples(index=False)):

            fund_name = row.Fund
            fund_id = row.FundID

            with fund_cols[index % 3]:

                is_selected = (
                    st.session_state.selected_fund == fund_name
                    and st.session_state.selected_fund_id == fund_id
                )

                if st.button(
                    fund_name,
                    key=f"fund_{fund_id}_{index}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True
                ):
                    pick_fund(fund_name, fund_id)
                    st.rerun()

        # ----------------------------------------------------
        # STEP 3 — FUND RESULTS (only after fund picked)
        # ----------------------------------------------------

        if st.session_state.selected_fund:

            fund_data = amc_df[
                (amc_df["Fund"].astype(str) == st.session_state.selected_fund)
                & (amc_df["FundID"].astype(str) == str(st.session_state.selected_fund_id))
            ]

            if fund_data.empty:

                st.warning("No prediction data available.")

                st.stop()

            selected = fund_data.iloc[0]

            st.markdown(
                f'<div class="crumb">Fund: '
                f'<b>{st.session_state.selected_fund}</b></div>',
                unsafe_allow_html=True
            )

            if st.button("← Back to Funds"):
                clear_fund()
                st.rerun()

            st.divider()

            st.subheader(selected.get("Fund", "Fund"))

            if pd.notna(selected.get("Category")):

                st.caption(
                    f"AMC: {st.session_state.selected_amc}  •  "
                    f"Category: {selected['Category']}"
                )

            else:

                st.caption(f"AMC: {st.session_state.selected_amc}")

            current_nav = selected["Current_NAV"]

            st.metric("Current NAV", f"{current_nav:.6f}")

            st.divider()

            # ------------------------------------------------
            # PREDICTION CARDS
            # ------------------------------------------------

            st.subheader("NAV Forecast")

            columns = st.columns(4)

            for index, horizon in enumerate(HORIZONS):

                prediction_column = f"Predicted_NAV_{horizon}"
                change_column = f"Change_NAV_{horizon}_Percent"
                method_column = f"Prediction_Method_NAV_{horizon}"

                prediction = selected.get(prediction_column)
                change = selected.get(change_column)
                method = selected.get(method_column, "Model")

                with columns[index % 4]:

                    st.metric(
                        f"{horizon} Forecast",
                        (
                            f"{prediction:.6f}"
                            if pd.notna(prediction)
                            else "N/A"
                        ),
                        (
                            f"{change:+.2f}%"
                            if pd.notna(change)
                            else None
                        )
                    )

                    if pd.notna(prediction):

                        st.caption(f"Method: {method}")

            st.divider()

            # ------------------------------------------------
            # FORECAST CHART
            # ------------------------------------------------

            st.subheader("NAV Forecast Curve")

            chart_data = {
                "Horizon": ["Current"],
                "NAV": [current_nav]
            }

            for horizon in HORIZONS:

                prediction_column = f"Predicted_NAV_{horizon}"

                prediction = selected.get(prediction_column)

                if pd.notna(prediction):

                    chart_data["Horizon"].append(horizon)
                    chart_data["NAV"].append(prediction)

            chart_df = pd.DataFrame(chart_data).set_index("Horizon")

            st.line_chart(chart_df)

            # ------------------------------------------------
            # DETAILED TABLE
            # ------------------------------------------------

            st.subheader("Detailed Forecast")

            details = []

            for horizon in HORIZONS:

                prediction = selected.get(f"Predicted_NAV_{horizon}")
                change = selected.get(f"Change_NAV_{horizon}_Percent")
                method = selected.get(f"Prediction_Method_NAV_{horizon}", "")
                status = selected.get(f"Prediction_Status_NAV_{horizon}", "")

                details.append({
                    "Horizon": horizon,
                    "Predicted NAV": prediction,
                    "Change %": change,
                    "Method": method,
                    "Status": status
                })

            details_df = pd.DataFrame(details)

            st.dataframe(
                details_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# DASHBOARD
# ============================================================

elif page == "Dashboard":

    st.header("FundForge Dashboard")

    total_funds = len(df)

    total_amcs = df["AMC"].nunique() if "AMC" in df.columns else 0

    valid_predictions = 0

    for horizon in HORIZONS:

        column = f"Predicted_NAV_{horizon}"

        if column in df.columns:

            valid_predictions += df[column].notna().sum()

    total_possible = total_funds * len(HORIZONS)

    coverage = (
        valid_predictions / total_possible * 100
        if total_possible > 0
        else 0
    )

    latest_date = None

    if "Latest_Date" in df.columns:

        latest_date = df["Latest_Date"].max()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Funds", f"{total_funds:,}")

    with col2:
        st.metric("AMCs", f"{total_amcs}")

    with col3:
        st.metric("Prediction Horizons", len(HORIZONS))

    with col4:
        st.metric("Total Predictions", f"{valid_predictions:,}")

    with col5:
        st.metric("Prediction Coverage", f"{coverage:.1f}%")

    if latest_date is not None:

        st.caption(f"Latest dataset date: {latest_date.strftime('%Y-%m-%d')}")

    st.divider()

    st.subheader(f"🏅 Best Performing Fund per AMC — {TICKER_HORIZON} Outlook")

    change_column = f"Change_NAV_{TICKER_HORIZON}_Percent"
    prediction_column = f"Predicted_NAV_{TICKER_HORIZON}"

    if "AMC" in df.columns and change_column in df.columns:

        best_rows = []

        for amc_name, group in df.groupby("AMC"):

            group_valid = group.dropna(subset=[change_column])

            if group_valid.empty:
                continue

            best = group_valid.loc[group_valid[change_column].idxmax()]

            best_rows.append({
                "AMC": amc_name,
                "Best Fund": best.get("Fund", "N/A"),
                "Current NAV": best.get("Current_NAV"),
                "Predicted NAV": best.get(prediction_column),
                "Predicted Change %": best.get(change_column)
            })

        best_df = pd.DataFrame(best_rows).sort_values(
            "Predicted Change %", ascending=False
        )

        display_best = best_df.copy()

        display_best["Predicted Change %"] = display_best[
            "Predicted Change %"
        ].map(lambda x: f"{x:+.2f}%")

        st.dataframe(display_best, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Prediction Overview")

    summary_rows = []

    for horizon in HORIZONS:

        change_column = f"Change_NAV_{horizon}_Percent"
        prediction_column = f"Predicted_NAV_{horizon}"

        if change_column not in df.columns:
            continue

        changes = df[change_column].dropna()

        if len(changes) == 0:
            continue

        summary_rows.append({
            "Horizon": horizon,
            "Average Change": changes.mean(),
            "Minimum Change": changes.min(),
            "Maximum Change": changes.max(),
            "Predictions": df[prediction_column].notna().sum()
        })

    summary_df = pd.DataFrame(summary_rows)

    if not summary_df.empty:

        display_df = summary_df.copy()

        for column in ["Average Change", "Minimum Change", "Maximum Change"]:

            display_df[column] = display_df[column].map(
                lambda x: f"{x:.2f}%"
            )

        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ============================================================
# MARKET RANKINGS
# ============================================================

elif page == "Market Rankings":

    st.header("🏆 Fund Rankings")

    horizon = st.selectbox("Prediction Horizon", HORIZONS)

    change_column = f"Change_NAV_{horizon}_Percent"
    prediction_column = f"Predicted_NAV_{horizon}"

    ranking_columns = [
        "AMC", "Fund", "FundID", "Current_NAV",
        prediction_column, change_column
    ]

    ranking_columns = [
        column for column in ranking_columns if column in df.columns
    ]

    ranking_df = df[ranking_columns].copy()

    st.subheader(f"🚀 Top Predicted Gainers — {horizon}")

    top_gainers = ranking_df.sort_values(
        change_column, ascending=False
    ).head(10)

    st.dataframe(top_gainers, use_container_width=True, hide_index=True)

    st.subheader(f"📉 Top Predicted Decliners — {horizon}")

    top_losers = ranking_df.sort_values(
        change_column, ascending=True
    ).head(10)

    st.dataframe(top_losers, use_container_width=True, hide_index=True)


# ============================================================
# PREDICTION TABLE
# ============================================================

elif page == "Prediction Table":

    st.header("📊 Complete Prediction Table")

    search = st.text_input("Search fund")

    filtered_df = df.copy()

    if search:

        filtered_df = filtered_df[
            filtered_df["Fund"].astype(str).str.contains(
                search, case=False, na=False
            )
        ]

    if "AMC" in filtered_df.columns:

        amc_options = sorted(
            filtered_df["AMC"].dropna().astype(str).unique().tolist()
        )

        selected_amcs = st.multiselect(
            "Filter by AMC", amc_options, default=amc_options
        )

        filtered_df = filtered_df[filtered_df["AMC"].isin(selected_amcs)]

    selected_horizons = st.multiselect(
        "Select Horizons", HORIZONS, default=HORIZONS
    )

    columns = ["AMC", "FundID", "Fund", "Category", "Latest_Date", "Current_NAV"]

    for horizon in selected_horizons:

        columns.extend([
            f"Predicted_NAV_{horizon}",
            f"Change_NAV_{horizon}_Percent",
            f"Prediction_Method_NAV_{horizon}"
        ])

    columns = [column for column in columns if column in filtered_df.columns]

    st.dataframe(
        filtered_df[columns],
        use_container_width=True,
        height=600,
        hide_index=True
    )

    csv = filtered_df[columns].to_csv(index=False)

    st.download_button(
        label="⬇️ Download Filtered Predictions",
        data=csv,
        file_name="FundForge_NAV_Predictions.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption("FundForge | MUFAP NAV Prediction")

st.sidebar.caption(
    "Existing trained models • No retraining performed by dashboard"
)
