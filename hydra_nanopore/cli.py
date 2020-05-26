"""Console script for hydra_nanopore."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for hydra_nanopore."""
    click.echo("Replace this message by putting your code into "
               "hydra_nanopore.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
