import textwrap

from rich.syntax import Syntax
from pygments.token import Comment
from rich.text import Segment

OLD_SYNTAX = Syntax
from rich.console import ConsoleOptions, RenderResult
from rich._loop import loop_first
from .style import MudStyle
from .console import MudConsole
from .text import MudText


class MudSyntax(OLD_SYNTAX):

    def _get_base_style(self) -> MudStyle:
        """Get the base style."""
        # default_style = (
        #     Style(bgcolor=self.background_color)
        #     if self.background_color is not None
        #     else self._theme.get_background_style()
        # )
        default_style = self._theme.get_background_style() + self.background_style
        return MudStyle.upgrade(default_style)

    def __rich_console__(
        self, console: MudConsole, options: ConsoleOptions
    ) -> RenderResult:

        transparent_background = self._get_base_style().transparent_background
        code_width = (
            (
                (options.max_width - self._numbers_column_width - 1)
                if self.line_numbers
                else options.max_width
            )
            if self.code_width is None
            else self.code_width
        )

        line_offset = 0
        if self.line_range:
            start_line, end_line = self.line_range
            line_offset = max(0, start_line - 1)

        code = textwrap.dedent(self.code) if self.dedent else self.code
        code = code.expandtabs(self.tab_size)
        text = self.highlight(code, self.line_range)
        text.remove_suffix("\n")

        (
            background_style,
            number_style,
            highlight_number_style,
        ) = self._get_number_styles(console)

        if not self.line_numbers and not self.word_wrap and not self.line_range:
            # Simple case of just rendering text
            style = (
                self._get_base_style()
                + self._theme.get_style_for_token(Comment)
                + MudStyle(dim=True)
                + self.background_style
            )
            if self.indent_guides and not options.ascii_only:
                text = text.with_indent_guides(self.tab_size, style=style)
                text.overflow = "crop"
            if style.transparent_background:
                yield from console.render(
                    text, options=options.update(width=code_width)
                )
            else:
                syntax_lines = console.render_lines(
                    text,
                    options.update(width=code_width, height=None),
                    style=self.background_style,
                    pad=True,
                    new_lines=True,
                )
                for syntax_line in syntax_lines:
                    yield from syntax_line
            return

        lines = text.split("\n")
        if self.line_range:
            lines = lines[line_offset:end_line]

        if self.indent_guides and not options.ascii_only:
            style = (
                self._get_base_style()
                + self._theme.get_style_for_token(Comment)
                + MudStyle(dim=True)
                + self.background_style
            )
            lines = (
                MudText("\n")
                .join(lines)
                .with_indent_guides(self.tab_size, style=style)
                .split("\n")
            )

        numbers_column_width = self._numbers_column_width
        render_options = options.update(width=code_width)

        highlight_line = self.highlight_lines.__contains__
        _Segment = Segment
        padding = _Segment(" " * numbers_column_width + " ", background_style)
        new_line = _Segment("\n")

        line_pointer = "> " if options.legacy_windows else "❱ "

        for line_no, line in enumerate(lines, self.start_line + line_offset):
            if self.word_wrap:
                wrapped_lines = console.render_lines(
                    line,
                    render_options.update(height=None),
                    style=background_style,
                    pad=not transparent_background,
                )

            else:
                segments = list(line.render(console, end=""))
                if options.no_wrap:
                    wrapped_lines = [segments]
                else:
                    wrapped_lines = [
                        _Segment.adjust_line_length(
                            segments,
                            render_options.max_width,
                            style=background_style,
                            pad=not transparent_background,
                        )
                    ]
            if self.line_numbers:
                for first, wrapped_line in loop_first(wrapped_lines):
                    if first:
                        line_column = str(line_no).rjust(numbers_column_width - 2) + " "
                        if highlight_line(line_no):
                            yield _Segment(line_pointer, MudStyle(color="red"))
                            yield _Segment(line_column, highlight_number_style)
                        else:
                            yield _Segment("  ", highlight_number_style)
                            yield _Segment(line_column, number_style)
                    else:
                        yield padding
                    yield from wrapped_line
                    yield new_line
            else:
                for wrapped_line in wrapped_lines:
                    yield from wrapped_line
                    yield new_line
