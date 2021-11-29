import os.path

import pandas as pd
from .query import Query
from .collector import Collector
from ..io.data_file import read_file
from tqdm import tqdm


class Handler:
    def __init__(self, input_path_file: str, output_dir: str = "/tmp"):
        """
        :param input_path_file: The path to the file (csv, parquet or pickle extension)
        :param output_dir: The path to the directory where the downloaded files will be write
        """
        self.input_path_file = input_path_file
        self.output_dir = output_dir
        self.data = None

    def _verify_io(self) -> bool:
        """

        :return:
        """
        if not os.path.exists(self.input_path_file):
            raise Exception(f"The input file {self.input_path_file} does not exists")
        if not os.path.isdir(self.output_dir):
            raise Exception(f"The output directory {self.input_path_file} does not exists")
        return True

    def _open_file(self) -> None:
        """

        :return:
        """
        data = read_file(self.input_path_file)
        data = data.where(pd.notnull(data), None)
        self.data = data

    def _submit(self):
        """

        :return:
        """
        response = []
        for index, row in tqdm(self.data.iterrows()):
            query = Query(20, 20, ra=row["ra"], dec=row["dec"], source_name=row["name"])
            res = query.submit()
            response.append(res)
        response = pd.concat(response, ignore_index=True)
        return response

    def _download(self):
        """

        :return:
        """
        collector = Collector(self.data, output_path=self.output_dir)
        collector.download()

    def download(self):
        """

        :return:
        """
        if self._verify_io():
            self._submit()
            self._download()
