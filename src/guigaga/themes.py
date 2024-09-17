import enum

import gradio as gr


class Theme(enum.Enum):
    base = gr.themes.Base()
    default = gr.themes.Default()
    glass = gr.themes.Glass()
    monochrome = gr.themes.Monochrome()
    soft = gr.themes.Soft()
