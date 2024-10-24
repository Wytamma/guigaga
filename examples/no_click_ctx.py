import click

from guigaga.guigaga import GUIGAGA


@click.command()
@click.argument("sequence",  type=str)
def reverse_complement(sequence):
    """This script computes the reverse complement of a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    sequence = sequence.upper()
    result = "".join(complement[base] for base in reversed(sequence))
    click.echo(result)

demo = GUIGAGA(reverse_complement)
demo.launch()
