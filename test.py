
def run_test():
    import mudstring
    mudstring.install()
    from rich.text import Text
    from rich.console import Console
    c = Console(record=True)
    from rich.style import Style
    from rich.table import Table
    from rich import box
    s = Style(color="red", tag="SEND", xml_attr={"href": "dothis"})
    t = Text("This is some text!", style=s)
    c.print(t)
    print(repr(c.export_mud(mxp=True)))

    table = Table(title="Star Wars Movies", box=box.ASCII, border_style="yellow")

    table.add_column("Released", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Box Office", justify="right", style="green")

    table.add_row("Dec 20, 2019", t, "$952,110,690")
    table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")
    table.add_row("Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889")
    table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439,889")

    c.print(table)

    print(repr(c.export_mud(mxp=True)))

if __name__ == "__main__":
    run_test()
