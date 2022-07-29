import os
import pandas as pd

CSV = ["csv", "txt"]
PARQUET = ["parquet"]
PICKLE = ["pkl", "pickle"]

pandas_read = {"csv": pd.read_csv, "parquet": pd.read_parquet, "pickle": pd.read_pickle}

pandas_write = {"csv": "to_csv", "parquet": "to_parquet", "pickle": "to_pickle"}


def get_format(extension: str) -> str:
    """
    Get format of the file. This project support `csv`, `parquet` or `pickle` extension
    :param extension: the format that follows to a dot in a regular file
    :return: format of the file
    """
    file_format = None
    if extension in CSV:
        file_format = "csv"
    if extension in PARQUET:
        file_format = "parquet"
    if extension in PICKLE:
        file_format = "pickle"

    if file_format is None:
        raise Exception(f"*.{extension} extension not supported")
    return file_format


def read_file(path: str, file_format: str = None, **kwargs) -> pd.DataFrame:
    """
    Read any file with `csv`, `parquet` or `pickle` extension
    :param path: Path to the file
    :param file_format: argument that indicates the format
    :param kwargs: arguments to specific io operations
    :return: Data in a pandas DataFrame
    """
    if not os.path.exists(path):
        raise FileNotFoundError("Path not exists")

    filename = os.path.basename(path)
    extension = filename.split(".")[-1]

    if file_format is None:
        file_format = get_format(extension)

    df = pandas_read[file_format](path, **kwargs)
    return df


def write_file(df: pd.DataFrame, path: str, file_format: str = None, **kwargs) -> None:
    """
    Write a pandas DataFrame in specific formats.
    :param df: Data in a pandas DataFrame
    :param path: Output path
    :param file_format: Format of the output file
    :param kwargs: Data in a pandas DataFrame
    :return: None
    """
    if os.path.isdir(path):
        raise Exception("Path has to be a directory")

    filename = os.path.basename(path)
    extension = filename.split(".")[-1]

    if file_format is None:
        file_format = get_format(extension)

    writer = getattr(df, pandas_write[file_format])
    writer(path, **kwargs)
