import marimo

__generated_with = "0.23.13"
app = marimo.App(width="full", app_title="SugarStatsPH")


@app.cell
def _():
    import html
    import math
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    from pathlib import Path

    return Path, go, html, math, mo, pd


@app.cell
def _(Path, pd):
    DATA_DIR = Path("data/final")
    SOURCE_URL = "https://sra.gov.ph/historicalStatistics/index"
    PROJECT_URL = "https://romaisablbgn.github.io/sugarstats-ph"

    monthly_supply = pd.read_csv(DATA_DIR / "monthly_production_withdrawals_long.csv")
    annual_supply = pd.read_csv(DATA_DIR / "annual_production_withdrawals_summary.csv")
    annual_overview = pd.read_csv(DATA_DIR / "annual_overview_supply_area_yield.csv")
    annual_area_yield = pd.read_csv(DATA_DIR / "annual_raw_production_area_yield_wide.csv")
    annual_millsite = pd.read_csv(DATA_DIR / "annual_millsite_prices_summary.csv")
    annual_metro = pd.read_csv(DATA_DIR / "annual_metro_manila_prices_summary.csv")
    millsite_prices = pd.read_csv(DATA_DIR / "monthly_millsite_prices_analysis.csv")
    metro_prices = pd.read_csv(DATA_DIR / "monthly_metro_manila_prices.csv")
    return (
        PROJECT_URL,
        SOURCE_URL,
        annual_area_yield,
        annual_metro,
        annual_millsite,
        annual_overview,
        annual_supply,
        metro_prices,
        millsite_prices,
        monthly_supply,
    )


@app.cell
def _(pd):
    MONTH_ORDER = [
        "September",
        "October",
        "November",
        "December",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
    ]

    PRICE_LABELS = {
        '"A" Export': 'Millsite "A" US Export Sugar',
        '"B" Domestic': 'Millsite "B" Domestic Sugar',
        '"D" World Market': 'Millsite "D" World Market Sugar',
        "raw_sugar": "Wholesale Raw Sugar",
        "washed_sugar": "Wholesale Washed Sugar",
        "refined_sugar": "Wholesale Refined Sugar",
    }

    PRICE_COLORS = {
        'Millsite "A" Export Sugar': "#f2b8b5",
        'Millsite "B" Domestic Sugar': "#f6a6b2",
        'Millsite "D" World Market Sugar': "#f8c9a8",
        "Wholesale Raw Sugar": "#2364aa",
        "Wholesale Washed Sugar": "#2fb344",
        "Wholesale Refined Sugar": "#d9480f",
    }

    def fmt_number(value, suffix="", decimals=0):
        if pd.isna(value):
            return "No data"
        clean_decimals = min(decimals, 2)
        return f"{value:,.{clean_decimals}f}{suffix}"

    def fmt_money(value):
        if pd.isna(value):
            return "No data"
        return f"PHP {value:,.2f}"

    def fmt_table_value(value):
        if pd.isna(value):
            return ""
        if isinstance(value, (int, float)):
            return f"{value:,.2f}"
        return str(value)

    def crop_year_sort(crop_year):
        return int(str(crop_year).split("-")[0])

    def month_sort_frame(df):
        return df.assign(
            month=pd.Categorical(df["month"], categories=MONTH_ORDER, ordered=True)
        ).sort_values("month")

    return (
        MONTH_ORDER,
        PRICE_COLORS,
        PRICE_LABELS,
        crop_year_sort,
        fmt_money,
        fmt_number,
        fmt_table_value,
        month_sort_frame,
    )


@app.cell
def _(mo):
    mo.md("""
    # SugarStatsPH

    Explore how Philippine sugar production, withdrawals, and prices move together from 2010 to 2025. Build a crop-year dashboard and download a PDF report with your selected supply, demand, and price series.
    """)
    return


