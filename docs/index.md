---
title: Home
---
# GUIGAGA <img src='https://guigaga.wytamma.com/assets/android-chrome-192x192.png' align="right" height="210" />

[![PyPI - Version](https://img.shields.io/pypi/v/guigaga.svg)](https://pypi.org/project/guigaga)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/guigaga.svg)](https://pypi.org/project/guigaga)

-----

## Installation

```console
pip install guigaga
```

## Usage

Simply decorate your script with the `@gui()` decorator to add a GUI to your click CLI.

```python
import click
from guigaga import gui


@gui()
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
```

Run the script with the `gui` argument to open the [gradio](https://www.gradio.app/) powered GUI:

```console
$ python app.py gui
```

![GUI](https://raw.githubusercontent.com/Wytamma/GUIGAGA/refs/heads/master/images/reverse_complement_gui.png)

Add it still works as a command line script:
```console
$ python app.py reverse_complement ATGC
GCAT
```

Check out the live demo [here](https://colab.research.google.com/gist/Wytamma/d2856c9258258f354e99c7eedffe6b07/guigaga.ipynb).

## License

`guigaga` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license and was heavily inspired by [trogon](https://github.com/Textualize/trogon).

##
All We Need Is GUI Ga Ga!