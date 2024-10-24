import uuid
from datetime import datetime
from importlib import metadata
from typing import Optional

import click
import gradio as gr
from gradio import Blocks, TabbedInterface
from gradio import Theme as GradioTheme

from guigaga.introspect import ArgumentSchema, CommandSchema, OptionSchema, introspect_click_app
from guigaga.logger import Logger
from guigaga.types import InputParamType, OutputParamType


class GUIGAGA:
    """
    A class to build a graphical user interface for a given command line interface.
    """
    def __init__(
        self,
        cli: click.Group | click.Command,
        app_name: str | None = None,
        command_name: str = "gui",
        click_context: click.Context = None,
        *,
        theme: GradioTheme | str = "soft",
        hide_not_required: bool = False,
        allow_file_download: bool = False,
        catch_errors: bool = True,
    ):
        """
        Initializes the GUIGAGA with the given parameters.

        Args:
          cli (click.Group | click.Command): The command line interface to build a GUI for.
          app_name (str | None): The name of the application. Defaults to None.
          command_name (str): The name of the command. Defaults to "gui".
          click_context (click.Context): The context of the click command. Defaults to None.
          theme (GradioTheme): The theme of the GUI. Defaults to Soft.
          hide_not_required (bool): Whether to hide not required options. Defaults to False.
          allow_file_download (bool): Whether to allow file download. Defaults to False.
          catch_errors (bool): Whether to catch errors. Defaults to True.

        Side Effects:
          - Initializes various instance variables.
          - Calls introspect_click_app to get the command schemas.
          - Calls traverse_command_tree to create the interface.
        """
        self.cli = cli
        self.app_name = app_name if app_name else self.cli.name.upper()
        self.command_name = command_name
        self.theme = theme
        self.hide_not_required = hide_not_required
        self.allow_file_download = allow_file_download
        self.catch_errors = catch_errors
        self.command_schemas = introspect_click_app(cli)
        self.blocks = []
        self.click_context = click_context
        try:
            self.version = metadata.version(self.click_app_name)
        except Exception:
            self.version = None
        # Traverse the command tree and create the interface
        if isinstance(self.command_schemas, dict) and "root" in self.command_schemas:
            schema_tree = self.command_schemas["root"]
        else:
            schema_tree = next(iter(self.command_schemas.values()))
        self.interface = self.traverse_command_tree(schema_tree)

    def launch(self, queue_kwargs: Optional[dict] = None, launch_kwargs: Optional[dict] = None):
        """
        Launches the GUI.

        Args:
          **kwargs: Additional keyword arguments to pass to the launch method.

        Side Effects:
          - Launches the GUI.
        """
        if launch_kwargs is None:
            launch_kwargs = {}
        if queue_kwargs is None:
            queue_kwargs = {}
        self.interface.queue(**queue_kwargs).launch(**launch_kwargs)

    def traverse_command_tree(self, schema: CommandSchema):
        """Recursively traverse the command tree and create a tabbed interface for each nested command group"""
        tab_blocks = []
        # If the current schema has no subcommands, create a block
        if not schema.subcommands:
            block = self.create_block(schema)
            tab_blocks.append(block)
        else:
            # Process all subcommands of the current schema
            for subcommand in schema.subcommands.values():
                if subcommand.name == self.command_name:
                    continue
                # Recursively traverse subcommands and collect blocks
                if subcommand.subcommands:  # Check if it's a group with nested commands
                    sub_interface = self.traverse_command_tree(subcommand)
                    tab_blocks.append((subcommand.name, sub_interface))
                else:
                    block = self.create_block(subcommand)
                    tab_blocks.append(block)

        # If there are multiple blocks, create a TabbedInterface
        if len(tab_blocks) > 1:
            tab_names = [name for name, _ in tab_blocks]
            interface_list = [block for _, block in tab_blocks]
            if schema.name == "root":
                with gr.Blocks(theme=self.theme, analytics_enabled=False, title=self.app_name) as block:
                    version = f" (v{self.version})" if self.version else ""
                    gr.Markdown(f"""# {self.app_name}{version}\n{schema.docstring}""")
                    # gr.Markdown(f"{schema.docstring}")
                    TabbedInterface(interface_list, tab_names=tab_names, analytics_enabled=False)
                return block
            return TabbedInterface(interface_list, tab_names=tab_names, analytics_enabled=False)
        # If there's only one block, just return that block (no tabs needed)
        elif len(tab_blocks) == 1:
            return tab_blocks[0][1]
        msg = "Could not create interface for command schema."
        raise ValueError(msg)


    def create_block(self, command_schema: CommandSchema):
        """
        Creates a block for the given command schema.

        Args:
          command_schema (CommandSchema): The command schema to create a block for.

        Returns:
          tuple: The name of the command and the created block.

        Side Effects:
          - Creates various GUI components.
          - Defines the run_command function.
        """
        logger = Logger()
        with Blocks(theme=self.theme, analytics_enabled=False, title=self.app_name) as block:
            self.render_help_and_header(command_schema)
            with gr.Row():
                with gr.Column():
                    if self.hide_not_required:
                        schemas = self.render_schemas(command_schema, render_not_required=False)
                        if self.has_advanced_options(command_schema):
                            with gr.Accordion("Advanced Options", open=False):
                                schemas.update(self.render_schemas(command_schema, render_required=False))
                    else:
                        schemas = self.render_schemas(command_schema)
                with gr.Column():
                    btn = gr.Button("Run")
                    with gr.Tab("Logs"):
                        logs = gr.Textbox(show_label=False, lines=19, max_lines=19)
                    with gr.Tab("Output", visible=False) as output_tab:
                        outputs = self.get_outputs(command_schema)
                    if self.allow_file_download:
                        with gr.Tab("Files"):
                            file_explorer = gr.FileExplorer(
                                label="Choose a file to download",
                                file_count="single",
                                every=1,
                                height=400,
                            )
                            output_file = gr.File(
                                label="Download file",
                                inputs=file_explorer,
                                visible=False,
                            )

                            def update(filename):
                                return gr.File(filename, visible=True)

                            file_explorer.change(update, file_explorer, output_file)

            # Define the run_command function as a generator
            def run_command(*args, **kwargs):
                # Start the logger's wrapped function which is a generator
                def unwrap(function):
                    if hasattr(function, "__wrapped__"):
                        return unwrap(function.__wrapped__)
                    return function
                function = unwrap(command_schema.function)
                log_gen = logger.intercept_stdin_stdout(
                    function, self.click_context, catch_errors=self.catch_errors
                )(*args, **kwargs)
                logs_output = ""
                # For each yielded log output
                for log_chunk in log_gen:
                    logs_output += log_chunk
                    # Yield logs and no update for other outputs
                    if self.allow_file_download:
                        yield [logs_output, gr.Tab("Output", visible=False), None]
                    else:
                        yield [logs_output, gr.Tab("Output", visible=False)]
                if logger.exit_code:
                    if self.allow_file_download:
                        return [logs_output, gr.Tab("Output", visible=False), None]
                    return [logs_output, gr.Tab("Output", visible=False)]
                # After function completes, yield final outputs
                # Update output_group visibility and outputs
                render_outputs = False
                if outputs:
                    render_outputs = True
                yield [logs_output, gr.Tab("Output", visible=render_outputs), *self.get_output_values(command_schema)]

            inputs = self.sort_schemas(command_schema, schemas)
            btn.click(fn=run_command, inputs=inputs, outputs=[logs, output_tab, *outputs])
        return command_schema.name, block

    def get_outputs(self, command_schema: CommandSchema):
        """
        Gets the outputs for the given command schema.

        Args:
          command_schema (CommandSchema): The command schema to get the outputs for.

        Returns:
          list: The list of outputs.
        """
        outputs = []
        for schema in command_schema.options + command_schema.arguments:
            if isinstance(schema.type, OutputParamType):
                outputs.append(schema.type.render(schema))
        return outputs

    def get_output_values(self, command_schema: CommandSchema):
        """
        Gets the output values for the given command schema.

        Args:
          command_schema (CommandSchema): The command schema to get the output values for.

        Returns:
          list: The list of output values.
        """
        outputs = []
        for schema in command_schema.options + command_schema.arguments:
            if isinstance(schema.type, OutputParamType):
                outputs.append(schema.type.value)
        return outputs

    def render_help_and_header(self, command_schema: CommandSchema):
        """
        Renders the help and header for the given command schema.

        Args:
          command_schema (CommandSchema): The command schema to render the help and header for.

        Side Effects:
          - Renders the help and header.
        """
        gr.Markdown(f"""# {command_schema.name}""")
        gr.Markdown(command_schema.docstring)

    def has_advanced_options(self, command_schema: CommandSchema):
        """
        Checks if the given command schema has advanced options.

        Args:
          command_schema (CommandSchema): The command schema to check.

        Returns:
          bool: True if the command schema has advanced options, False otherwise.
        """
        return any(not schema.required for schema in command_schema.options + command_schema.arguments)

    def render_schemas(self, command_schema, *, render_required=True, render_not_required=True):
        """
        Renders the schemas for the given command schema.

        Args:
          command_schema (CommandSchema): The command schema to render the schemas for.
          render_required (bool): Whether to render required schemas. Defaults to True.
          render_not_required (bool): Whether to render not required schemas. Defaults to True.

        Returns:
          dict: The rendered schemas.
        """
        inputs = {}
        schemas = command_schema.arguments + command_schema.options  #TODO: sort the schemas before passing them to the render function
        schemas = [
            schema
            for schema in schemas
            if (render_required and schema.required) or (render_not_required and not schema.required)
        ]
        schemas_name_map = {
            schema.name if isinstance(schema.name, str) else schema.name[0].lstrip("-").replace("-", "_"): schema for schema in schemas
        }
        for name, schema in schemas_name_map.items():
            component = self.get_component(schema)
            inputs[name] = component
        return inputs

    def sort_schemas(self, command_schema, schemas: dict):
        """
        Sorts the given schemas based on the order of the command schema's function arguments.

        Args:
          command_schema (CommandSchema): The command schema to sort the schemas based on.
          schemas (dict): The schemas to sort.

        Returns:
          list: The sorted schemas.
        """
        # recursively unwrap the function
        def unwrap(function):
            if hasattr(function, "__wrapped__"):
                return unwrap(function.__wrapped__)
            return function
        function = unwrap(command_schema.function)
        order = function.__code__.co_varnames[: function.__code__.co_argcount]
        schemas = [schemas[name] for name in order if name in schemas]
        return schemas

    def get_component(self, schema: OptionSchema | ArgumentSchema):
        """
        Gets the component for the given schema.

        Args:
          schema (OptionSchema | ArgumentSchema): The schema to get the component for.

        Returns:
          gradio.Interface: The component for the given schema.
        """

        default = None
        if schema.default.values:
            default = schema.default.values[0][0]
        if isinstance(schema, OptionSchema):
            label = schema.name[0].lstrip("-")
            help_text = schema.help
        else:
            label = schema.name
            help_text = None
        # Handle different component types
        if isinstance(schema.type, OutputParamType):
            return gr.Textbox(value=schema.type.value, visible=False)
        if isinstance(schema.type, InputParamType):
            return schema.type.render(schema)
        # Defaults will be moved into Types
        component_type_name = schema.type.name
        if component_type_name == "text":
            return gr.Textbox(label=label, value=default, info=help_text)

        elif component_type_name == "integer":
            return gr.Number(default, label=label, precision=0, info=help_text)

        elif component_type_name == "float":
            return gr.Number(default, label=label, info=help_text)

        elif component_type_name == "boolean":
            return gr.Checkbox(default == "true", label=label, info=help_text)

        elif component_type_name == "uuid":
            uuid_val = str(uuid.uuid4()) if default is None else default
            return gr.Textbox(uuid_val, label=label, info=help_text)

        elif component_type_name == "filename":
            return gr.File(label=label, value=default)

        elif component_type_name == "path":
            return gr.File(label=label, value=default)

        elif component_type_name == "choice":
            choices = schema.type.choices
            return gr.Dropdown(choices, value=default, label=label, info=help_text)

        elif component_type_name == "integer range":
            min_val = schema.type.min if schema.type.min is not None else 0
            max_val = schema.type.max if schema.type.max is not None else 100
            return gr.Slider(minimum=min_val, maximum=max_val, step=1, value=default, label=label, info=help_text)

        elif component_type_name == "float range":
            min_val = schema.type.min if schema.type.min is not None else 0.0
            max_val = schema.type.max if schema.type.max is not None else 1.0
            return gr.Slider(minimum=min_val, maximum=max_val, value=default, label=label, step=0.01, info=help_text)

        elif component_type_name == "datetime":
            formats = (
                schema.type.formats if schema.type.formats else ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
            )
            datetime_val = default if default is not None else datetime.now().strftime(formats[0])  # noqa: DTZ005
            return gr.DateTime(value=datetime_val, label=label, info=help_text)

        else:
            return gr.Textbox(value=default, label=label, info=help_text)
