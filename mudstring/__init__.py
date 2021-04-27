

def install():
    from .patches import console as new_console, style as new_style, default_styles
    from rich import style, console, themes
    themes.DEFAULT = default_styles.DEFAULT
    style.Style = new_style.MudStyle
    style.NULL_STYLE = new_style.MudStyle()
    console.ConsoleOptions = new_console.MudConsoleOptions
    console.Console = new_console.MudConsole

