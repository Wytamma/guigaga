import click

from guigaga import gui


# Click command line interface
@gui()
@click.command()
@click.argument("sequence",  type=str)
def reverse_complement(sequence):
    """This script computes the reverse complement of a DNA sequence."""
    # Define the complement dictionary
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
    # Convert the sequence to upper case to handle both lower and upper case inputs
    sequence = sequence.upper()
    # Generate the reverse complement
    result = "".join(complement[base] for base in reversed(sequence))
    # Print the result
    click.echo(result)

# Entry point for the command line app
if __name__ == "__main__":
    reverse_complement()
