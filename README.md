# CIRADA SENPY
**CIRADA** cutout **SE**rvice i**N** **PY**thon

# Getting started

An example of input can be the `input_example.csv`:

| ra          | dec         | name  |
|-------------|-------------|-------|
| 162.338077  | -0.66805    |       |
|             |             | M87   |
| '00 42 30   | +41 12 00'  |       |
| 05h 35m 18s | -05d 23m 0s | Orion |



```python
from cirada_senpy.core import download_file

download_file(input_example,
              "/tmp/my_fits")
```

If you want open a tgz fits, just use:

```python
from cirada_senpy.core import open_fits_tgz
data_path = "/tmp/my_fits/Orion.tgz"
fits_list = open_fits_tgz(data_path)
```
