from typing import Callable, Optional


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
    message: str = "Launch the GUI.",
    *,
    theme: str = "soft",
    hide_not_required: bool = False,
    allow_file_download: bool = False,
    launch_kwargs: Optional[dict] = None,
    queue_kwargs: Optional[dict] = None,
    catch_errors: bool = True,
) -> Callable:
    """
    Creates a decorator for a click command or group to add a GUI interface.

    Args:
      name (Optional[str]): The name of the application. Defaults to None.
      command_name (str): The name of the command to open the GUI. Defaults to "gui".
      message (str): The message to display when the GUI is opened. Defaults to "Open Gradio GUI."
      theme (GradioTheme|str): The theme to use for the GUI. Defaults to Soft.
      hide_not_required (bool): Whether to hide options that are not required. Defaults to False.
      allow_file_download (bool): Whether to allow file downloads. Defaults to False.
      launch_kwargs (Optional[dict]): Additional keyword arguments to pass to the launch method. Defaults to None.
      queue_kwargs (Optional[dict]): Additional keyword arguments to pass to the queue method. Defaults to None.
      catch_errors (bool): Whether to catch and display errors in the GUI. Defaults to True.

    Returns:
      Callable: A decorator that can be used to add a GUI to a click command or group.
    """
    if launch_kwargs is None:
        launch_kwargs = {}
    if queue_kwargs is None:
        queue_kwargs = {}

    def decorator(app):
        """
        A decorator that adds a GUI to a click command or group.

        Args:
            app (Union[click.Group, click.Command]): The click command or group to add the GUI to.

        Returns:
            Union[click.Group, click.Command]: The click command or group with the added GUI.
        """
        import click


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
            """
            A click command that launches the GUI.

            Args:
                ctx (click.Context): The click context.
                share (bool): Whether to share the GUI over the internet.
                host (str): The host address to use for sharing the GUI.
                port (int): The port number to use for sharing the GUI.

            Side Effects:
                Modifies the launch_kwargs dictionary based on the CLI inputs.
                Launches the GUI.

            Notes:
                This function is decorated with click.pass_context, and click.option for "share", "host", and "port".
            """
            from guigaga.guigaga import GUIGAGA

            # Mapping of CLI option names to launch_kwargs keys
            cli_mappings = {
                "share": "share",
                "host": "server_name",
                "port": "server_port",
            }

            # Update launch_kwargs based on CLI inputs
            update_launch_kwargs_from_cli(ctx, launch_kwargs, cli_mappings)

            # Build the interface using GUIGAGA
            GUIGAGA(
                app,
                app_name=name,
                command_name=command_name,
                click_context=click.get_current_context(),
                theme=theme,
                hide_not_required=hide_not_required,
                allow_file_download=allow_file_download,
                catch_errors=catch_errors,
            ).launch(queue_kwargs=queue_kwargs, launch_kwargs=launch_kwargs)

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
