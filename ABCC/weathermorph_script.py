import csv
import os
import datetime
from datetime import timedelta
import re
import psychrolib
import math
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherMorphProcessor:
    def __init__(self, base_dir, epw_csv_path, master_csv_path):
        self.base_dir = Path(base_dir)
        self.epw_csv_path = Path(epw_csv_path)
        self.master_csv_path = Path(master_csv_path)
        self.output_data = []
        self.failures = []
        self.morph_df = None

        self._validate_paths()
        psychrolib.SetUnitSystem(psychrolib.SI)

    def _validate_paths(self):
        if not self.base_dir.exists():
            raise FileNotFoundError(f"Base directory not found: {self.base_dir}")
        if not self.epw_csv_path.exists():
            raise FileNotFoundError(f"EPW CSV file not found: {self.epw_csv_path}")
        if not self.master_csv_path.exists():
            raise FileNotFoundError(f"Master CSV file not found: {self.master_csv_path}")

    def extract_wmo_number(self, lines):
        for line in lines:
            if 'WMO Station' in line:
                match = re.search(r'\b(\d{6})\b', line)
                if match:
                    return match.group(1)
        return 'N/A'

    def parse_extreme_periods(self, lines):
        cold_line = next((l for l in lines if 'Extreme Cold Week Period selected' in l), None)
        hot_line = next((l for l in lines if 'Extreme Hot Week Period selected' in l), None)
        if not cold_line or not hot_line:
            raise ValueError("No extreme period lines found")

        cold_range = cold_line.split(': ')[1].split(', ')[0]
        hot_range = hot_line.split(': ')[1].split(', ')[0]

        c_start, c_end = [d.strip() for d in cold_range.split(':')]
        h_start, h_end = [d.strip() for d in hot_range.split(':')]

        c_start = (datetime.datetime.strptime(c_start, '%b %d') - timedelta(days=1)).strftime('%m/%d')
        c_end = datetime.datetime.strptime(c_end, '%b %d').strftime('%m/%d')
        h_start = (datetime.datetime.strptime(h_start, '%b %d') - timedelta(days=1)).strftime('%m/%d')
        h_end = datetime.datetime.strptime(h_end, '%b %d').strftime('%m/%d')

        return {'winter_start': c_start, 'winter_end': c_end, 'summer_start': h_start, 'summer_end': h_end}

    def process_stat_file(self, stat_file_path):
        try:
            with open(stat_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            wmo = self.extract_wmo_number(lines)
            periods = self.parse_extreme_periods(lines)

            self.output_data.append([
                wmo, periods['winter_start'], periods['winter_end'],
                periods['summer_start'], periods['summer_end']
            ])
            logger.info(f"✅ Processed {stat_file_path.name}")

        except Exception as e:
            logger.error(f"⚠️ Error processing {stat_file_path.name}: {e}")
            self.failures.append(str(stat_file_path.name))

    def load_epw_data(self):
        logger.info("Loading EPW data...")
        with open(self.epw_csv_path, 'r') as f:
            content = f.read()
            pattern = r"Date.*\nDate.*\n"
            prelines = len(re.split(pattern, content)[0].splitlines()) + 1

        df = pd.read_csv(self.epw_csv_path, skiprows=prelines, encoding='latin1')
        df['Date'] = df['Date'].str[5:]
        df = df.set_index(['Date', 'HH:MM'])

        df.index = df.index.set_levels([
            pd.to_datetime(df.index.levels[0], format='%m/%d').strftime('%m/%d'),
            df.index.levels[1]
        ])
        df = df.sort_index()
        return df[["Dry Bulb Temperature {C}", "Dew Point Temperature {C}"]]

    def compute_morphing_factors(self, summer_start, winter_start, elev, s_wb, s_db, w_wb, w_db):
        p = psychrolib.GetStandardAtmPressure(float(elev))
        s_dp = psychrolib.GetTDewPointFromTWetBulb(float(s_db), float(s_wb), p)
        w_dp = psychrolib.GetTDewPointFromTWetBulb(float(w_db), float(w_wb), p)

        if self.morph_df is None:
            self.morph_df = self.load_epw_data()

        summer_dates = [(pd.to_datetime(summer_start, format='%m/%d') + pd.Timedelta(days=n)).strftime('%m/%d') for n in range(7)]
        winter_dates = [(pd.to_datetime(winter_start, format='%m/%d') + pd.Timedelta(days=n)).strftime('%m/%d') for n in range(7)]

        s_df = self.morph_df.loc[self.morph_df.index.get_level_values(0).isin(summer_dates)]
        w_df = self.morph_df.loc[self.morph_df.index.get_level_values(0).isin(winter_dates)]

        assert len(s_df) == 168 and len(w_df) == 168

        phase = [math.pi * h / 168 for h in range(168)]

        def iterate_delta(target, series, fn):
            delta = target - series.mean()
            for _ in range(100):
                morphed = series + delta * np.sin(phase)
                actual = fn(morphed)
                if abs(target - actual) < 0.01:
                    break
                delta += 0.1 * (target - actual)
            return round(delta, 2)

        return (
            iterate_delta(float(s_db), s_df["Dry Bulb Temperature {C}"], max),
            iterate_delta(s_dp, s_df["Dew Point Temperature {C}"], max),
            iterate_delta(float(w_db), w_df["Dry Bulb Temperature {C}"], min),
            iterate_delta(w_dp, w_df["Dew Point Temperature {C}"], min)
        )

    def process_all_stat_files(self):
        stat_files = list(self.base_dir.glob('*.stat'))
        logger.info(f"Found {len(stat_files)} .stat files")
        for file in stat_files:
            self.process_stat_file(file)

        with open(self.base_dir / 'outage_periods.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['WMO_Number', 'Cold_Start', 'Cold_End', 'Hot_Start', 'Hot_End'])
            writer.writerows(self.output_data)

    def append_to_master_csv(self):
        master_df = pd.read_csv(self.master_csv_path)
        morph_records = []

        for row in self.output_data:
            wmo, c_start, c_end, h_start, h_end = row
            try:
                match = master_df.loc[master_df['WMO_Number'] == int(wmo)].iloc[0]

                elev = match['weather_Elev [m]']
                s_db = match['weather_DB Max [c] (20)']
                s_wb = match['weather_WB Max [c] (20)']
                w_db = match['weather_DB Min [c] (10)']
                w_wb = match['weather_WB Min [c] (10)']

                summer_db, summer_dp, winter_db, winter_dp = self.compute_morphing_factors(
                h_start, c_start, elev, s_wb, s_db, w_wb, w_db
            )

                morph_records.append({
                    'WMO_Number': int(wmo),
                    'Cold_Start': c_start,
                    'Cold_End': c_end,
                    'Hot_Start': h_start,
                    'Hot_End': h_end,
                    'Summer_DB_Factor': summer_db,
                    'Summer_DP_Factor': summer_dp,
                    'Winter_DB_Factor': winter_db,
                    'Winter_DP_Factor': winter_dp
            })

            except Exception as e:
                logger.error(f"Error processing WMO {wmo}: {e}")
                self.failures.append(wmo)

    # Create DataFrame and merge with master
        morph_df = pd.DataFrame(morph_records)
        merged_df = pd.merge(master_df, morph_df, on='WMO_Number', how='left')

        output_path = self.base_dir / 'master_with_morphing.csv'
        merged_df.to_csv(output_path, index=False)
    
        logger.info(f" New merged CSV saved to: {output_path}")
        logger.info(f"Successfully processed {len(morph_records)} WMO entries.")

        if self.failures:
            logger.warning(f" Failures for WMO Numbers: {self.failures}")
    
        return output_path


# Main execution
if __name__ == "__main__":
    CONFIG = {
        'base_dir': 'A:/PHIUS/abcc_weatherMorph',
        'epw_csv': 'A:/PHIUS/abcc_weatherMorph/USA_GA_Brunswick-Golden.Isles.AP.722136_TMY3EPW.csv',
        'master_csv': 'A:/PHIUS/mastercsv.csv'
    }

    try:
        processor = WeatherMorphProcessor(CONFIG['base_dir'], CONFIG['epw_csv'], CONFIG['master_csv'])
        processor.process_all_stat_files()
        result_path = processor.append_to_master_csv()
        logger.info(f" All done! Morphing output at: {result_path}")

    except Exception as e:
        logger.error(f" Fatal error: {e}")
