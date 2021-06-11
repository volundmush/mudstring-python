from rich.traceback import Traceback, PathHighlighter, _SyntaxError
from rich.highlighter import RegexHighlighter, ReprHighlighter
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    RenderResult,
    render_group,
)
from rich.theme import Theme
from rich.panel import Panel
from rich._loop import loop_first, loop_last
from rich.constrain import Constrain

from pygments.lexers import guess_lexer_for_filename
from pygments.token import Comment, Keyword, Name, Number, Operator, String
from pygments.token import Text as TextToken
from pygments.token import Token

from .text import MudText
from .style import MudStyle


OLD_TRACEBACK = Traceback


class MudTraceback(OLD_TRACEBACK):

    @render_group()
    def _render_syntax_error(self, syntax_error: _SyntaxError) -> RenderResult:
        highlighter = ReprHighlighter()
        path_highlighter = PathHighlighter()
        if syntax_error.filename != "<stdin>":
            text = MudText.assemble(
                (f" {syntax_error.filename}", "pygments.string"),
                (":", "pygments.text"),
                (str(syntax_error.lineno), "pygments.number"),
                style="pygments.text",
            )
            yield path_highlighter(text)
        syntax_error_text = highlighter(syntax_error.line.rstrip())
        syntax_error_text = MudText.upgrade(syntax_error_text)
        syntax_error_text.no_wrap = True
        offset = min(syntax_error.offset - 1, len(syntax_error_text))
        syntax_error_text.stylize("bold underline", offset, offset + 1)
        to_add = MudText.upgrade(MudText.from_markup(
            "\n" + " " * offset + "[traceback.offset]▲[/]",
            style="pygments.text",
        ))
        syntax_error_text += to_add
        yield syntax_error_text

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        theme = self.theme
        background_style = theme.get_background_style()
        token_style = theme.get_style_for_token

        traceback_theme = Theme(
            {
                "pretty": token_style(TextToken),
                "pygments.text": token_style(Token),
                "pygments.string": token_style(String),
                "pygments.function": token_style(Name.Function),
                "pygments.number": token_style(Number),
                "repr.indent": token_style(Comment) + MudStyle(dim=True),
                "repr.str": token_style(String),
                "repr.brace": token_style(TextToken) + MudStyle(bold=True),
                "repr.number": token_style(Number),
                "repr.bool_true": token_style(Keyword.Constant),
                "repr.bool_false": token_style(Keyword.Constant),
                "repr.none": token_style(Keyword.Constant),
                "scope.border": token_style(String.Delimiter),
                "scope.equals": token_style(Operator),
                "scope.key": token_style(Name),
                "scope.key.special": token_style(Name.Constant) + MudStyle(dim=True),
            }
        )

        highlighter = ReprHighlighter()
        for last, stack in loop_last(reversed(self.trace.stacks)):
            if stack.frames:
                stack_renderable: ConsoleRenderable = Panel(
                    self._render_stack(stack),
                    title="[traceback.title]Traceback [dim](most recent call last)",
                    style=background_style,
                    border_style="traceback.border.syntax_error",
                    expand=True,
                    padding=(0, 1),
                )
                stack_renderable = Constrain(stack_renderable, self.width)
                with console.use_theme(traceback_theme):
                    yield stack_renderable
            if stack.syntax_error is not None:
                with console.use_theme(traceback_theme):
                    yield Constrain(
                        Panel(
                            self._render_syntax_error(stack.syntax_error),
                            style=background_style,
                            border_style="traceback.border",
                            expand=True,
                            padding=(0, 1),
                            width=self.width,
                        ),
                        self.width,
                    )
                yield MudText.assemble(
                    (f"{stack.exc_type}: ", "traceback.exc_type"),
                    highlighter(stack.syntax_error.msg),
                )
            else:
                yield MudText.assemble(
                    (f"{stack.exc_type}: ", "traceback.exc_type"),
                    highlighter(stack.exc_value),
                )

            if not last:
                if stack.is_cause:
                    yield MudText.from_markup(
                        "\n[i]The above exception was the direct cause of the following exception:\n",
                    )
                else:
                    yield MudText.from_markup(
                        "\n[i]During handling of the above exception, another exception occurred:\n",
                    )