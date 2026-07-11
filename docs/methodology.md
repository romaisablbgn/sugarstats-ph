# Methodology

SugarStatsPH extracts Philippine public sugar historical statistics from Sugar Regulatory Administration website (https://www.sra.gov.ph/historicalStatistics/index) PDF reports using tabula-py. The extraction step converts PDF tables into raw CSV files. Because PDF extraction does not understand the domain meaning of sugar statistics, the project applies separate cleaning scripts for each document type.

The project separates product type, sugar class, unit, and market/price level to avoid mixing different concepts. Regulatory classifications such as "A", "B", "C", "D", and "E" are not treated as product types. They indicate allocation or market classification.

For millsite prices, "A" Export, "B" Domestic, "D" World Market, and Composite Price are treated as PHP/LKg, while Molasses is treated as PHP/MT. Months marked as Terminated are retained in the processed data for transparency but excluded from analytical summaries.

Overlapping crop years from different source periods are deduplicated by keeping records from the newer source period.