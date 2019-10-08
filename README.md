# ASCII Decorator

[Features](https://github.com/viisual/ASCII-Decorator#features) &nbsp;|&nbsp; [Installation](https://github.com/viisual/ASCII-Decorator#installation) &nbsp;|&nbsp; [Usage](https://github.com/viisual/ASCII-Decorator#usage) &nbsp;|&nbsp; [Configuration](https://github.com/viisual/ASCII-Decorator#configuration) &nbsp;|&nbsp; [Credits](https://github.com/viisual/ASCII-Decorator#credits)

&nbsp;

ASCII Decorator is a simple plugin implementation of [**pyfiglet**](https://github.com/pwaller/pyfiglet) for [**Sublime Text 3**](https://www.sublimetext.com/3).&nbsp; `pyfiglet` is a full port of [**FIGlet**](http://www.figlet.org/) into pure python.&nbsp; `FIGlet` is a program that generates text banners, in a variety of typefaces, composed of letters made up of conglomerations of smaller ASCII characters.

Or simply:
```
    __________________     __         __                   __  __    _
   / ____/  _/ ____/ /__  / /_   ____/ /___  ___  _____   / /_/ /_  (_)____
  / /_   / // / __/ / _ \/ __/  / __  / __ \/ _ \/ ___/  / __/ __ \/ / ___/
 / __/ _/ // /_/ / /  __/ /_   / /_/ / /_/ /  __(__  )  / /_/ / / / (__  ) _ _
/_/   /___/\____/_/\___/\__/   \__,_/\____/\___/____/   \__/_/ /_/_/____(_|_|_)
```

# Features

### Font Selector & Font Favorites

See a live preview of the first selected region and convert all selected regions to the chosen font upon execution.  
`Font Selector` shows all fonts by name, while `Font Favorites` shows your customized list of frequently used fonts.

By default, `Font Favorites` comes with a list of searchable header styles that can be used in the following ways:

**─── By Size ───**

![**FontFavorites_BySize**](https://raw.githubusercontent.com/Enteleform/ASCII-Decorator/master/GIFs/FontFavorites_BySize.gif)

**─── By Style ───**

![**FontFavorites_ByStyle**](https://raw.githubusercontent.com/Enteleform/ASCII-Decorator/master/GIFs/FontFavorites_ByStyle.gif)

### Generate Font Test

Creates a new document which shows your selected text ( *or "Lorem Ipsum"* ) in all available fonts, so you can choose the one you like best!

![**GenerateFontTest_SelectedText**](https://raw.githubusercontent.com/Enteleform/ASCII-Decorator/master/GIFs/GenerateFontTest_SelectedText.gif)

# Installation

Install via [**Package Control**](https://packagecontrol.io/installation) for [**Sublime Text 3**](https://www.sublimetext.com/3) (*Preferred*)

* Bring up the command palette:
 * <kbd>Cmd + Shift + P</kbd> (*OSX & Linux*)
 * <kbd>Ctrl + Shift + P</kbd> (*Windows*)
* Select option: `Package Control: Install Package`
* Select `ASCII Decorator` from the list

Install via `git`

* In a shell: navigate to the Sublime Text `Packages` directory
* Type: `git clone https://github.com/viisual/ASCII-Decorator.git`

# Usage

### Command Palette

Bring up the command palette:
* <kbd>Cmd + Shift + P</kbd> (*OSX & Linux*)
* <kbd>Ctrl + Shift + P</kbd> (*Windows*)

Type:

* `ASCII Decorator: Default Font`
* `ASCII Decorator: Font Selector`
* `ASCII Decorator: Font Favorites`
* `ASCII Decorator: Generate Font Test (Selected Text)`
* `ASCII Decorator: Generate Font Test (Lorem Ipsum)`

### Context Menu

Right-click on your document to access the context menu.

The `ASCII Decorator` sub-menu contains:

* `Default Font`
* `Font Selector`
* `Font Favorites`
* `Generate Font Test (Selected Text)`

### Key Bindings

One key binding is included for `Default Font`:

 * <kbd>Super + Shift + K</kbd> (*OSX & Linux*)
 * <kbd>Alt + Shift + K</kbd> (*Windows*)

See [**sublime-commands**](https://github.com/viisual/ASCII-Decorator/blob/master/Default.sublime-commands) for a list of additional commands that can be mapped to key bindings.

### Selections

Each command will convert all selected regions to ASCII text.

Regions are handled in the following ways:

* Caret with no selection:
 * the entire line's text will be converted
* Selection on a single line:
 * only selected text will be converted.
* Selection that spans multiple lines:
 * each line that contains text will be converted

# Configuration

You can define your [**sublime-settings**](https://github.com/viisual/ASCII-Decorator/blob/master/ASCII%20Decorator.sublime-settings) preferences @:  
`Menu > Preferences > Package Settings > ASCII Decorator > Settings - User`

Custom key bindings can be set @:  
`Menu > Preferences > Package Settings > ASCII Decorator > Key Bindings - User`

# Credits

Primary development & documentation by: [**Christopher Jones**](mailto:cjones@insub.org)

Packaging of `pyfiglet` by: [**Peter Waller**](mailto:peter.waller@gmail.com)  
Various enhancements by: [**Stefano Rivera**](mailto:stefano@rivera.za.net) & [**Enteleform**](https://packagecontrol.io/browse/authors/Enteleform)  
Ported to `Sublime Text 3` by: [**Sascha Wolf**](mailto:swolf.dev@gmail.com)  

```
                        _|_|  _|            _|              _|
_|_|_|    _|    _|    _|            _|_|_|  _|    _|_|    _|_|_|_|
_|    _|  _|    _|  _|_|_|_|  _|  _|    _|  _|  _|_|_|_|    _|
_|    _|  _|    _|    _|      _|  _|    _|  _|  _|          _|
_|_|_|      _|_|_|    _|      _|    _|_|_|  _|    _|_|_|      _|_|
_|              _|                      _|
_|          _|_|                    _|_|
```
