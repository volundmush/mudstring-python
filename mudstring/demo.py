def run_test():
    import mudstring
    mudstring.install()
    from mudstring.codecs.evennia import decode
    from rich.console import Console
    c = Console(record=True)
    from rich.table import Table
    from rich import box
    t = decode("|rthis|n text is red. |Rthis|n is dark red|/This has a newline.|>This is indented||And piped.")
    c.print(t)
    print(repr(c.export_mud(mxp=True)))
    import time
    table = Table(title="Star Wars Movies", box=box.ASCII, border_style="yellow")

    table.add_column("Released", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Box Office", justify="right", style="green")

    table.add_row("Dec 20, 2019", t, "$952,110,690")
    table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")
    table.add_row("Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889")
    table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439,889")

    start = time.time()
    c.print(table)
    end = time.time()
    print(" (runtime ~ %.4f ms)" % ((end - start) * 1000))

    start = time.time()
    print(repr(c.export_mud(mxp=True)))
    end = time.time()
    print(" (runtime ~ %.4f ms)" % ((end - start) * 1000))

    from mudstring.codecs.pennmush import decode as pdecode, ansi_fun
    to_decode = "Have some \002cr\003very \002ch\003red\002c/\003\002c/\003 text!"
    p = pdecode(to_decode)
    c.print(p)
    print(repr(c.export_mud(mxp=True)))

    p2 = ansi_fun("hc", "this is bright cyan!")
    c.print(p2)
    print(repr(c.export_mud(mxp=True)))


if __name__ == "__main__":
    run_test()
