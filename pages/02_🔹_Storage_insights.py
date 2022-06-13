import streamlit as st

st.set_page_config(
    page_title="Usage Insights app - Storage", page_icon="🔹", layout="centered"
)

from utils import charts, gui, processing
from utils import snowflake_connector as sf
from utils import sql


def main():

    # Date selector widget
    with st.sidebar:
        date_from, date_to = gui.date_selector()

    # Header
    gui.icon("🔹")
    st.title("Storage insights")

    # Get data
    query = sql.STORAGE_QUERY
    df = sf.sql_to_dataframe(
        query.format(date_from=date_from, date_to=date_to)
    )

    # Get consumption
    consumption = df["DATABASE_BYTES"].sum()

    if df.empty:
        st.caption("No data found.")
        st.stop()
    if consumption == 0:
        st.caption("No consumption!")
        st.stop()

    # Resample by day
    df_resampled = processing.resample_by_day(
        df,
        date_column="USAGE_DATE",
    )

    # Average bytes used per day
    credits_used_html = "Average "
    credits_used_html += gui.underline(
        text=gui.pretty_print_bytes(int(df_resampled.DATABASE_BYTES.mean())),
        color=gui.BLUE_COLOR,
    )
    credits_used_html += " were used per day"

    gui.space(1)
    st.write(credits_used_html, unsafe_allow_html=True)

    gui.space(1)
    gui.subsubheader(
        "**Storage** spend over time",
        "Aggregated by day",
    )

    # Bar chart
    chart = charts.get_bar_chart(
        df=df_resampled,
        date_column="USAGE_DATE",
        value_column="DATABASE_BYTES",
    )

    st.altair_chart(chart, use_container_width=True)

    # st.write(
    #     df_resampled.groupby(
    #         ["OBJECT_NAME", "USAGE_DATE"]
    #     ).DATABASE_BYTES.mean()
    # )

    # Group by
    df_grouped = (
        df.groupby(["OBJECT_NAME", "USAGE_DATE"])
        .DATABASE_BYTES.mean()
        .reset_index()
        .groupby("OBJECT_NAME")
        .mean()
        .reset_index()
    )
    # agg_config = {"DATABASE_BYTES": "sum"}
    # df_grouped = df.groupby("OBJECT_NAME").agg(agg_config).reset_index()

    # Sort and pretty print credits
    df_grouped_top_10 = df_grouped.sort_values(
        by="DATABASE_BYTES", ascending=False
    ).head(10)

    df_grouped_top_10["AVG_DAILY_STORAGE_SIZE"] = df_grouped_top_10[
        "DATABASE_BYTES"
    ].apply(gui.pretty_print_bytes)

    # Pretty print BYTES
    # value_pretty_print_column = "DATABASE_BYTES_PP"
    # df_grouped[value_pretty_print_column] = df_grouped["DATABASE_BYTES"].apply(
    # gui.pretty_print_bytes
    # )
    # df_grouped["AVG_DAILY_STORAGE_SIZE"] = df_grouped[
    #     "DATABASE_BYTES_PP"
    # ].apply(lambda x: x + " " * 10)

    # df_grouped = df_grouped.sort_values(
    #     by="DATABASE_BYTES",
    #     ascending=False,
    # )

    gui.subsubheader(
        "**Storage** spend per day",
        "Average",
        "Grouped by OBJECT_NAME",
        "Top 10",
    )

    st.dataframe(
        gui.dataframe_with_podium(
            df_grouped_top_10[["OBJECT_NAME", "AVG_DAILY_STORAGE_SIZE"]],
        ),
    )


if __name__ == "__main__":
    main()
