import click

import guigaga as ga


def read_fasta(input_file):
  sequences = {}
  with open(input_file) as f:
      for line in f:
          if line.startswith(">"):
              header = line.strip()[1:]
              sequences[header] = ""
          else:
              sequences[header] += line.strip()
  return sequences

def write_fasta(output_file, sequences):
    with open(output_file, "w") as f:
        for header, sequence in sequences.items():
            f.write(f">{header}\n{sequence}\n")

@ga.gui()
@click.command()
@click.argument("input_fasta",  type=ga.Upload(exists=True))
@click.argument("output_fasta", type=ga.Download("reverse_complement.fa"))
def reverse_complement(input_fasta: str, output_fasta: str):
    """This script computes the reverse complement of a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    sequences = read_fasta(input_fasta)
    for header, sequence in sequences.items():
        try:
            sequences[header] = "".join(complement[base] for base in reversed(sequence))
        except KeyError as e:
            msg = f"Invalid base found in sequence '{header}': {e}"
            raise ValueError(msg) from KeyError
    write_fasta(output_fasta, sequences)

if __name__ == "__main__":
    reverse_complement()
