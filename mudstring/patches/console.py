from dataclasses import dataclass
from rich import console
from rich.segment import Segment
from typing import List, Iterable
from .style import MudStyle

OLD_OPTIONS = console.ConsoleOptions


@dataclass
class MudConsoleOptions(OLD_OPTIONS):
    mxp: bool = False
    """Whether the console supports MXP, for MUD compatability."""

    def copy(self) -> "MudConsoleOptions":
        options = self.__class__.__new__(self.__class__)
        options.__dict__ = self.__dict__.copy()
        return options

    def update(self, **kwargs) -> "MudConsoleOptions":
        mxp = kwargs.pop('mxp', False)
        options = super().update(**kwargs)
        if not isinstance(mxp, console.NoChange):
            options.mxp = mxp
        return options

    def update_mxp(self, mxp: bool):
        options = self.copy()
        options.mxp = mxp
        return options


OLD_CONSOLE = console.Console


class MudConsole(OLD_CONSOLE):

    def export_mud(self, *, clear: bool = True, styles: bool = True, mxp: bool = False) -> str:
        """Generate text from console contents (requires record=True argument in constructor).

        Args:
            clear (bool, optional): Clear record buffer after exporting. Defaults to ``True``.
            styles (bool, optional): If ``True``, ansi escape codes will be included. ``False`` for plain text.
                Defaults to ``False``.

        Returns:
            str: String containing console contents.

        """
        assert (
            self.record
        ), "To export console contents set record=True in the constructor or instance"

        with self._record_buffer_lock:
            if styles:
                text = "".join(
                    (style.render(text, mxp=mxp) if style else text)
                    for text, style, _ in self._record_buffer
                )
            else:
                text = "".join(
                    segment.text
                    for segment in self._record_buffer
                    if not segment.control
                )
            if clear:
                del self._record_buffer[:]
        return text