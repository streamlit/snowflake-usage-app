import streamlit as st

st.set_page_config(
    page_title="Usage Insights app - Data Transfer",
    page_icon="🔹",
    layout="centered",
)

from app_utils import charts, gui, processing
from app_utils import snowflake_connector as sf
from app_utils import sql


def main():

    # Date selector widget
    with st.sidebar:
        date_from, date_to = gui.date_selector()

    # Header
    gui.icon("🔹")
    st.title("Data Transfer insights")

    # Get data
    query = sql.DATA_TRANSFER_QUERY
    df = sf.sql_to_dataframe(
        query.format(
            date_from=date_from,
            date_to=date_to,
        )
    )

    gui.space(1)
    st.subheader("Target region")

    # Add filtering widget
    all_values = df["TARGET_REGION"].unique().tolist()
    selected_value = st.selectbox(
        "Choose target region",
        ["All"] + all_values,
        0,
    )

    if selected_value == "All":
        selected_value = all_values
    else:
        selected_value = [selected_value]

    # Filter df accordingly
    df = df[df["TARGET_REGION"].isin(selected_value)]

    # Get consumption
    consumption = int(df["BYTES_TRANSFERRED"].sum())

    if df.empty:
        st.caption("No data found.")
        st.stop()
    if consumption == 0:
        st.caption("No consumption!")
        st.stop()

    # Sum of credits used
    credits_used_html = gui.underline(
        text=gui.pretty_print_bytes(consumption),
        color=gui.BLUE_COLOR,
    )
    credits_used_html += " were used"

    gui.space(1)
    st.write(credits_used_html, unsafe_allow_html=True)

    gui.space(1)
    gui.subsubheader(
        "**Data Transfer** spend over time",
        "Aggregated by day",
    )

    # Resample by day
    df_resampled = processing.resample_by_day(
        df,
        date_column="START_TIME",
    )

    # Bar chart
    chart = charts.get_bar_chart(
        df=df_resampled,
        date_column="START_TIME",
        value_column="BYTES_TRANSFERRED",
    )

    st.altair_chart(chart, use_container_width=True)

    # Group by
    agg_config = {"BYTES_TRANSFERRED": "sum"}
    df_grouped = (
        df.groupby(["TRANSFER_TYPE", "TARGET_CLOUD", "TARGET_REGION"])
        .agg(agg_config)
        .reset_index()
    )

    # Sort and pretty print credits
    df_grouped_top_10 = df_grouped.sort_values(
        by="BYTES_TRANSFERRED", ascending=False
    ).head(10)

    df_grouped_top_10["BYTES_TRANSFERRED"] = df_grouped_top_10[
        "BYTES_TRANSFERRED"
    ].apply(gui.pretty_print_bytes)

    gui.subsubheader(
        "**Storage** spend",
        " Grouped by TRANSFER_TYPE",
        "Top 10",
    )

    st.dataframe(
        gui.dataframe_with_podium(
            df_grouped_top_10[
                [
                    "TRANSFER_TYPE",
                    "TARGET_CLOUD",
                    "TARGET_REGION",
                    "BYTES_TRANSFERRED",
                ]
            ]
        ),
        width=600,
    )


if __name__ == "__main__":
    main()