@app.cell
def _(
    annual_area_yield,
    annual_metro,
    annual_millsite,
    annual_overview,
    annual_supply,
    pd,
):
    supply_wide = annual_supply.pivot_table(
        index=["crop_year", "crop_year_start"],
        columns="indicator",
        values="total_value_mt",
        aggfunc="first",
    ).reset_index()

    annual_cards = annual_overview.merge(
        annual_area_yield,
        on=["crop_year", "crop_year_start"],
        how="outer",
        suffixes=("", "_area"),
    )

    if "area_harvested_hectares" not in annual_cards.columns:
        annual_cards["area_harvested_hectares"] = pd.NA

    b_millsite = annual_millsite[
        annual_millsite["price_type"].eq('"B" Domestic')
    ][["crop_year", "crop_year_start", "average_price"]].rename(
        columns={"average_price": "avg_millsite_b_domestic_php_lkg"}
    )

    metro_wholesale = annual_metro[
        annual_metro["market_level"].eq("wholesale")
        & annual_metro["product_type"].isin(["raw_sugar", "refined_sugar"])
    ].pivot_table(
        index=["crop_year", "crop_year_start"],
        columns="product_type",
        values="average_price",
        aggfunc="first",
    ).reset_index()
    metro_wholesale = metro_wholesale.rename(
        columns={
            "raw_sugar": "avg_metro_manila_raw_php_lkg",
            "refined_sugar": "avg_metro_manila_refined_php_lkg",
        }
    )

    overview_table = (
        supply_wide.merge(
            b_millsite,
            on=["crop_year", "crop_year_start"],
            how="left",
        )
        .merge(
            metro_wholesale,
            on=["crop_year", "crop_year_start"],
            how="left",
        )
        .sort_values("crop_year_start", ascending=False)
    )

    overview_table = overview_table.rename(
        columns={
            "crop_year": "Crop Year",
            "raw_sugar_production": "Production Raw Sugar MT",
            "refined_sugar_production": "Production Refined Sugar MT",
            "raw_sugar_domestic_withdrawals": "Withdrawals Raw Sugar MT",
            "refined_sugar_withdrawals": "Withdrawals Refined Sugar MT",
            "avg_millsite_b_domestic_php_lkg": 'Millsite "B" Sugar',
            "avg_metro_manila_raw_php_lkg": "Raw Sugar (Metro Manila)",
            "avg_metro_manila_refined_php_lkg": "Refined Sugar (Metro Manila)",
        }
    )

    overview_table = overview_table[
        [
            "Crop Year",
            "Production Raw Sugar MT",
            "Production Refined Sugar MT",
            "Withdrawals Raw Sugar MT",
            "Withdrawals Refined Sugar MT",
            'Millsite "B" Sugar',
            "Raw Sugar (Metro Manila)",
            "Refined Sugar (Metro Manila)",
        ]
    ]
    return annual_cards, b_millsite, overview_table


@app.cell
def _(fmt_table_value, html, mo, overview_table):
    overview_display = overview_table.copy()
    for column in overview_display.columns:
        if column != "Crop Year":
            overview_display[column] = overview_display[column].map(fmt_table_value)

    header_html = """
        <tr>
          <th class="top-header" rowspan="2">Crop Year</th>
          <th class="top-header" colspan="2">Annual Production (MT)</th>
          <th class="top-header" colspan="2">Annual Withdrawal (MT)</th>
          <th class="top-header" colspan="3">Average Prices (Php/LKg)</th>
        </tr>
        <tr>
          <th class="sub-header">Raw Sugar</th>
          <th class="sub-header">Refined Sugar</th>
          <th class="sub-header">Raw Sugar</th>
          <th class="sub-header">Refined Sugar</th>
          <th class="sub-header">Millsite</th>
          <th class="sub-header">Raw Sugar</th>
          <th class="sub-header">Refined Sugar</th>
        </tr>
    """
    row_html = []
    for _, _row in overview_display.iterrows():
        cells = "".join(f"<td>{html.escape(str(_value))}</td>" for _value in _row)
        row_html.append(f"<tr>{cells}</tr>")

    overview_html = f"""
    <style>
    .overview-wrap {{
        max-height: 260px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
        border-radius: 8px;
    }}
    .overview-table {{
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
    }}
    .overview-table th {{
        position: sticky;
        background: #f8f9fa;
        border-bottom: 1px solid #ced4da;
        color: #212529;
        font-weight: 700;
        padding: 10px 12px;
        text-align: center;
    }}
    .overview-table .top-header {{
        top: 0;
        z-index: 3;
    }}
    .overview-table .sub-header {{
        top: 40px;
        z-index: 2;
    }}
    .overview-table td {{
        border-bottom: 1px solid #edf2f7;
        color: #343a40;
        padding: 9px 12px;
        text-align: right;
    }}
    .overview-table td:first-child,
    .overview-table th:first-child {{
        text-align: left;
        white-space: nowrap;
    }}
    </style>
    <div class="overview-wrap">
      <table class="overview-table">
        <thead>{header_html}</thead>
        <tbody>{''.join(row_html)}</tbody>
      </table>
    </div>
    """

    mo.vstack([mo.md("## Overview"), mo.Html(overview_html)])
    return


