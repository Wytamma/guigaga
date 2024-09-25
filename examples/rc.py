import click

import guigaga


@guigaga.gui()
@click.command()
@click.argument("sequence",  type=str)
def reverse_complement(sequence):
    """This script computes the reverse complement of a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    sequence = sequence.upper()
    result = "".join(complement[base] for base in reversed(sequence))
    click.echo(result)

if __name__ == "__main__":
    reverse_complement()
