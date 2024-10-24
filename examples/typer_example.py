import typer

app = typer.Typer()

@app.command()
def reverse_complement(sequence):
    """This script computes the reverse complement of a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    sequence = sequence.upper()
    result = "".join(complement[base] for base in reversed(sequence))
    typer.echo(result)

@app.command()
def gui():
    from guigaga.guigaga import GUIGAGA  # lazy load

    GUIGAGA(typer.main.get_group(app)).launch()

if __name__ == "__main__":
    app()
