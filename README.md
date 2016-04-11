## Description

ASCII Decorator is a simple plugin implementation of [**pyfiglet**](https://github.com/pwaller/pyfiglet) for [**Sublime Text 3**](www.sublimetext.com/3).&nbsp; [**pyfiglet**](https://github.com/pwaller/pyfiglet) is a full port of [**FIGlet**](http://www.figlet.org/) into pure python.&nbsp; [**FIGlet**](http://www.figlet.org/) is a program that generates text banners, in a variety of typefaces, composed of letters made up of conglomerations of smaller ASCII characters.

Or simply:
```
    __________________     __         __                   __  __    _
   / ____/  _/ ____/ /__  / /_   ____/ /___  ___  _____   / /_/ /_  (_)____
  / /_   / // / __/ / _ \/ __/  / __  / __ \/ _ \/ ___/  / __/ __ \/ / ___/
 / __/ _/ // /_/ / /  __/ /_   / /_/ / /_/ /  __(__  )  / /_/ / / / (__  ) _ _
/_/   /___/\____/_/\___/\__/   \__,_/\____/\___/____/   \__/_/ /_/_/____(_|_|_)
```

## Prerequisites

* [**Sublime Text 3**](www.sublimetext.com/3)
* [**Package Control**](http://wbond.net/sublime_packages/package_control)

## Features

Each command will convert all selected regions to ASCII text. Regions are handled in the following ways:

* Caret with no selection: entire line text will be converted
* Selection on a single line: only selected text will be converted.
* Selection that spans multiple lines: each line with text will be converted

### Font Selector & Font Favorites

See a live preview of all selected regions. `Font Selector` shows all fonts by name, while `Font Favorites` shows your customized list of frequently used fonts.

By default, `Font Favorites` comes with a list of searchable header styles that can be used in the following ways:

**By Size**

![FontFavorites_BySize](https://raw.githubusercontent.com/Enteleform/ASCII-Decorator/master/GIFs/FontFavorites_BySize.gif)

**By Style**

![FontFavorites_ByStyle](https://raw.githubusercontent.com/Enteleform/ASCII-Decorator/master/GIFs/FontFavorites_ByStyle.gif)

### Generate Font Test

Creates a new document which shows your selected text in all available fonts, so you can choose the one you like best!

![GenerateFontTest_SelectedText](https://raw.githubusercontent.com/Enteleform/ASCII-Decorator/master/GIFs/GenerateFontTest_SelectedText.gif)

## Installation

**(Preferred) Install via [**Package Control Plugin**](http://wbond.net/sublime_packages/package_control) for [**Sublime Text 3**](www.sublimetext.com/3)**

* Bring up command palette (cmd+shift+P or ctrl+shift+P)
* Select option: "Package Control: Install Package"
* Select ASCII Decorator from the list.

**Install via git**

* In a shell: path to the [**Sublime Text 3**](www.sublimetext.com/3) Packages directory
* type: git clone https://github.com/viisual/ASCII Decorator.git

## Usage

* You can access the plugin default font via from selecting: Menu > Edit > ASCII Decorator
* You can access the plugin default font via the key-binding: super+shift+K or alt+shift+K
* You can access the `Font Selector`, `Font Favorites`, & `Generate Font Test` commands via the view context menu or the command palette

## Configuration

You can define your [**sublime-settings**](https://github.com/viisual/ASCII-Decorator/blob/master/ASCII%20Decorator.sublime-settings) preferences @:
```
`Menu / Preferences / Package Settings / ASCII Decorator / Settings - User
```

Custom key-bindings can be set @:
```
`Menu / Preferences / Package Settings / ASCII Decorator / Key Bindings - User

```

## Credits

```
All of the documentation and the majority of the work done was by [**Christopher Jones**](cjones@insub.org).

pyfiglet Packaged by [**Peter Waller**](peter.waller@gmail.com),
various enhancements by [**Stefano Rivera**](stefano@rivera.za.net) & [**Enteleform**](https://packagecontrol.io/browse/authors/Enteleform).
ported to Sublime Text 3 by [**Sascha Wolf**](swolf.dev@gmail.com)

                        _|_|  _|            _|              _|
_|_|_|    _|    _|    _|            _|_|_|  _|    _|_|    _|_|_|_|
_|    _|  _|    _|  _|_|_|_|  _|  _|    _|  _|  _|_|_|_|    _|
_|    _|  _|    _|    _|      _|  _|    _|  _|  _|          _|
_|_|_|      _|_|_|    _|      _|    _|_|_|  _|    _|_|_|      _|_|
_|              _|                      _|
_|          _|_|                    _|_|
```
