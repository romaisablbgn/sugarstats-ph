# SugarStatsPH

**SugarStatsPH** is a web app built with [marimo](https://marimo.io/) that transforms 15 years of Philippine sugar production and trade reports into clean, interactive, and downloadable visualizations.

This app allows users to explore trends in:

* Sugar production
* Sugar withdrawals
* Millsite and Wholesale market prices

**[View SugarStatsPH Web App](https://romaisablbgn.github.io/sugarstats-ph/)**: https://romaisablbgn.github.io/sugarstats-ph

**[View source data](https://www.sra.gov.ph/historicalStatistics/index)**: https://www.sra.gov.ph/historicalStatistics/index

> SugarStatsPH is an independent data visualization project and is not an official publication of the Sugar Regulatory Administration.

## Preview

![SugarStatsPH web app preview](docs\images\sugarstats-ph_preview.png)

### Sample Downloadable PDF Report

![Sample PDF report](docs\images\sugarstatsph_2024-2025_sample_dashboard_report.png)

## Purpose

SugarStatsPH is designed to help Philippine sugar industry stakeholders and the public quickly explore historical trends in the Philippine sugar sector. At a glance, the dashboard can help answer the following questions:

- What were the total harvested area, yield per hectare, and annual sugar production for a selected crop year?
- How do annual raw and refined sugar production and withdrawal volumes compare across months and crop years?
- During which months do sugar withdrawals exceed or fall below production?
- How do sugar prices move alongside monthly production and withdrawals?
- Which months or crop years show notable increases, declines, or unusual gaps in production, withdrawals, or prices?

## How to Use SugarStatsPH

1. **Review the annual overview.**  
   The overview table provides an at-a-glance comparison of annual raw and refined sugar production, annual raw and refined sugar withdrawals, average millsite prices, and average wholesale market prices. Scroll through the table to review figures from different crop years.
   ![SugarStatsPH Annual Overview Preview](docs\images\sugarstats-ph_annual_overview.jpeg)

2. **Select a crop year and review the summary cards.**  
   Choose a crop year from the dropdown menu. The summary cards automatically update to display the selected crop year's total harvested area, yield per hectare, annual raw sugar production, annual refined sugar production, and Average "B" sugar millsite price.
    ![SugarStatsPH Summary Cards Preview](docs\images\sugarstats-ph_summary_cards_preview.png)

3. **Generate a customized report.**  
   Select the production, withdrawal, millsite price, and wholesale market price series you want to examine. You may select all available series or only a few to create a more focused report.

   By default, the charts will display the following data:![Generate a report available series selector](docs\images\sugarstats-ph_generate_report_selector.png)

4. **Explore the monthly charts.**  
   The dashboard generates two charts based on the selected crop year and data series:
   
   ![SugarStatsPH Monthly Charts Preview](docs\images\sugarstats-ph_monthly_charts_preview.png)

   - **Monthly Production and Withdrawals Chart:** The chart on the left compares monthly sugar production and withdrawals, providing a view of supply and demand movements throughout the crop year.
   - **Monthly Price Index Chart:** The chart on the right compares the selected millsite and wholesale market price series.
   

5. **Download the generated report.**  
   After selecting and reviewing the data, click the **Download PDF Report** button to save an A4-sized PDF copy of your generated report.


## Key Terms

| Term                | Definition                                                                                                                                                                                                                                                      |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Crop Year**       | The reporting period used by the Philippine sugar industry. It usually begins in September and ends in August of the following year. See Sugar Orders No. 1 in  [SRA Sugar Orders](https://www.sra.gov.ph/policy/sugarOrder).                                                    |
| **Raw Sugar**       | Sugar produced by sugar mills before further refining. It is typically brown in color.                                                                                                                                                                          |
| **Refined Sugar**   | Sugar that has undergone further processing to remove impurities and is typically white in color.                                                                                                                                                               |
| **Production**      | Sugar production figures reported by active sugar mills and refineries. See the SRA directories of [Sugar Mills](https://www.sra.gov.ph/stakeholders/directorySugarMills) and [Sugar Refineries](https://www.sra.gov.ph/stakeholders/directorySugarRefineries). |
| **Withdrawals**     | Sugar released from warehouses, based on withdrawal reports submitted by active sugar mills and refineries.                                                                                                                                                     |
| **LKg**             | A unit equivalent to one 50-kilogram bag of sugar.                                                                                                                                                                                                              |
| **MT**              | Metric ton, equivalent to 1,000 kilograms.                                                                                                                                                                                                                      |
| **“A” Sugar**       | Sugar classified for export to the United States under the US sugar quota.                                                                                                                                                                                      |
| **“B” Sugar**       | Sugar classified for domestic sale, use, and circulation in the Philippines.                                                                                                                     
| **“D” Sugar** | Sugar classified for export to the world market, excluding exports to the United States. |                                                                                                                                |
| **Millsite Price**  | The price of sugar at the mill level,  reported in Philippine pesos per LKg.                                                                                                                      |
| **Wholesale Market Price** | The average wholesale prices (Php/LKg) of raw and refined sugar in Metro Manila.|


## Data Sources and Processing

The primary data source is the Sugar Regulatory Administration (SRA) historical sugar statistics: https://www.sra.gov.ph/historicalStatistics/index

The source data is available to the public in PDF format. Tables from these reports were extracted and processed using [`tabula-py`](https://tabula-py.readthedocs.io/) before being cleaned, standardized, and prepared for visualization in marimo.

Refined sugar production and withdrawal figures originally reported in LKg were converted to metric tons using the following formula:

```text
Metric tons = LKg × 50 ÷ 1,000
```

## Limitations

Users should consider the following limitations when interpreting the data from SugarStatsPH:

1. **PDF extraction and data quality**

   The source data were extracted from PDF reports using `tabula-py`. Because PDF tables are not always consistently formatted, some values may have been extracted, interpreted, or cleaned incorrectly.

2. **Unit conversion**

   Refined sugar production and withdrawal figures were converted from 50-kilogram bags, or LKg, to metric tons. Small differences may occur because of rounding.

3. **Imported refined sugar**

   The source data do not clearly indicate whether refined sugar withdrawal data included refined sugar imported from other countries into the Philippines.

4. **Missing “A” Export millsite prices**

   “A” Export millsite prices for Crop Years 2023–2024 and 2024–2025 were not published in the historical statistics available on the SRA website, despite reports that the Philippines exported sugar to the United States during these periods. See  [Philippine Daily Inquirer report](https://business.inquirer.net/568497/for-3rd-straight-year-ph-exports-sugar-to-us).

5. **Molasses and bioethanol**

   The analysis does not account for the effects of molasses and bioethanol production on sugarcane allocation, production volumes, or market conditions.

6. **Geographic coverage of retail prices**

   Average retail sugar prices are based on the available monthly average prices for raw and refined sugar in Metro Manila. These figures may not represent prices in other regions of the Philippines.

7. **Interpretation of supply conditions**

   Differences between production and withdrawals should not automatically be interpreted as proof of an undersupply or oversupply. Beginning inventories, imports, exports, reserve stocks, reclassifications, reporting schedules, and other market factors may also affect sugar availability.
   
8. **Other sugar market classifications**

   The Philippine sugar industry also uses “C” and “E” classifications. “C” sugar refers to reserve sugar, which includes imported sugar that is initially classified as “C” and cannot be sold, used, or circulated in the Philippines unless it is reclassified as “B” domestic sugar. “E” sugar refers to sugar allocated for accredited food processors and manufacturers producing sugar-based products for export. For the purposes of SugarStatsPH, only the “A,” “B,” and “D” classifications that appear in the processed historical reports are presented.


The information presented in SugarStatsPH should therefore be used as a reference for exploration and further analysis rather than as the sole basis for policy, financial, or commercial decisions.

## Contributor Guide

Contributions, corrections, and suggestions are welcome.

You may fork this repository and modify or improve any part of the project. Contributions may include:

* Correcting data extraction or cleaning errors
* Adding missing historical reports
* Improving documentation
* Adding new visualizations or analytical features
* Improving accessibility and user experience
* Reporting inconsistencies between the app and the original SRA reports

To propose a change, you may open an issue or submit a pull request through this repository.

For questions or error reports, email me at [romaisablbgn@gmail.com](mailto:romaisablbgn@gmail.com).
