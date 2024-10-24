import pathlib
import tempfile
from abc import ABC, abstractmethod

from click import ParamType as ClickParamType
from click import Path as ClickPath
from gradio import File
from gradio import FileExplorer as GradioFileExplorer
from gradio.components.base import Component

from guigaga.introspect import ArgumentSchema, OptionSchema


class ParamType(ClickParamType, ABC):
    """
    An abstract base class that inherits from ClickParamType and ABC. It provides a blueprint for parameter types.
    """
    @abstractmethod
    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        """
        An abstract method that must be implemented by any class that inherits from ParamType.

        Args:
          schema (OptionSchema | ArgumentSchema): The schema to render.

        Returns:
          Component: The rendered component.
        """
        pass

class InputParamType(ParamType):
    """
    A class that inherits from ParamType. It represents an input parameter type.
    """
    pass

class OutputParamType(ParamType):
    """
    A class that inherits from ParamType. It represents an output parameter type.
    """
    pass


class FilePath(File):
    """
    A class that inherits from File. It represents a file path.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes a FilePath instance.

        Args:
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)

    def _process_single_file(self, f) -> pathlib.Path | bytes:
        """
        Processes a single file.

        Args:
          f: The file to process.

        Returns:
          pathlib.Path | bytes: The processed file.

        Raises:
          ValueError: If the file type is unknown.
        """
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
    """
    A class that inherits from InputParamType and ClickPath. It represents an upload parameter type.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes an Upload instance.

        Args:
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)


    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        """
        Renders the upload component.

        Args:
          schema (OptionSchema | ArgumentSchema): The schema to render.

        Returns:
          Component: The rendered component.
        """
        return File(label=schema.name)


class Download(OutputParamType, ClickPath):
    """
    A class that inherits from OutputParamType and ClickPath. It represents a download parameter type.
    """
    def __init__(self, filename, *args, **kwargs):
        """
        Initializes a Download instance.

        Args:
          filename: The name of the file to download.
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.value = filename

    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        """
        Renders the download component.

        Args:
          schema (OptionSchema | ArgumentSchema): The schema to render.

        Returns:
          Component: The rendered component.
        """
        return File(label=schema.name)


class FileExplorer(InputParamType, ClickPath):
    """
    A class that inherits from InputParamType and ClickPath. It represents a file explorer parameter type.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes a FileExplorer instance.

        Args:
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)

    def render(self, schema: OptionSchema | ArgumentSchema) -> Component:
        """
        Renders the file explorer component.

        Args:
          schema (OptionSchema | ArgumentSchema): The schema to render.

        Returns:
          Component: The rendered component.
        """
        return GradioFileExplorer(label=schema.name, file_count="single", value=schema.default)
