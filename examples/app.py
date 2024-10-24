import click

from guigaga import gui


@gui(name="Bioinformatics tools")
@click.group()
def home():
    """
    This is the homepage of the bioinformatics CLI.
    ![](https://picsum.photos/200)
    """
    pass


@home.command()
@click.argument("sequence",  type=str)
def reverse_complement(sequence):
    """
    This script computes the reverse complement of a DNA sequence.
    """
    complement = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    sequence = sequence.upper()
    result = "".join(complement[base] for base in reversed(sequence))
    click.echo(result)

@home.command()
@click.argument("sequence",  type=str)
def rna2dna(sequence):
    """
    This script converts an RNA sequence to a DNA sequence.
    """
    result = sequence.replace("U", "T")
    click.echo(result)

if __name__ == "__main__":
    home()
