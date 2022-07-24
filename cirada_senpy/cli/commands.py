from cirada_senpy.core import download_file

import click


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="It's True doesn't download already existing records",
)
def download(input_path: str, output_path: str, force: bool):
    download_file(input_path, output_path, force)


if __name__ == "__main__":
    cli()