@app.cell
def _(crop_year_sort, mo, monthly_supply):
    crop_year_options = sorted(
        monthly_supply["crop_year"].dropna().unique(),
        key=crop_year_sort,
    )
    default_crop_year = crop_year_options[-1]

    crop_year = mo.ui.dropdown(
        options=crop_year_options,
        value=default_crop_year,
        label="Crop year",
    )

    raw_production = mo.ui.checkbox(value=True, label="Raw sugar")
    refined_production = mo.ui.checkbox(value=False, label="Refined sugar")
    raw_withdrawals = mo.ui.checkbox(value=True, label="Raw sugar")
    refined_withdrawals = mo.ui.checkbox(value=False, label="Refined sugar")
    millsite_a = mo.ui.checkbox(value=False, label='"A" Export sugar')
    millsite_b = mo.ui.checkbox(value=True, label='"B" Domestic sugar')
    millsite_d = mo.ui.checkbox(value=False, label='"D" World Market sugar')
    wholesale_raw = mo.ui.checkbox(value=True, label="Raw sugar")
    wholesale_washed = mo.ui.checkbox(value=False, label="Washed sugar")
    wholesale_refined = mo.ui.checkbox(value=False, label="Refined sugar")

    controls = mo.vstack(
        [
            mo.md("## Generate a report"),
            crop_year,
            mo.hstack(
                [
                    mo.vstack([mo.md("**Production**"), raw_production, refined_production]),
                    mo.vstack([mo.md("**Withdrawals**"), raw_withdrawals, refined_withdrawals]),
                    mo.vstack([mo.md("**Millsite Prices**"), millsite_a, millsite_b, millsite_d]),
                    mo.vstack([mo.md("**Wholesale Market Prices**"), wholesale_raw, wholesale_washed, wholesale_refined]),
                ],
                justify="start",
            ),
        ]
    )
    controls
    return (
        crop_year,
        millsite_a,
        millsite_b,
        millsite_d,
        raw_production,
        raw_withdrawals,
        refined_production,
        refined_withdrawals,
        wholesale_raw,
        wholesale_refined,
        wholesale_washed,
    )


