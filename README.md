# CIRADA SENPY
The **CIRADA** cutout **SE**rvice i**N** **PY**thon is a simple package to download cutouts in batches from [CIRADA](http://cutouts.cirada.ca/) portal.

# Getting started

First install this repo with easy-(informal)-way: `pip install .`.

An example of input can be the `input_example.csv`:

| ra          | dec         | name  |
|-------------|-------------|-------|
| 162.338077  | -0.66805    |       |
|             |             | M87   |
| '00 42 30   | +41 12 00'  |       |
| 05h 35m 18s | -05d 23m 0s | Orion |


If you want to use the CLI of CIRADA SENPY to download a dataset:

```bash
senpy download <path_to_file> <path_to_output>
```

Where `path_to_file` can be a `.csv`, `.parquet` or a `.pkl`. Also, you can add a flag to ignore the download of existing records in your output path.

```bash
senpy download <path_to_file> <path_to_output> --force
```

If you want to use Python to manage the package:

```python
from cirada_senpy.core import download_file

download_file("input_example.csv",
              "/tmp/my_fits")
```

If you want open a tgz fits, just use:

```python
from cirada_senpy.core import open_fits_tgz
data_path = "/tmp/my_fits/Orion.tgz"
fits_list = open_fits_tgz(data_path)
```
