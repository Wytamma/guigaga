import pathlib
import tempfile
from abc import ABC, abstractmethod
from typing import Optional

from click import ParamType as ClickParamType
from click import Path as ClickPath
from gradio import File
from gradio.components.base import Component

from guigaga.introspect import ArgumentSchema, OptionSchema


class ParamType(ClickParamType, ABC):
    @abstractmethod
    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        pass

class InputParamType(ParamType):
    pass

class OutputParamType(ParamType):
    pass


class FilePath(File):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process_single_file(self, f) -> pathlib.Path | bytes:
        file_name = f.path
        if self.type == "filepath":
            file = tempfile.NamedTemporaryFile(delete=False, dir=self.GRADIO_CACHE)
            file.name = file_name
            return pathlib.Path(file_name)
        elif self.type == "binary":
            with open(file_name, "rb") as file_data:
                return file_data.read()
        else:
            raise ValueError(
                "Unknown type: "
                + str(type)
                + ". Please choose from: 'filepath', 'binary'."
            )

class Upload(InputParamType, ClickPath):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        return File(label=schema.name)


class Download(OutputParamType, ClickPath):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = filename

    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        return File(label=schema.name)