@app.cell
def _(
    PRICE_LABELS,
    crop_year,
    metro_prices,
    millsite_a,
    millsite_b,
    millsite_d,
    millsite_prices,
    month_sort_frame,
    monthly_supply,
    pd,
    raw_production,
    raw_withdrawals,
    refined_production,
    refined_withdrawals,
    wholesale_raw,
    wholesale_refined,
    wholesale_washed,
):
    selected_indicators = []
    if raw_production.value:
        selected_indicators.append("raw_sugar_production")
    if refined_production.value:
        selected_indicators.append("refined_sugar_production")
    if raw_withdrawals.value:
        selected_indicators.append("raw_sugar_domestic_withdrawals")
    if refined_withdrawals.value:
        selected_indicators.append("refined_sugar_withdrawals")

    dashboard_supply = monthly_supply[
        monthly_supply["crop_year"].eq(crop_year.value)
        & monthly_supply["indicator"].isin(selected_indicators)
    ].copy()

    selected_millsite_types = []
    if millsite_a.value:
        selected_millsite_types.append('"A" Export')
    if millsite_b.value:
        selected_millsite_types.append('"B" Domestic')
    if millsite_d.value:
        selected_millsite_types.append('"D" World Market')

    selected_market_products = []
    if wholesale_raw.value:
        selected_market_products.append("raw_sugar")
    if wholesale_washed.value:
        selected_market_products.append("washed_sugar")
    if wholesale_refined.value:
        selected_market_products.append("refined_sugar")

    price_frames = []

    if selected_millsite_types:
        millsite_selected = millsite_prices[
            millsite_prices["crop_year"].eq(crop_year.value)
            & millsite_prices["price_type"].isin(selected_millsite_types)
            & millsite_prices["unit"].eq("PHP/LKg")
        ].copy()
        millsite_selected["series"] = millsite_selected["price_type"].map(PRICE_LABELS)
        millsite_selected["price_php_lkg"] = millsite_selected["price"]
        price_frames.append(millsite_selected[["month", "month_order", "series", "price_php_lkg"]])

    if selected_market_products:
        market_selected = metro_prices[
            metro_prices["crop_year"].eq(crop_year.value)
            & metro_prices["market_level"].eq("wholesale")
            & metro_prices["product_type"].isin(selected_market_products)
        ].copy()
        market_selected["series"] = market_selected["product_type"].map(PRICE_LABELS)
        market_selected["price_php_lkg"] = market_selected["price"]
        price_frames.append(market_selected[["month", "month_order", "series", "price_php_lkg"]])

    if price_frames:
        dashboard_prices = month_sort_frame(pd.concat(price_frames, ignore_index=True))
    else:
        dashboard_prices = pd.DataFrame(
            columns=["month", "month_order", "series", "price_php_lkg"]
        )
    return dashboard_prices, dashboard_supply


@app.cell
def _(annual_cards, b_millsite, crop_year, fmt_money, fmt_number, html, mo):
    card_row = annual_cards[annual_cards["crop_year"].eq(crop_year.value)]
    price_row = b_millsite[b_millsite["crop_year"].eq(crop_year.value)]

    if card_row.empty:
        area = yield_value = raw_prod = refined_prod = None
    else:
        _card_values = card_row.iloc[0]
        area = _card_values.get("area_harvested_hectares")
        yield_value = _card_values.get("yield_lkg_per_ha")
        raw_prod = _card_values.get("raw_sugar_production")
        refined_prod = _card_values.get("refined_sugar_production")

    avg_b_price = (
        price_row["avg_millsite_b_domestic_php_lkg"].iloc[0]
        if not price_row.empty
        else None
    )

    cards = [
        (fmt_number(area, " ha"), "Total Area Harvested"),
        (fmt_number(yield_value, " LKg/ha", 2), "Yield per Hectare"),
        (fmt_number(raw_prod, " MT"), "Annual Raw Sugar Production"),
        (fmt_number(refined_prod, " MT"), "Annual Refined Sugar Production"),
        (fmt_money(avg_b_price), 'Average Millsite Price "B"'),
    ]
    report_cards = cards
    card_html = "".join(
        f"""
        <div class="stat-card">
          <div class="stat-value">{html.escape(value)}</div>
          <div class="stat-label">{html.escape(label)}</div>
        </div>
        """
        for value, label in cards
    )
    mo.Html(
        f"""
        <style>
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(5, minmax(150px, 1fr));
            gap: 12px;
            margin: 14px 0 18px;
        }}
        .stat-card {{
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 14px 16px;
            background: #ffffff;
        }}
        .stat-value {{
            color: #111827;
            font-size: 25px;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 8px;
        }}
        .stat-label {{
            color: #495057;
            font-size: 12px;
            font-weight: 600;
            line-height: 1.25;
            text-transform: uppercase;
        }}
        @media (max-width: 900px) {{
            .stat-grid {{
                grid-template-columns: repeat(2, minmax(150px, 1fr));
            }}
        }}
        </style>
        <div class="stat-grid">{card_html}</div>
        """
    )
    return (report_cards,)


