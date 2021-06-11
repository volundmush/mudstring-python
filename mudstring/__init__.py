

def install():
    from .patches import console as new_console, style as new_style, default_styles, text as new_text
    from .patches import traceback as new_traceback, syntax as new_syntax
    from rich import style, console, themes, text, traceback, syntax
    text.Text = new_text.MudText
    themes.DEFAULT = default_styles.DEFAULT
    style.Style = new_style.MudStyle
    style.NULL_STYLE = new_style.MudStyle()
    console.ConsoleOptions = new_console.MudConsoleOptions
    console.Console = new_console.MudConsole
    traceback.Traceback = new_traceback.MudTraceback
    syntax.Syntax = new_syntax.MudSyntax
