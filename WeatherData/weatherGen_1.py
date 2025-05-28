import pandas as pd
import os
import diyepw

years = list(range(1970,2025,1))

print(years)


for year in years:
    diyepw.create_amy_epw_files_for_years_and_wmos(
    [year],
    [725090],
    max_records_to_interpolate=10,
    max_missing_amy_rows=300,
    allow_downloads=True,
    amy_epw_dir='D:/Boston'
    )