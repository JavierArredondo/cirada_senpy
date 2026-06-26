"""Batch orchestration: read a target table, fetch cutouts per survey, write FITS."""
import glob
import os.path
from typing import List, Optional

import astropy.units as u
import pandas as pd
from tqdm import tqdm

from ..io.data_file import read_file
from .coords import parse_position, source_label
from .surveys import DEFAULT_SURVEYS, fetch_survey, normalize_survey


class Handler:
    def __init__(
        self,
        input_path_file: str,
        output_dir: str = "/tmp",
        surveys: Optional[List[str]] = None,
        radius_arcmin: float = 3.0,
        overwrite: bool = False,
    ):
        """
        :param input_path_file: Path to the target table (csv, parquet or pickle).
        :param output_dir: Directory where cutout FITS files are written.
        :param surveys: Survey keys to fetch (defaults to VLASS, NVSS, FIRST).
        :param radius_arcmin: Cutout radius in arcminutes.
        :param overwrite: Re-fetch cutouts that already exist (default: skip).
        """
        self.input_path_file = input_path_file
        self.output_dir = output_dir
        self.surveys = [normalize_survey(s) for s in (surveys or DEFAULT_SURVEYS)]
        self.radius = radius_arcmin * u.arcmin
        self.overwrite = overwrite
        self.data = self._open_file()

    def _verify_io(self) -> bool:
        if not os.path.exists(self.input_path_file):
            raise FileNotFoundError(
                f"The input file {self.input_path_file} does not exist"
            )
        os.makedirs(self.output_dir, exist_ok=True)
        return True

    def _open_file(self) -> pd.DataFrame:
        self._verify_io()
        data = read_file(self.input_path_file)
        for column in ("ra", "dec", "name"):
            if column not in data.columns:
                data[column] = None
        return data.where(pd.notnull(data), None)

    def _write(self, hduls: list, label: str, survey: str) -> List[str]:
        paths = []
        for index, hdul in enumerate(hduls):
            suffix = f"_{index + 1}" if len(hduls) > 1 else ""
            out_path = os.path.join(self.output_dir, f"{label}_{survey}{suffix}.fits")
            # output_verify="ignore": some archive headers (e.g. FIRST via
            # SkyView) carry non-ASCII commentary cards that are unfixable but
            # harmless; "ignore" writes them as-is instead of raising.
            hdul.writeto(out_path, overwrite=True, output_verify="ignore")
            paths.append(out_path)
        return paths

    def download(self) -> List[str]:
        self._verify_io()
        written: List[str] = []
        failed: List[tuple] = []

        progress_bar = tqdm(self.data.iterrows(), total=len(self.data))
        for _, row in progress_bar:
            try:
                position = parse_position(row["ra"], row["dec"], row["name"])
            except Exception as error:
                target = row["name"] or f"{row['ra']},{row['dec']}"
                failed.append((target, "parse", str(error)))
                continue

            label = source_label(row["ra"], row["dec"], row["name"], position)
            for survey in self.surveys:
                progress_bar.set_description(f"{label} / {survey}")
                existing = glob.glob(
                    os.path.join(self.output_dir, f"{label}_{survey}*.fits")
                )
                if existing and not self.overwrite:
                    continue
                try:
                    hduls = fetch_survey(position, survey, self.radius)
                    if not hduls:
                        failed.append((label, survey, "no coverage"))
                        continue
                    written += self._write(hduls, label, survey)
                except Exception as error:
                    failed.append((label, survey, str(error)))

        if failed:
            print(f"\n{len(failed)} fetch(es) failed or had no coverage:")
            for target, survey, message in failed:
                print(f"  - {target} [{survey}]: {message}")
        print(f"\nWrote {len(written)} FITS file(s) to {self.output_dir}")
        return written
