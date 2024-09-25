import click

from guigaga import gui


@gui(catch_errors=False)
@click.command()
@click.argument("sequence",  type=str)
@click.argument("sequence2", type=str)
@click.pass_context
def reverse_complement(ctx, sequence, sequence2):
    """This script computes the reverse complement of a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
    sequence = sequence.upper()
    result = "".join(complement[base] for base in reversed(sequence))
    click.echo(result)

if __name__ == "__main__":
    reverse_complement()
