from typing import Callable, Optional, Union

import click

from guigaga.interface import InterfaceBuilder
from guigaga.themes import Theme


def update_launch_kwargs_from_cli(ctx, launch_kwargs, cli_mappings):
    """
    Update launch_kwargs with CLI options that differ from their defaults.

    Args:
        ctx: Click context object containing the command parameters and options.
        launch_kwargs: Dictionary to update with CLI-specified values.
        cli_mappings: Dictionary mapping CLI option names to their corresponding launch_kwargs keys.
    """
    for param in ctx.command.params:
        param_name = param.name
        if param_name in cli_mappings and ctx.params[param_name] != param.default:
            launch_kwargs[cli_mappings[param_name]] = ctx.params[param_name]

def gui(
    name: Optional[str] = None,
    command_name: str = "gui",
    message: str = "Open Gradio GUI.",
    *,
    theme: Theme = Theme.soft,
    hide_not_required: bool = False,
    allow_file_download: bool = False,
    launch_kwargs: Optional[dict] = None,
    queue_kwargs: Optional[dict] = None,
    catch_errors: bool = True,
) -> Callable:
    if launch_kwargs is None:
        launch_kwargs = {}
    if queue_kwargs is None:
        queue_kwargs = {}

    def decorator(app: Union[click.Group, click.Command]):
        @click.pass_context
        @click.option(
            "--share",
            is_flag=True,
            default=False,
            required=False,
            help="Share the GUI over the internet."
        )
        @click.option(
            "--host",
            type=str,
            default="127.0.0.1",
            required=False,
            help="Host address to use for sharing the GUI."
        )
        @click.option(
            "--port",
            type=int,
            default=7860,
            required=False,
            help="Port number to use for sharing the GUI."
        )
        def wrapped_gui(ctx, share, host, port):  # noqa: ARG001
            # Mapping of CLI option names to launch_kwargs keys
            cli_mappings = {
                "share": "share",
                "host": "server_name",
                "port": "server_port",
            }

            # Update launch_kwargs based on CLI inputs
            update_launch_kwargs_from_cli(ctx, launch_kwargs, cli_mappings)

            # Build the interface using InterfaceBuilder
            builder = InterfaceBuilder(
                app,
                app_name=name,
                command_name=command_name,
                click_context=click.get_current_context(),
                theme=theme,
                hide_not_required=hide_not_required,
                allow_file_download=allow_file_download,
                catch_errors=catch_errors,
            )

            # Launch the interface with optional sharing
            builder.interface.queue(**queue_kwargs).launch(**launch_kwargs, app_kwargs={"docs_url": "/docs"})

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
