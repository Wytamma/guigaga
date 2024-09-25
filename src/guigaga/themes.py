import enum

import gradio as gr


class Theme(enum.Enum):
    """
    An enumeration representing different themes available in gradio.

    Attributes:
      base (gr.themes.Base): The base theme.
      default (gr.themes.Default): The default theme.
      glass (gr.themes.Glass): The glass theme.
      monochrome (gr.themes.Monochrome): The monochrome theme.
      soft (gr.themes.Soft): The soft theme.

    Note:
      This class is a part of the 'enum' module. It is used for creating enumerations, which are a set of symbolic names (members) bound to unique, constant values. The members of an enumeration can be compared with these symbolic names.

    Examples:
      >>> print(Theme.base)
      Theme.base
      >>> print(Theme.default)
      Theme.default
      >>> print(Theme.glass)
      Theme.glass
      >>> print(Theme.monochrome)
      Theme.monochrome
      >>> print(Theme.soft)
      Theme.soft
    """
    base = gr.themes.Base()
    default = gr.themes.Default()
    glass = gr.themes.Glass()
    monochrome = gr.themes.Monochrome()
    soft = gr.themes.Soft()
