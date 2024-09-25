import uuid
from datetime import datetime
from importlib import metadata

import click
import gradio as gr
from gradio import Blocks, TabbedInterface

from guigaga.introspect import ArgumentSchema, CommandSchema, OptionSchema, introspect_click_app
from guigaga.logger import Logger
from guigaga.themes import Theme
from guigaga.types import InputParamType, OutputParamType


class InterfaceBuilder:
    def __init__(
        self,
        cli: click.Group | click.Command,
        app_name: str | None = None,
        command_name: str = "gui",
        click_context: click.Context = None,
        *,
        theme: Theme = Theme.soft,
        hide_not_required: bool = False,
        allow_file_download: bool = True,
        catch_errors: bool = True,
    ):
        self.cli = cli
        self.app_name = app_name
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
            schemas = self.command_schemas["root"]
        else:
            schemas = next(iter(self.command_schemas.values()))
        self.interface = self.traverse_command_tree(schemas)

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
                with gr.Blocks() as block:
                    version = f" (v{self.version})" if self.version else ""
                    gr.Markdown(f"""# {self.cli.name.upper()}{version}\n{schema.docstring}""")
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
        logger = Logger()

        with Blocks(theme=self.theme.value) as block:
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
                    with gr.Tab("Output", visible=False) as output_tab:
                        outputs = self.get_outputs(command_schema)
                    with gr.Tab("Logs"):
                        logs = gr.Textbox(show_label=False, lines=19, max_lines=19)
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
                log_gen = logger.intercept_stdin_stdout(
                    command_schema.function, self.click_context, catch_errors=self.catch_errors
                )(*args, **kwargs)
                logs_output = ""
                # For each yielded log output
                for log_chunk in log_gen:
                    logs_output += log_chunk
                    # Yield logs and no update for other outputs
                    yield [logs_output, gr.Tab("Output", visible=False), None]
                if logger.exit_code:
                    return [logs_output, gr.Tab("Output", visible=False), None]
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
        outputs = []
        for schema in command_schema.options + command_schema.arguments:
            if isinstance(schema.type, OutputParamType):
                outputs.append(schema.type.render(schema))
        return outputs

    def get_output_values(self, command_schema: CommandSchema):
        outputs = []
        for schema in command_schema.options + command_schema.arguments:
            if isinstance(schema.type, OutputParamType):
                outputs.append(schema.type.value)
        return outputs

    def render_help_and_header(self, command_schema: CommandSchema):
        gr.Markdown(f"""# {command_schema.name}""")
        gr.Markdown(command_schema.docstring)

    def has_advanced_options(self, command_schema: CommandSchema):
        return any(not schema.required for schema in command_schema.options + command_schema.arguments)

    def render_schemas(self, command_schema, *, render_required=True, render_not_required=True):
        inputs = {}
        schemas = command_schema.options + command_schema.arguments
        schemas = [
            schema
            for schema in schemas
            if (render_required and schema.required) or (render_not_required and not schema.required)
        ]
        schemas_name_map = {
            schema.name if isinstance(schema.name, str) else schema.name[0].lstrip("-"): schema for schema in schemas
        }
        for name, schema in schemas_name_map.items():
            component = self.get_component(schema)
            inputs[name] = component
        return inputs

    def sort_schemas(self, command_schema, schemas: dict):
        function = getattr(command_schema.function, "__wrapped__", command_schema.function)
        order = function.__code__.co_varnames[: function.__code__.co_argcount]
        schemas = [schemas[name] for name in order if name in schemas]
        return schemas

    def get_component(self, schema: OptionSchema | ArgumentSchema):

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
            return gr.Number(label=label, precision=0, value=default, info=help_text)

        elif component_type_name == "float":
            return gr.Number(label=label, value=default, info=help_text)

        elif component_type_name == "boolean":
            return gr.Checkbox(default == "true", label=label, info=help_text)

        elif component_type_name == "uuid":
            uuid_val = str(uuid.uuid4()) if default is None else default
            return gr.Textbox(uuid_val, label=label, info=help_text)

        elif component_type_name == "filename":
            return gr.File(label=label, value=default)

        elif component_type_name == "path":
            return gr.FileExplorer(label=label, file_count="single", value=default)

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