@app.cell
def _(MONTH_ORDER, dashboard_supply, go, month_sort_frame):
    supply_data = dashboard_supply.copy()
    supply_data["flow"] = supply_data["indicator"].map(
        {
            "raw_sugar_production": "Raw production",
            "raw_sugar_domestic_withdrawals": "Raw withdrawals",
            "refined_sugar_production": "Refined production",
            "refined_sugar_withdrawals": "Refined withdrawals",
        }
    )
    supply_data["product_group"] = supply_data["indicator"].map(
        {
            "raw_sugar_production": "Raw sugar",
            "raw_sugar_domestic_withdrawals": "Raw sugar",
            "refined_sugar_production": "Refined sugar",
            "refined_sugar_withdrawals": "Refined sugar",
        }
    )
    supply_data = month_sort_frame(supply_data)

    production_chart = go.Figure()
    bar_styles = {
        "Raw production": ("Raw sugar", "#2f9e44"),
        "Raw withdrawals": ("Raw sugar", "#e03131"),
        "Refined production": ("Refined sugar", "#74c69d"),
        "Refined withdrawals": ("Refined sugar", "#c92a2a"),
    }

    for flow, (product_group, color) in bar_styles.items():
        flow_data = supply_data[supply_data["flow"].eq(flow)]
        if flow_data.empty:
            continue
        production_chart.add_bar(
            x=flow_data["month"],
            y=flow_data["value_mt"],
            name=flow,
            offsetgroup=product_group,
            legendgroup=flow,
            marker_color=color,
            opacity=1,
            hovertemplate="%{x}<br>%{y:,.2f} MT<extra>" + flow + "</extra>",
        )

    trend_styles = {
        "Raw production": "#1b7f36",
        "Raw withdrawals": "#b42318",
        "Refined production": "#40916c",
        "Refined withdrawals": "#8f1d1d",
    }
    for flow, color in trend_styles.items():
        flow_data = supply_data[supply_data["flow"].eq(flow)]
        if flow_data.empty:
            continue
        production_chart.add_scatter(
            x=flow_data["month"],
            y=flow_data["value_mt"],
            name=f"{flow} trend",
            mode="lines",
            opacity=0.6,
            line=dict(color=color, width=2, shape="spline", smoothing=1.15),
            hovertemplate="%{x}<br>%{y:,.2f} MT<extra>" + f"{flow} trend" + "</extra>",
        )

    _ = production_chart.update_layout(
        title=f"Monthly Production and Withdrawals Chart",
        barmode="stack",
        bargap=0.28,
        xaxis=dict(title="Month", categoryorder="array", categoryarray=MONTH_ORDER),
        yaxis_title="Metric tons",
        legend_title="Supply and demand series",
        legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0),
        hovermode="x unified",
        template="plotly_white",
        height=500,
        margin=dict(l=55, r=20, t=55, b=130),
        autosize=True,
    )
    return (production_chart,)


@app.cell
def _(MONTH_ORDER, PRICE_COLORS, dashboard_prices, go):
    price_chart = go.Figure()

    for series in dashboard_prices["series"].dropna().unique():
        series_data = dashboard_prices[dashboard_prices["series"].eq(series)]
        series_data = series_data.copy()
        series_data["smoothed_price"] = (
            series_data["price_php_lkg"]
            .rolling(window=3, min_periods=1, center=True)
            .mean()
        )
        price_chart.add_scatter(
            x=series_data["month"],
            y=series_data["smoothed_price"],
            name=series,
            mode="lines",
            customdata=series_data["price_php_lkg"],
            line=dict(
                color=PRICE_COLORS.get(series, "#495057"),
                width=3,
                shape="spline",
                smoothing=0.55,
            ),
            hovertemplate="%{x}<br>Trend: PHP %{y:,.2f}/LKg<br>Actual: PHP %{customdata:,.2f}/LKg<extra>" + series + "</extra>",
        )

    if dashboard_prices.empty:
        price_chart.add_annotation(
            text="Select at least one price series.",
            showarrow=False,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )

    _ = price_chart.update_layout(
        title=f"Monthly Price Index Chart",
        xaxis=dict(title="Month", categoryorder="array", categoryarray=MONTH_ORDER),
        yaxis_title="Php/LKg",
        legend_title="Price series",
        legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0),
        hovermode="x unified",
        template="plotly_white",
        height=500,
        margin=dict(l=50, r=20, t=55, b=130),
        autosize=True,
    )
    return (price_chart,)


