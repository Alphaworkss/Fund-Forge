import os
import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FundForge - MUFAP NAV",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# CONFIGURATION
# ============================================================

PREDICTION_FILE = os.path.join(
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


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 30px;
    }

    .metric-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
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
# PAGE HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📈 FundForge</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered MUFAP Mutual Fund NAV Prediction Dashboard'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("FundForge")

st.sidebar.markdown(
    "### Navigation"
)

page = st.sidebar.radio(
    "Select",
    [
        "Dashboard",
        "Fund Prediction",
        "Market Rankings",
        "Prediction Table"
    ]
)


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


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.header("FundForge Dashboard")

    # --------------------------------------------------------
    # KPI METRICS
    # --------------------------------------------------------

    total_funds = len(df)

    valid_predictions = 0

    for horizon in HORIZONS:

        column = (
            f"Predicted_NAV_{horizon}"
        )

        if column in df.columns:

            valid_predictions += (
                df[column].notna().sum()
            )

    total_possible = (
        total_funds * len(HORIZONS)
    )

    coverage = (
        valid_predictions / total_possible * 100
        if total_possible > 0
        else 0
    )

    latest_date = None

    if "Latest_Date" in df.columns:

        latest_date = df[
            "Latest_Date"
        ].max()


    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Funds",
            f"{total_funds:,}"
        )

    with col2:

        st.metric(
            "Prediction Horizons",
            len(HORIZONS)
        )

    with col3:

        st.metric(
            "Total Predictions",
            f"{valid_predictions:,}"
        )

    with col4:

        st.metric(
            "Prediction Coverage",
            f"{coverage:.1f}%"
        )


    if latest_date is not None:

        st.caption(
            f"Latest dataset date: "
            f"{latest_date.strftime('%Y-%m-%d')}"
        )


    st.divider()


    # --------------------------------------------------------
    # HORIZON SUMMARY
    # --------------------------------------------------------

    st.subheader(
        "Prediction Overview"
    )

    summary_rows = []

    for horizon in HORIZONS:

        change_column = (
            f"Change_NAV_{horizon}_Percent"
        )

        prediction_column = (
            f"Predicted_NAV_{horizon}"
        )

        if change_column not in df.columns:

            continue

        changes = df[
            change_column
        ].dropna()

        if len(changes) == 0:

            continue

        summary_rows.append({

            "Horizon":
                horizon,

            "Average Change":
                changes.mean(),

            "Minimum Change":
                changes.min(),

            "Maximum Change":
                changes.max(),

            "Predictions":
                df[
                    prediction_column
                ].notna().sum()
        })


    summary_df = pd.DataFrame(
        summary_rows
    )


    if not summary_df.empty:

        display_df = summary_df.copy()

        display_df[
            "Average Change"
        ] = display_df[
            "Average Change"
        ].map(
            lambda x: f"{x:.2f}%"
        )

        display_df[
            "Minimum Change"
        ] = display_df[
            "Minimum Change"
        ].map(
            lambda x: f"{x:.2f}%"
        )

        display_df[
            "Maximum Change"
        ] = display_df[
            "Maximum Change"
        ].map(
            lambda x: f"{x:.2f}%"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# FUND PREDICTION
# ============================================================

elif page == "Fund Prediction":

    st.header(
        "🔎 Fund Prediction"
    )

    fund_names = sorted(
        df["Fund"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_fund = st.selectbox(
        "Select Fund",
        fund_names
    )


    fund_data = df[
        df["Fund"].astype(str)
        == selected_fund
    ].copy()


    if fund_data.empty:

        st.warning(
            "No prediction data available."
        )

        st.stop()


    # --------------------------------------------------------
    # HANDLE DUPLICATE FUND NAMES
    # --------------------------------------------------------

    if len(fund_data) > 1:

        st.info(
            "Multiple FundIDs exist for this fund name. "
            "Select the required FundID below."
        )

        fund_id = st.selectbox(
            "FundID",
            fund_data[
                "FundID"
            ].astype(str).tolist()
        )

        selected = fund_data[
            fund_data["FundID"].astype(str)
            == fund_id
        ].iloc[0]

    else:

        selected = fund_data.iloc[0]


    # --------------------------------------------------------
    # FUND INFORMATION
    # --------------------------------------------------------

    st.subheader(
        selected.get(
            "Fund",
            "Fund"
        )
    )

    if pd.notna(
        selected.get("Category")
    ):

        st.caption(
            f"Category: "
            f"{selected['Category']}"
        )


    current_nav = selected[
        "Current_NAV"
    ]


    st.metric(
        "Current NAV",
        f"{current_nav:.6f}"
    )


    st.divider()


    # --------------------------------------------------------
    # PREDICTION CARDS
    # --------------------------------------------------------

    st.subheader(
        "NAV Forecast"
    )

    columns = st.columns(4)


    for index, horizon in enumerate(
        HORIZONS
    ):

        prediction_column = (
            f"Predicted_NAV_{horizon}"
        )

        change_column = (
            f"Change_NAV_{horizon}_Percent"
        )

        method_column = (
            f"Prediction_Method_NAV_{horizon}"
        )

        prediction = selected.get(
            prediction_column
        )

        change = selected.get(
            change_column
        )

        method = selected.get(
            method_column,
            "Model"
        )


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

            if pd.notna(
                prediction
            ):

                st.caption(
                    f"Method: {method}"
                )


    st.divider()


    # --------------------------------------------------------
    # FORECAST CHART
    # --------------------------------------------------------

    st.subheader(
        "NAV Forecast Curve"
    )

    chart_data = {

        "Horizon": ["Current"],

        "NAV": [current_nav]
    }


    for horizon in HORIZONS:

        prediction_column = (
            f"Predicted_NAV_{horizon}"
        )

        prediction = selected.get(
            prediction_column
        )

        if pd.notna(
            prediction
        ):

            chart_data[
                "Horizon"
            ].append(horizon)

            chart_data[
                "NAV"
            ].append(prediction)


    chart_df = pd.DataFrame(
        chart_data
    ).set_index(
        "Horizon"
    )


    st.line_chart(
        chart_df
    )


    # --------------------------------------------------------
    # DETAILED TABLE
    # --------------------------------------------------------

    st.subheader(
        "Detailed Forecast"
    )

    details = []

    for horizon in HORIZONS:

        prediction = selected.get(
            f"Predicted_NAV_{horizon}"
        )

        change = selected.get(
            f"Change_NAV_{horizon}_Percent"
        )

        method = selected.get(
            f"Prediction_Method_NAV_{horizon}",
            ""
        )

        status = selected.get(
            f"Prediction_Status_NAV_{horizon}",
            ""
        )

        details.append({

            "Horizon":
                horizon,

            "Predicted NAV":
                prediction,

            "Change %":
                change,

            "Method":
                method,

            "Status":
                status
        })


    details_df = pd.DataFrame(
        details
    )


    st.dataframe(
        details_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# MARKET RANKINGS
# ============================================================

elif page == "Market Rankings":

    st.header(
        "🏆 Fund Rankings"
    )


    horizon = st.selectbox(
        "Prediction Horizon",
        HORIZONS
    )


    change_column = (
        f"Change_NAV_{horizon}_Percent"
    )


    prediction_column = (
        f"Predicted_NAV_{horizon}"
    )


    ranking_columns = [

        "Fund",

        "FundID",

        "Current_NAV",

        prediction_column,

        change_column
    ]


    ranking_columns = [

        column

        for column in ranking_columns

        if column in df.columns
    ]


    ranking_df = df[
        ranking_columns
    ].copy()


    # --------------------------------------------------------
    # TOP GAINERS
    # --------------------------------------------------------

    st.subheader(
        f"🚀 Top Predicted Gainers — {horizon}"
    )


    top_gainers = (
        ranking_df
        .sort_values(
            change_column,
            ascending=False
        )
        .head(10)
    )


    st.dataframe(
        top_gainers,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------------
    # TOP LOSERS
    # --------------------------------------------------------

    st.subheader(
        f"📉 Top Predicted Decliners — {horizon}"
    )


    top_losers = (
        ranking_df
        .sort_values(
            change_column,
            ascending=True
        )
        .head(10)
    )


    st.dataframe(
        top_losers,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PREDICTION TABLE
# ============================================================

elif page == "Prediction Table":

    st.header(
        "📊 Complete Prediction Table"
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "Search fund"
    )


    filtered_df = df.copy()


    if search:

        filtered_df = filtered_df[
            filtered_df[
                "Fund"
            ]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]


    # --------------------------------------------------------
    # HORIZON FILTER
    # --------------------------------------------------------

    selected_horizons = st.multiselect(
        "Select Horizons",
        HORIZONS,
        default=HORIZONS
    )


    columns = [

        "AMC",
        "FundID",
        "Fund",
        "Category",
        "Latest_Date",
        "Current_NAV"
    ]


    for horizon in selected_horizons:

        columns.extend([

            f"Predicted_NAV_{horizon}",

            f"Change_NAV_{horizon}_Percent",

            f"Prediction_Method_NAV_{horizon}"
        ])


    columns = [

        column

        for column in columns

        if column in filtered_df.columns
    ]


    st.dataframe(
        filtered_df[
            columns
        ],
        use_container_width=True,
        height=600,
        hide_index=True
    )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    csv = filtered_df[
        columns
    ].to_csv(
        index=False
    )


    st.download_button(

        label="⬇️ Download Filtered Predictions",

        data=csv,

        file_name=(
            "FundForge_NAV_Predictions.csv"
        ),

        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "FundForge | MUFAP NAV Prediction"
)

st.sidebar.caption(
    "Existing trained models • "
    "No retraining performed by dashboard"
)