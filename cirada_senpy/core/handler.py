import pandas as pd
from query import Query
from collector import Collector
from tqdm import tqdm


class Handler:
    def __init__(self, input_data: pd.DataFrame):
        """

        :param input_data: *** This must be the path to
        """
        self.input_data = input_data
        self.input_data = self.input_data.where(pd.notnull(self.input_data), None)

    def submit(self):
        response = []
        for index, row in tqdm(self.input_data.iterrows()):
            query = Query(20, 20, ra=row["ra"], dec=row["dec"], source_name=row["name"])
            res = query.submit()
            response.append(res)
        response = pd.concat(response, ignore_index=True)
        return response

    def download(self, submited_data: pd.DataFrame):
        collector = Collector(submited_data, output_path="/tmp")
        collector.download()


if __name__ == "__main__":
    from io import StringIO
    example_file = """ra,dec,name
    162.338077, -0.66805,
    ,,M87
    '00 42 30, +41 12 00'
    05h 35m 18s, -05d 23m 0s,Orion
    """
    test_data = StringIO(example_file)
    input_data = pd.read_csv(test_data)
    handler = Handler(input_data)
    files = handler.submit()
    handler.download(files)