@app.cell
def _(mo, price_chart, production_chart):
    production_plot = mo.ui.plotly(
        production_chart,
        config={"responsive": True, "displayModeBar": True},
    )
    price_plot = mo.ui.plotly(
        price_chart,
        config={"responsive": True, "displayModeBar": True},
    )
    chart_row = mo.hstack(
        [production_plot, price_plot],
        justify="start",
        align="stretch",
        wrap=False,
        gap=1,
        widths=[0.65, 0.35],
    )
    chart_row
    return


@app.cell
def _(
    MONTH_ORDER,
    PRICE_COLORS,
    PROJECT_URL,
    SOURCE_URL,
    crop_year,
    dashboard_prices,
    dashboard_supply,
    math,
    report_cards,
):
    def build_pdf_report():
        def clean_text(text):
            return (
                str(text)
                .replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
            )

        def hex_to_rgb(color):
            color = color.lstrip("#")
            return tuple(int(color[i : i + 2], 16) / 255 for i in (0, 2, 4))

        def text(cmds, x, y, value, size=10, bold=False, italic=False):
            font = "/F3" if italic else "/F2" if bold else "/F1"
            cmds.append(f"0 0 0 rg BT {font} {size} Tf {x:.2f} {y:.2f} Td ({clean_text(value)}) Tj ET")

        def fill_rect(cmds, x, y, width, height, color):
            if height <= 0:
                return
            r, g, b = hex_to_rgb(color)
            cmds.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} {width:.2f} {height:.2f} re f")

        def stroke_line(cmds, points, color, width=1.3):
            if len(points) < 2:
                return
            r, g, b = hex_to_rgb(color)
            first = points[0]
            commands = [f"{r:.3f} {g:.3f} {b:.3f} RG {width:.2f} w", f"{first[0]:.2f} {first[1]:.2f} m"]
            for x, y in points[1:]:
                commands.append(f"{x:.2f} {y:.2f} l")
            commands.append("S")
            cmds.append(" ".join(commands))

        def footer(cmds):
            text(cmds, 36, 28, "Data Source: ", 7)
            text(cmds, 86, 28, SOURCE_URL, 7, italic=True)
            text(cmds, 334, 28, "Report generated by SugarStatsPH: ", 7)
            text(cmds, 456, 28, PROJECT_URL, 7, italic=True)

        def axis(cmds, x0, y0, width, height, title):
            text(cmds, x0, y0 + height + 32, title, 15, True)
            cmds.append("0.200 0.227 0.263 RG 1 w")
            cmds.append(f"{x0:.2f} {y0:.2f} m {x0 + width:.2f} {y0:.2f} l S")
            cmds.append(f"{x0:.2f} {y0:.2f} m {x0:.2f} {y0 + height:.2f} l S")

        def dashboard_page():
            cmds = []
            page_width = 841.89
            page_height = 595.28
            text(cmds, 24, 552, f"SugarStatsPH Report for Crop Year {crop_year.value}", 24, False)
            card_y = 486
            card_w = 152
            for index, (value, label) in enumerate(report_cards):
                x = 24 + index * 160
                fill_rect(cmds, x, card_y, card_w, 36, "#ffffff")
                cmds.append("0.878 0.902 0.929 RG 0.5 w")
                cmds.append(f"{x:.2f} {card_y:.2f} {card_w:.2f} 36 re S")
                text(cmds, x + 8, card_y + 22, value, 10, True)
                text(cmds, x + 8, card_y + 9, label.upper()[:34], 5, True)

            prod_x0, prod_y0, prod_width, prod_height = 42, 164, 475, 250
            price_x0, price_y0, price_width, price_height = 590, 164, 205, 250
            axis(cmds, prod_x0, prod_y0, prod_width, prod_height, f"Monthly Production and Withdrawals Chart")
            axis(cmds, price_x0, price_y0, price_width, price_height, f"Monthly Price Index Chart")

            supply = dashboard_supply.copy()
            supply["flow"] = supply["indicator"].map(
                {
                    "raw_sugar_production": "Raw production",
                    "raw_sugar_domestic_withdrawals": "Raw withdrawals",
                    "refined_sugar_production": "Refined production",
                    "refined_sugar_withdrawals": "Refined withdrawals",
                }
            )
            supply["product_group"] = supply["indicator"].map(
                {
                    "raw_sugar_production": "Raw sugar",
                    "raw_sugar_domestic_withdrawals": "Raw sugar",
                    "refined_sugar_production": "Refined sugar",
                    "refined_sugar_withdrawals": "Refined sugar",
                }
            )

            stack_max = 1
            for month in MONTH_ORDER:
                for product in ["Raw sugar", "Refined sugar"]:
                    value = supply[
                        supply["month"].eq(month) & supply["product_group"].eq(product)
                    ]["value_mt"].sum()
                    stack_max = max(stack_max, value)
            scale = prod_height / stack_max
            month_step = prod_width / len(MONTH_ORDER)
            bar_width = 7
            colors = {
                "Raw production": "#2f9e44",
                "Raw withdrawals": "#e03131",
                "Refined production": "#74c69d",
                "Refined withdrawals": "#c92a2a",
            }

            for month_index, month in enumerate(MONTH_ORDER):
                center = prod_x0 + month_index * month_step + month_step / 2
                text(cmds, center - 9, prod_y0 - 16, month[:3], 6)
                for product, offset in [("Raw sugar", -7), ("Refined sugar", 7)]:
                    y_cursor = prod_y0
                    product_data = supply[
                        supply["month"].eq(month) & supply["product_group"].eq(product)
                    ]
                    for flow in [
                        f"{product.split()[0]} production",
                        f"{product.split()[0]} withdrawals",
                    ]:
                        value = product_data[product_data["flow"].eq(flow)]["value_mt"].sum()
                        fill_rect(
                            cmds,
                            center + offset - bar_width / 2,
                            y_cursor,
                            bar_width,
                            value * scale,
                            colors.get(flow, "#868e96"),
                        )
                        y_cursor += value * scale

            for flow, color in colors.items():
                points = []
                for month_index, month in enumerate(MONTH_ORDER):
                    flow_data = supply[supply["month"].eq(month) & supply["flow"].eq(flow)]
                    if flow_data.empty:
                        continue
                    x = prod_x0 + month_index * month_step + month_step / 2
                    y = prod_y0 + flow_data["value_mt"].sum() * scale
                    points.append((x, y))
                stroke_line(cmds, points, color, 0.9)

            legend_y = 122
            for index, (label, color) in enumerate(colors.items()):
                x = 42 + (index % 4) * 112
                y = legend_y
                fill_rect(cmds, x, y, 7, 7, color)
                text(cmds, x + 11, y + 1, label, 6)

            prices = dashboard_prices.dropna(subset=["price_php_lkg"]).copy()
            if prices.empty:
                text(cmds, price_x0 + 38, price_y0 + 118, "No selected price series.", 9)
            else:
                min_price = prices["price_php_lkg"].min()
                max_price = prices["price_php_lkg"].max()
                if math.isclose(min_price, max_price):
                    min_price -= 1
                    max_price += 1
                price_month_step = price_width / len(MONTH_ORDER)

                for series in prices["series"].dropna().unique():
                    series_data = prices[prices["series"].eq(series)].copy()
                    series_data["smoothed_price"] = (
                        series_data["price_php_lkg"]
                        .rolling(window=3, min_periods=1, center=True)
                        .mean()
                    )
                    points = []
                    for month_index, month in enumerate(MONTH_ORDER):
                        month_value = series_data[series_data["month"].eq(month)]["smoothed_price"]
                        if month_value.empty:
                            continue
                        x = price_x0 + month_index * price_month_step + price_month_step / 2
                        y = price_y0 + ((month_value.iloc[0] - min_price) / (max_price - min_price)) * price_height
                        points.append((x, y))
                    stroke_line(cmds, points, PRICE_COLORS.get(series, "#495057"), 1.7)

                for month_index, month in enumerate(MONTH_ORDER):
                    center = price_x0 + month_index * price_month_step + price_month_step / 2
                    text(cmds, center - 8, price_y0 - 16, month[:3], 6)

                for index, series in enumerate(prices["series"].dropna().unique()):
                    x = price_x0 + (index % 1) * 100
                    y = 122 - index * 12
                    fill_rect(cmds, x, y, 7, 7, PRICE_COLORS.get(series, "#495057"))
                    text(cmds, x + 11, y + 1, series[:28], 6)

            footer(cmds)
            return "\n".join(cmds).encode("latin-1", errors="replace")

        page_streams = [dashboard_page()]

        objects = []
        page_refs = []
        next_id = 6

        for content in page_streams:
            page_id = next_id
            content_id = next_id + 1
            source_link_id = next_id + 2
            project_link_id = next_id + 3
            next_id += 4
            page_refs.append(f"{page_id} 0 R")
            objects.append(
                (
                    page_id,
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 841.89 595.28] "
                    f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> "
                    f"/Annots [{source_link_id} 0 R {project_link_id} 0 R] "
                    f"/Contents {content_id} 0 R >>".encode("latin-1"),
                )
            )
            objects.append(
                (
                    content_id,
                    b"<< /Length "
                    + str(len(content)).encode("latin-1")
                    + b" >>\nstream\n"
                    + content
                    + b"\nendstream",
                )
            )
            objects.append(
                (
                    source_link_id,
                    f"<< /Type /Annot /Subtype /Link /Rect [84 24 250 36] /Border [0 0 0] /A << /S /URI /URI ({SOURCE_URL}) >> >>".encode("latin-1"),
                )
            )
            objects.append(
                (
                    project_link_id,
                    f"<< /Type /Annot /Subtype /Link /Rect [452 24 590 36] /Border [0 0 0] /A << /S /URI /URI ({PROJECT_URL}) >> >>".encode("latin-1"),
                )
            )

        base_objects = [
            (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
            (
                2,
                f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {len(page_refs)} >>".encode(
                    "latin-1"
                ),
            ),
            (3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
            (4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"),
            (5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>"),
        ]

        all_objects = sorted(base_objects + objects, key=lambda item: item[0])
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for object_id, body in all_objects:
            offsets.append(len(pdf))
            pdf.extend(f"{object_id} 0 obj\n".encode("latin-1"))
            pdf.extend(body)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(all_objects) + 1}\n".encode("latin-1"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        pdf.extend(
            f"trailer << /Size {len(all_objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
        )
        return bytes(pdf)

    pdf_report = build_pdf_report()
    return (pdf_report,)


@app.cell
def _(crop_year, mo, pdf_report):
    mo.vstack(
        [
            mo.download(
                data=pdf_report,
                filename=f"sugarstatsph_{crop_year.value}_dashboard_report.pdf",
                mimetype="application/pdf",
                label="Download PDF Report",
            ),
            mo.md(
                "_Disclaimer: SugarStatsPH is not responsible for any errors and data inaccuracy. Users should practice due diligence in using generated reports._"
            ),
        ]
    )
    return


@app.cell
def _(SOURCE_URL, mo):
    mo.md(f"""
    Data Source: Sugar Regulatory Administration (SRA) Historical Statistics  
    {SOURCE_URL}
    """)
    return


if __name__ == "__main__":
    app.run()
