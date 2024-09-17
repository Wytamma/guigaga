
from typing import Callable, Optional, Union

import click

from guigaga.interface import InterfaceBuilder
from guigaga.themes import Theme


def gui(
    name: Optional[str] = None,
    command_name: str = "gui",
    message: str = "Open Gradio GUI.",
    *,
    theme: Theme = Theme.soft,
    hide_not_required: bool = False,
    allow_file_download: bool = False,
) -> Callable:
    """
    A decorator to attach a GUI command to a Click app (either a Group or Command).
    """
    def decorator(app: Union[click.Group, click.Command]):
        @click.pass_context
        @click.option(
            "--share",
            is_flag=True,
            default=False,
            required=False,
            help="Share the GUI over the internet."
        )
        def wrapped_gui(ctx, share: bool, *args, **kwargs):  # noqa: ARG001
            """
            Initialize the interface and launch it directly, bypassing the need for a separate class.
            """
            # Build the interface using InterfaceBuilder
            interface = InterfaceBuilder(
                app,
                app_name=name,
                command_name=command_name,
                theme=theme,
                hide_not_required=hide_not_required,
                allow_file_download=allow_file_download,
            ).interface

            # Launch the interface with optional sharing
            interface.queue().launch(share=share)

        # Handle case where app is a click.Group or a click.Command
        if isinstance(app, click.Group):
            app.command(name=command_name, help=message)(wrapped_gui)
        else:
            new_group = click.Group()
            new_group.add_command(app)
            new_group.command(name=command_name, help=message)(wrapped_gui)
            return new_group

        return app

    return decorator
