# Volund's MudString library for Python

## CONTACT INFO
**Name:** Volund

**Email:** volundmush@gmail.com

**PayPal:** volundmush@gmail.com

**Discord:** Volund#1206

**Patreon:** https://www.patreon.com/volund

**Home Repository:** https://github.com/volundmush/mudstring-python

## TERMS AND CONDITIONS

MIT license. In short: go nuts, but give credit where credit is due.

Please see the included LICENSE.txt for the legalese.

## INTRO
MUD (Multi-User Dungeon) games and their brethren like MUSH, MUX, MUCK, and MOO (look 'em up!) use various ANSI features to provide colors to clients. Sadly there aren't many libraries out there which allow advanced manipulation of such text which preserve the formatting already applied to it. This attempts to address this problem.

mudstring is built upon the existing library, rich, using monkey-patching to hack in support for MXP (Mud eXtension Protocol). So, in order to use this library effectively, one must familiarize themselves with Rich. Rich is awesome, so be sure and do that soon.

## FEATURES
  * Everything Rich can do. Seriously, check it out...
  * Also allows the support features of enrich to work.
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

Rich can then be used as one normally uses Rich, however Style objects can now be created with MXP Tags+Attributes, and the Console's .export_mud() method is used to render everything that was Console-printed to a single string, ready to be sent to the client.

## FAQ 
  __Q:__ This is cool! How can I help?  
  __A:__ Patreon support is always welcome. If you can code and have cool ideas or bug fixes, feel free to fork, edit, and pull request!

  __Q:__ I found a bug! What do I do?  
  __A:__ Post it on this GitHub's Issues tracker. I'll see what I can do when I have time. ... or you can try to fix it yourself and submit a Pull Request. That's cool too.

  __Q:__ But... I want a MUD! Where do I start making a MUD?  
  __A:__ Coming soon...

## Special Thanks
  * The absolute lunatics who wrote PennMUSH's ANSI library.
  * The Evennia Project.
  * All of my Patrons on Patreon.
  * Anyone who contributes to this project or my other ones.
  * The Rich devs. That library is a godsend.