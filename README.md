# Volund's MudString library for Python

## CONTACT INFO
**Name:** Volund

**Email:** volundmush@gmail.com

**PayPal:** volundmush@gmail.com

**Discord:** Volund#1206

**Discord Channel:** https://discord.gg/Sxuz3QNU8U

**Patreon:** https://www.patreon.com/volund

**Home Repository:** https://github.com/volundmush/mudstring-python

## TERMS AND CONDITIONS

MIT license. In short: go nuts, but give credit where credit is due.

Please see the included LICENSE.txt for the legalese.

## INTRO
MUD (Multi-User Dungeon) games and their brethren like MUSH, MUX, MUCK, and MOO (look 'em up!) use various ANSI features to provide colors to clients. Sadly there aren't many libraries out there which allow advanced manipulation of such text which preserve the formatting already applied to it. This attempts to address this problem.

mudstring is built upon the existing library, [rich](https://github.com/willmcgugan/rich), using monkey-patching to hack in support for MXP (Mud eXtension Protocol). So, in order to use this library effectively, one must familiarize themselves with Rich. Rich is awesome, so be sure and do that soon.

## FEATURES
  * Everything Rich can do. Seriously, check it out...
  * MXP Support.
  * Encodings library, containing fully-working examples for how to implement various ANSI systems used by existing games.
  

## OKAY, BUT HOW DO I USE IT?
Glad you asked.

Early on in your program, you should...
```python
import mudstring
mudstring.install()
```
This will monkey-patch Rich for this process, replacing a few classes with ones from MudString in a way that will still allow Rich to do everything it normally does. From here on out, though, importing from Rich will net you the patched versions of classes like Style, Text, and Console.

Afterwards, instantiating a MudConsole and directing some output to an output buffer is this easy.

```python
# this will get the MudCOnsole and MudText if install() has been run!
from rich import Console
from rich.text import Text
from mudstring.util import OutBuffer

buffer = bytearray()

out = OutBuffer(buffer)

con = Console(color_system="256", mxp=True, soft_wrap=True, file=out)

con.print(Text("Have some red text!", style="red"))
```
Afterwards, `buffer` will contain the formatted red text.

Note that MudString's Text class for Rich implements a great deal more of the Python String API than Rich's original version, allowing for advanced text formatting - though, unfortunately, no f-strings or str.format() - it won't preserve the styling...

## FAQ 
  __Q:__ This is cool! How can I help?  
  __A:__ [Patreon](https://www.patreon.com/volund) support is always welcome. If you can code and have cool ideas or bug fixes, feel free to fork, edit, and pull request! Join our [discord](https://discord.gg/Sxuz3QNU8U) to really get cranking away though.

  __Q:__ I found a bug! What do I do?  
  __A:__ Post it on this GitHub's Issues tracker. I'll see what I can do when I have time. ... or you can try to fix it yourself and submit a Pull Request. That's cool too.

  __Q:__ But... I want a MUD! Where do I start making a MUD?  
  __A:__ check out [pymush](https://github.com/volundmush/pymush) and [athanor](https://github.com/volundmush/athanor)

## Special Thanks
  * The absolutely awesome lunatics who wrote PennMUSH's ANSI library.
  * The Evennia Project.
  * All of my Patrons on Patreon.
  * Anyone who contributes to this project or my other ones.
  * The Rich devs. That library is a godsend.