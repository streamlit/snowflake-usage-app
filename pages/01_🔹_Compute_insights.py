import plost
import streamlit as st

st.set_page_config(
    page_title="Usage Insights app - Compute", page_icon="🔹", layout="centered"
)

from utils import charts, gui, processing
from utils import snowflake_connector as sf
from utils import sql as sql


def main():

    # Date selector widget
    with st.sidebar:
        date_from, date_to = gui.date_selector()

    # Header
    gui.icon("🔹")
    st.title("Compute insights")

    # ----------------------
    # ---- Service type ----
    # ----------------------

    gui.space(1)
    st.subheader("Service type")

    # Get data
    query = sql.CONSUMPTION_PER_SERVICE_TYPE_QUERY
    df = sf.sql_to_dataframe(
        query.format(date_from=date_from, date_to=date_to)
    )

    # Add filtering widget per Service type
    all_values = df["SERVICE_TYPE"].unique().tolist()
    selected_value = st.selectbox(
        "Choose service type",
        ["All"] + all_values,
        0,
    )

    if selected_value == "All":
        selected_value = all_values
    else:
        selected_value = [selected_value]

    # Filter df accordingly
    df = df[df["SERVICE_TYPE"].isin(selected_value)]

    # Get consumption
    consumption = int(df["CREDITS_USED"].sum())

    if df.empty:
        st.caption("No data found.")
    elif consumption == 0:
        st.caption("No consumption found.")
    else:
        # Sum of credits used
        credits_used_html = gui.underline(
            text=gui.pretty_print_credits(consumption),
        )
        credits_used_html += " were used"

        gui.space(1)
        st.write(credits_used_html, unsafe_allow_html=True)

        gui.space(1)
        gui.subsubheader(
            "**Compute** spend over time",
            "Aggregated by day",
        )

        # Resample by day
        df_resampled = processing.resample_by_day(
            df,
            date_column="START_TIME",
        )

        # Bar chart
        bar_chart = charts.get_bar_chart(
            df=df_resampled,
            date_column="START_TIME",
            value_column="CREDITS_USED",
        )

        st.altair_chart(bar_chart, use_container_width=True)

        # Group by
        agg_config = {"CREDITS_USED": "sum"}
        df_grouped = (
            df.groupby(["NAME", "SERVICE_TYPE"]).agg(agg_config).reset_index()
        )

        # Sort and pretty print credits
        df_grouped_top_10 = df_grouped.sort_values(
            by="CREDITS_USED", ascending=False
        ).head(10)

        df_grouped_top_10["CREDITS_USED"] = df_grouped_top_10[
            "CREDITS_USED"
        ].apply(gui.pretty_print_credits)

        gui.subsubheader(
            "**Compute** spend",
            " Grouped by NAME",
            "Top 10",
        )

        st.dataframe(
            gui.dataframe_with_podium(
                df_grouped_top_10,
            )[["NAME", "SERVICE_TYPE", "CREDITS_USED"]],
            width=600,
        )

        gui.space(1)
        gui.hbar()

    # -------------------
    # ---- Warehouse ----
    # -------------------

    st.subheader("Warehouse")

    # Get data
    warehouse_usage_hourly = sf.sql_to_dataframe(
        sql.WAREHOUSE_USAGE_HOURLY.format(
            date_from=date_from,
            date_to=date_to,
        )
    )

    # Add filtering widget per Warehouse name
    warehouses = warehouse_usage_hourly.WAREHOUSE_NAME.unique()
    selected_warehouse = st.selectbox(
        "Choose warehouse",
        warehouses.tolist(),
    )

    # Filter accordingly
    warehouse_usage_hourly_filtered = warehouse_usage_hourly[
        warehouse_usage_hourly.WAREHOUSE_NAME.eq(selected_warehouse)
    ]

    # Resample so that all the period has data (fill with 0 if needed)
    warehouse_usage_hourly_filtered = processing.resample_date_period(
        warehouse_usage_hourly_filtered,
        date_from,
        date_to,
        value_column="CREDITS_USED_COMPUTE",
    )

    gui.subsubheader("Time-histogram of **warehouse usage**")

    plost.time_hist(
        data=warehouse_usage_hourly_filtered,
        date="START_TIME",
        x_unit="day",
        y_unit="hours",
        color={
            "field": "CREDITS_USED_COMPUTE",
            "scale": {
                "scheme": charts.ALTAIR_SCHEME,
            },
        },
        aggregate=None,
        legend=None,
    )

    gui.space(1)
    gui.hbar()

    # -----------------
    # ---- Queries ----
    # -----------------

    st.subheader("Queries")

    # Get data
    queries_data = sf.get_queries_data(
        date_from,
        date_to,
    )

    # Add filtering widget per Warehouse name
    warehouses = queries_data.WAREHOUSE_NAME.dropna().unique().tolist()
    selected_warehouse = st.selectbox(
        "Choose warehouse",
        warehouses,
    )

    # Filter accordingly
    queries_data = queries_data[
        queries_data.WAREHOUSE_NAME.eq(selected_warehouse)
    ]

    gui.subsubheader(
        "Histogram of **queries duration** (in secs)", "Log scale"
    )

    # Histogram
    histogram = charts.get_histogram_chart(
        df=queries_data,
        date_column="DURATION_SECS",
    )

    st.altair_chart(histogram, use_container_width=True)

    # Top-3 longest queries
    queries_podium_df = gui.dataframe_with_podium(
        queries_data, "DURATION_SECS"
    ).head(3)

    # Only show if at least three queries!
    if len(queries_podium_df) >= 3:
        with st.expander("🔎 Zoom into top-3 longest queries in detail"):
            for query in queries_podium_df.itertuples():
                st.caption(f"{query.Index} {query.DURATION_SECS_PP}")
                st.code(query.QUERY_TEXT_PP, "sql")

    gui.space(1)
    st.write("Time-histograms of **aggregate queries duration** (in secs)")

    # Resample so that all the period has data (fill with 0 if needed)
    queries_data = processing.resample_date_period(
        queries_data, date_from, date_to, "DURATION_SECS"
    )

    num_days_selected = (date_to - date_from).days
    if num_days_selected > 14:
        st.caption("Week-day histogram")
        plost.time_hist(
            data=queries_data,
            date="START_TIME",
            x_unit="week",
            y_unit="day",
            color={
                "field": "DURATION_SECS",
                "scale": {"scheme": charts.ALTAIR_SCHEME},
            },
            aggregate="sum",
            legend=None,
        )

    st.caption("Day-hour histogram")
    plost.time_hist(
        data=queries_data,
        date="START_TIME",
        x_unit="day",
        y_unit="hours",
        color={
            "field": "DURATION_SECS",
            "scale": {"scheme": charts.ALTAIR_SCHEME},
        },
        aggregate="sum",
        legend=None,
    )

    gui.space(1)
    gui.subsubheader(
        "**Query optimization**: longest and most frequent queries",
        "Log scales (🖱️ hover for real values!)",
    )

    queries_agg = sf.sql_to_dataframe(
        sql.QUERIES_COUNT_QUERY.format(
            date_from=date_from,
            date_to=date_to,
            num_min=1,
            limit=10_000,
            warehouse_name=selected_warehouse,
        )
    )

    queries_agg = processing.apply_log1p(
        df=queries_agg, columns=["EXECUTION_MINUTES", "NUMBER_OF_QUERIES"]
    )

    scatter_chart = charts.get_scatter_chart(df=queries_agg)

    st.altair_chart(
        scatter_chart,
        use_container_width=True,
    )

    gui.space(1)
    gui.hbar()

    # -------------
    # --- Users ---
    # -------------

    st.subheader("Users")

    # Get data
    users_data = sf.sql_to_dataframe(
        sql.USERS_QUERY.format(
            date_from=date_from,
            date_to=date_to,
        )
    )

    gui.subsubheader("**Users** with the **largest** number of credits spent")

    # Bar chart
    plost.bar_chart(
        data=users_data,
        bar="USER_NAME",
        value="APPROXIMATE_CREDITS_USED",
        color=gui.BLUE_COLOR,
        direction="horizontal",
        height=200,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
