from ..io.data_file import read_file
from .collector import Collector
from .query import Query
from tqdm import tqdm

import os.path
import pandas as pd


class Handler:
    def __init__(
        self, input_path_file: str, output_dir: str = "/tmp", force: bool = False
    ):
        """
        :param input_path_file: The path to the file (csv, parquet or pickle extension)
        :param output_dir: The path to the directory where the downloaded files will be write
        """
        self.input_path_file = input_path_file
        self.output_dir = output_dir
        self.data = self._open_file()
        self.force = force

    def _verify_io(self) -> bool:
        """

        :return:
        """
        if not os.path.exists(self.input_path_file):
            raise Exception(f"The input file {self.input_path_file} does not exists")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print("The output doesn't exists but I created the folder for you :)")
        return True

    def _open_file(self) -> pd.DataFrame:
        """

        :return:
        """
        if self._verify_io():
            data = read_file(self.input_path_file)
            data = data.where(pd.notnull(data), None)
            return data

    def _submit(self):
        """

        :return:
        """
        response = []
        progress_bar = tqdm(self.data.iterrows())
        for index, row in progress_bar:
            progress_bar.set_description(
                f"Querying for {row['ra']}, {row['dec']} / {row['name']}"
            )
            query = Query(20, 20, ra=row["ra"], dec=row["dec"], source_name=row["name"])
            if self.force:
                tmp_output_name = (
                    query.source_name
                    if query.source_name
                    else f"{query.ra} {query.dec}"
                )
                tmp_output_name = f"{tmp_output_name}.tgz"
                tmp_output_path = os.path.join(self.output_dir, tmp_output_name)
                if os.path.exists(tmp_output_path):
                    print(f"{tmp_output_path} already exists")
                    continue
            res = query.submit()
            response.append(res)
        if len(response) == 0:
            return pd.DataFrame()
        response = pd.concat(response, ignore_index=True)
        return response

    def _download(self, downloadable_data: pd.DataFrame):
        """

        :return:
        """
        collector = Collector(downloadable_data, output_path=self.output_dir)
        collector.download()

    def download(self):
        """

        :return:
        """
        if self._verify_io():
            payloads = self._submit()
            if not payloads.empty:
                self._download(payloads)
