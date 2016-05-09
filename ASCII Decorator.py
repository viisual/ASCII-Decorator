import sublime
import sublime_plugin
import os
import re
import sys
import traceback
import tempfile

ST3 = int(sublime.version()) >= 3000

if not ST3:
    from subfiglet import SublimeFiglet, figlet_paths
    import subcomments
else:
    from .subfiglet import SublimeFiglet, figlet_paths
    from . import subcomments

PACKAGE_LOCATION = os.path.abspath(os.path.dirname(__file__))


def calculate_indent(view, sel):

    # Determine the indent of the CSS rule
    (row, col) = view.rowcol(sel.begin())
    indent_region = view.find('^\s+', view.text_point(row, 0))
    if indent_region and view.rowcol(indent_region.begin())[0] == row:
        indent = view.substr(indent_region)
    else:
        indent = ''
    return indent


def remove_trailing_ws(string):
    return re.sub(r'(?m) *$', '', string)


class FontPreviewGeneratorCommand(sublime_plugin.WindowCommand):
    def run(self, text = "Lorem Ipsum", use_selected_text = False):
        # Find directory locations
        font_locations = figlet_paths()

        # Verify selected text
        if use_selected_text == True:

            view = self.window.active_view()
            selections = view.sel()
            regionCount = len( selections )

            if regionCount == 0 or regionCount > 1:
                return

            selection = selections[0]
            line_A = view.line( selection.a )
            line_B = view.line( selection.b )

            if line_A != line_B:
                return

            if selection.a == selection.b:
                sourceRegion = line_A
            else:
                sourceRegion = selection

            text = view.substr( sourceRegion )
            text = text.strip()

            if text == "":
                return

        # Find available fonts
        self.options = []
        for fl in font_locations:
            for f in os.listdir(fl):
                pth = os.path.join(fl, f)
                if os.path.isfile(pth):
                    if f.endswith((".flf", ".tlf")):
                        self.options.append((f[:-4], fl))

        self.options.sort()

        with tempfile.NamedTemporaryFile(mode = 'wb', delete=False, suffix='.txt') as p:
            for font in self.options:
                f = SublimeFiglet(
                    font=font[0], directory=font[1], width=80,
                    justify="auto", direction="auto"
                )
                p.write(("Font: %s Directory: %s\n" % (font[0], font[1])).encode("utf-8"))
                p.write(
                    remove_trailing_ws(f.renderText(text).replace('\r\n', '\n').replace('\r', '\n')).encode('utf-8')
                )
                p.write("\n\n".encode("utf-8"))

        self.window.open_file(p.name)


class UpdateFigletPreviewCommand(sublime_plugin.TextCommand):
    """
        A reasonable edit command that works in ST2 and ST3
    """

    preview = None
    def run(
        self, edit, font, directory=None, width=None,
        justify=None, direction=None, use_additional_indent=False,
        flip=None, reverse=None
    ):
        preview = UpdateFigletPreviewCommand.get_buffer()
        if not ST3:
            preview = preview.encode('UTF-8')
        if preview is not None:
            self.view.replace(edit, sublime.Region(0, self.view.size()), preview)
            sel = self.view.sel()
            sel.clear()
            sel.add(sublime.Region(0, self.view.size()))
            self.view.run_command(
                "figlet",
                {
                    "font": font,
                    "directory": directory,
                    "use_additional_indent": use_additional_indent,
                    "insert_as_comment": False,
                    "width": width,
                    "justify": justify,
                    "direction": direction,
                    "flip": flip,
                    "reverse": reverse
                }
            )
            UpdateFigletPreviewCommand.clear_buffer()
            sel.clear()

    @classmethod
    def set_buffer(cls, text):
        cls.preview = text

    @classmethod
    def get_buffer(cls):
        return cls.preview

    @classmethod
    def clear_buffer(cls):
        cls.preview = None


class FigletFavoritesCommand( sublime_plugin.TextCommand ):
    def run( self, edit ):
        self.undo = False
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')

        favorites = settings.get("favorite_fonts", [])

        if len(favorites) == 0:
            return

        self.fonts = []

        for f in favorites:
            if "font" not in f or "name" not in f:
                continue

            self.fonts.append(
                {
                    "name": f.get("name"),
                    "font": f.get("font"),
                    "comment": f.get("comment", True),
                    "comment_style": f.get("comment_style", "block"),
                    "width": f.get("width", 80),
                    "direction": f.get("direction", "auto"),
                    "justify": f.get("justify", "auto"),
                    "indent": f.get("indent", True),
                    "flip": f.get("flip", False),
                    "reverse": f.get("reverse", False)
                }
            )

        # Prepare and show quick panel
        if len(self.fonts):
            if not ST3:
                self.view.window().show_quick_panel(
                    [f["name"] for f in self.fonts],
                    self.apply_figlet
                )
            else:
                self.view.window().show_quick_panel(
                    [f["name"] for f in self.fonts],
                    self.apply_figlet,
                    on_highlight=self.preview if bool(settings.get("show_preview", False)) else None
                )

    def preview(self, value):
        """
            Preview the figlet output (ST3 only)
        """

        if value != -1:
            # Find the first good selection to preview
            example = None

            for selection in self.view.sel():

                line_A = self.view.line( selection.a )
                line_B = self.view.line( selection.b )

                if  line_A == line_B \
                and selection.a == selection.b \
                and self.view.substr( line_A ).strip() != "": # use caret line
                    indent = calculate_indent(self.view, line_A)
                    example = self.view.substr( sublime.Region(line_A.begin() + len(indent), line_A.end()) )
                    break

                elif line_A == line_B \
                and  selection.a != selection.b \
                and self.view.substr( selection ).strip() != "": # use selection
                    example = self.view.substr( selection )
                    break

                else: # multi line selection
                    for line in self.view.lines( selection ):
                        if self.view.substr( line ).strip() != "":
                            indent = calculate_indent(self.view, line)
                            example = self.view.substr( sublime.Region(line.begin() + len(indent), line.end()) )
                            break

            if example is None:
                return

            # Create output panel and set to current syntax
            view = self.view.window().get_output_panel('figlet_preview')
            view.settings().set("draw_white_space", "none")
            self.view.window().run_command("show_panel", {"panel": "output.figlet_preview"})

            font = self.fonts[value]

            # Preview
            UpdateFigletPreviewCommand.set_buffer(example)
            view.run_command(
                "update_figlet_preview",
                {
                    "font": font.get("font"),
                    "use_additional_indent": font.get("indent"),
                    "width": font.get("width"),
                    "justify": font.get("justify"),
                    "direction": font.get("direction"),
                    "flip": font.get("flip"),
                    "reverse": font.get("reverse")
                }
            )

    def apply_figlet(self, value):
        """
            Run and apply pyfiglet on the selections in the view
        """

        # Hide the preview panel if shown
        self.view.window().run_command("hide_panel", {"panel": "output.figlet_preview"})

        # Apply figlet
        if value != -1:
            font = self.fonts[value]
            self.view.run_command(
                "figlet",
                {
                    "font": font.get("font"),
                    "insert_as_comment": font.get("comment"),
                    "comment_style": font.get("comment_style"),
                    "use_additional_indent": font.get("indent"),
                    "width": font.get("width"),
                    "justify": font.get("justify"),
                    "direction": font.get("direction"),
                    "flip": font.get("flip"),
                    "reverse": font.get("reverse")
                }
            )


class FigletMenuCommand( sublime_plugin.TextCommand ):
    def run( self, edit ):
        self.undo = False
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')

        # Find directory locations
        font_locations = figlet_paths()

        # Find available fonts
        self.options = []
        for fl in font_locations:
            for f in os.listdir(fl):
                pth = os.path.join(fl, f)
                if os.path.isfile(pth):
                    if f.endswith((".flf", ".tlf")):
                        self.options.append(f)

        self.options.sort()

        # Prepare and show quick panel
        if len(self.options):
            if not ST3:
                self.view.window().show_quick_panel(
                    [o[:-4] for o in self.options],
                    self.apply_figlet
                )
            else:
                self.view.window().show_quick_panel(
                    [o[:-4] for o in self.options],
                    self.apply_figlet,
                    on_highlight=self.preview if bool(settings.get("show_preview", False)) else None
                )

    def preview(self, value):
        """
            Preview the figlet output (ST3 only)
        """

        if value != -1:
            # Find the first good selection to preview
            sel = self.view.sel()
            example = None
            for s in sel:
                if s.size():
                    example = self.view.substr(s)
                    break
            if example is None:
                return

            # Create output panel and set to current syntax
            view = self.view.window().get_output_panel('figlet_preview')
            view.settings().set("draw_white_space", "none")
            self.view.window().run_command("show_panel", {"panel": "output.figlet_preview"})

            # Preview
            UpdateFigletPreviewCommand.set_buffer(example)
            view.run_command(
                "update_figlet_preview",
                {
                    "font": self.options[value][:-4]
                }
            )

    def apply_figlet(self, value):
        """
            Run and apply pyfiglet on the selections in the view
        """

        # Hide the preview panel if shown
        self.view.window().run_command("hide_panel", {"panel": "output.figlet_preview"})

        # Apply figlet
        if value != -1:
            self.view.run_command(
                "figlet",
                {
                    "font": self.options[value][:-4]
                }
            )


class FigletDefaultCommand( sublime_plugin.TextCommand ):
    def run(self, edit):
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        font = settings.get('ascii_decorator_font', "slant")
        self.view.run_command("figlet", {"font": font})


class FigletCommand( sublime_plugin.TextCommand ):
    """
        @todo Load Settings...
        Iterate over selections
            convert selection to ascii art
            preserve OS line endings and spaces/tabs
            update selections
    """

    def run(
        self, edit, font, directory=None,
        insert_as_comment=None, use_additional_indent=None, comment_style=None,
        width=80, justify=None, direction=None, flip=None, reverse=None
    ):
        self.edit = edit
        newSelections = []
        self.init(
            font, directory, insert_as_comment, use_additional_indent,
            comment_style, width, justify, direction, flip, reverse
        )

        # Loop through user selections & decorate the selections to ASCII Art.
        for selection in self.view.sel():

            line_A = self.view.line( selection.a )
            line_B = self.view.line( selection.b )

            if  line_A == line_B \
            and selection.a == selection.b \
            and self.view.substr( line_A ).strip() != "": # use caret line
                indent = calculate_indent(self.view, line_A)
                line_A = sublime.Region(line_A.begin() + len(indent), line_A.end())
                newSelections.append( self.decorate( self.edit, line_A ) )

            elif line_A == line_B \
            and  selection.a != selection.b \
            and self.view.substr( selection ).strip() != "": # use selection
                newSelections.append( self.decorate( self.edit, selection ) )

            else: # multi line selection
                # Calculate the indentation that must be removed from the first line.
                # Convert the indent into a value representing the size of the white space:
                #     space = 1, tab = (current sublime setting)
                indent = calculate_indent(self.view, selection)
                settings = sublime.load_settings('ASCII Decorator.sublime-settings')
                tab_size = int(settings.get('tab_size', 8))
                char_count = 0
                for c in indent:
                    if c is '\t':
                        char_count += tab_size
                    else:
                        char_count += 1
                lines = []
                for line in self.view.lines( selection ):
                    # Remove the equivalent indentation of each line in the block.
                    # Helps with files that use inconsistent leading indentation (mix of tabs and spaces).
                    text = self.view.substr( line )
                    if text.strip() != "":
                        line_ws = char_count
                        char_removal = 0
                        for c in text:
                            if c == '\t':
                                line_ws -= tab_size
                                char_removal += 1
                            elif c == ' ':
                                char_removal += 1
                                line_ws -= 1
                            else:
                                break
                            if line_ws <= 0:
                                break
                        lines.append(sublime.Region(line.begin() + char_removal, line.end()))

                newSelections.append( self.decorate_multi( self.edit, lines ) )

        # Clear selections since they've been modified.
        self.view.sel().clear()

        for newSelection in newSelections:
            self.view.sel().add( newSelection )

    def init(
        self, font, directory, insert_as_comment, use_additional_indent,
        comment_style, width, justify, direction, flip, reverse
    ):
        """
            Read plugin settings
        """

        settings = sublime.load_settings('ASCII Decorator.sublime-settings')

        if use_additional_indent is not None:
            self.insert_as_comment = insert_as_comment
        else:
            self.insert_as_comment = settings.get("default_insert_as_comment", False)

        if use_additional_indent is not None:
            self.use_additional_indent = use_additional_indent
        else:
            self.use_additional_indent = settings.get("default_insert_as_comment", False)

        self.comment_style = settings.get("default_comment_style_preference", "block") if comment_style is None else comment_style
        if self.comment_style is None or self.comment_style not in ["line", "block"]:
            self.comment_style = "line"

        self.width = settings.get('default_width', 80) if width is None else int(width)

        self.justify = settings.get('default_justify', "auto") if width is None else justify
        if self.justify not in ["auto", "center", "left", "right"]:
            self.justify = "auto"

        self.direction = settings.get('default_direction', "auto") if width is None else direction
        if self.direction not in ["auto", "left-to-right", "right-to-left"]:
            self.direction = "auto"

        self.flip = flip if flip is not None else False
        self.reverse = reverse if reverse is not None else False

        self.font = font
        self.directory = directory

    def decorate_multi( self, edit, currentSelections ):
        """
            Take input and use FIGlet to convert it to ASCII art.
            Normalize converted ASCII strings to use proper line endings and spaces/tabs.
        """

        # Convert the input range to a string, this represents the original selection.
        font_locations = figlet_paths() if self.directory is None else [self.directory]

        # Find where the font resides
        directory = None
        found = False
        for fl in font_locations:
            pth = os.path.join(fl, self.font)
            for ext in (".flf", ".tlf"):
                directory = fl
                if os.path.exists(pth + ext):
                    found = True
                    break
            if found is True:
                break
        assert found is True

        output = []

        for line in currentSelections:
            original = self.view.substr(line)

            # Convert the input string to ASCII Art.
            f = SublimeFiglet(
                directory=directory, font=self.font, width=self.width,
                justify=self.justify, direction=self.direction
            )
            line_output = f.renderText( original )
            if self.reverse is True:
                line_output = line_output.reverse()
            if self.flip is True:
                line_output = line_output.flip()

            if not ST3:
                line_output = line_output.decode("utf-8", "replace")
            output.append(line_output)

        # Normalize line endings based on settings.
        output = self.normalize_line_endings( '\n'.join(output) )
        # Normalize whitespace based on settings.
        totalselection = sublime.Region(currentSelections[0].begin(), currentSelections[-1].end())
        output = self.fix_whitespace( original, output, totalselection )

        self.view.replace( edit, totalselection, output )

        return sublime.Region( totalselection.begin(), totalselection.begin() + len(output) )

    def decorate( self, edit, currentSelection ):
        """
            Take input and use FIGlet to convert it to ASCII art.
            Normalize converted ASCII strings to use proper line endings and spaces/tabs.
        """

        # Convert the input range to a string, this represents the original selection.
        original = self.view.substr( currentSelection )

        font_locations = figlet_paths() if self.directory is None else [self.directory]

        # Find where the font resides
        directory = None
        found = False
        for fl in font_locations:
            pth = os.path.join(fl, self.font)
            for ext in (".flf", ".tlf"):
                directory = fl
                if os.path.exists(pth + ext):
                    found = True
                    break
            if found is True:
                break

        # Convert the input string to ASCII Art.
        assert found is True
        f = SublimeFiglet(
            directory=directory, font=self.font, width=self.width,
            justify=self.justify, direction=self.direction
        )
        output = f.renderText( original )
        if self.reverse is True:
            output = output.reverse()
        if self.flip is True:
            output = output.flip()

        if not ST3:
            output = output.decode("utf-8", "replace")

        # Normalize line endings based on settings.
        output = self.normalize_line_endings( output )
        # Normalize whitespace based on settings.
        output = self.fix_whitespace( original, output, currentSelection )

        self.view.replace( edit, currentSelection, output )

        return sublime.Region( currentSelection.begin(), currentSelection.begin() + len(output) )

    def normalize_line_endings(self, string):
        # Sublime buffers only use '\n', but then normalize all line-endings to
        # the appropriate ending on save.
        string = string.replace('\r\n', '\n').replace('\r', '\n')
        return string

    def fix_whitespace(self, original, prefixed, sel):
        """
            Determine leading whitespace and comments if desired.
        """

        # Determine the indent of the CSS rule
        indent = calculate_indent(self.view, sel)

        # Strip whitespace from the prefixed version so we get it right
        #prefixed = prefixed.strip()
        #prefixed = re.sub(re.compile('^\s+', re.M), '', prefixed)

        # Get comments for current syntax if desired
        comment = ('',)
        if self.insert_as_comment:
            comments = subcomments.get_comment(self.view, sel.begin())
            if len(comments[0]):
                comment = comments[0][0]
            if (self.comment_style == "block" or len(comments[0]) == 0) and len(comments[1]):
                comment = comments[1][0]

        # Indent the prefixed version to the right level
        settings = self.view.settings()
        use_spaces = settings.get('translate_tabs_to_spaces')
        tab_size = int(settings.get('tab_size', 8))

        # Determine if additional indentation is desired
        if self.use_additional_indent:
            indent_characters = '\t'
            if use_spaces:
                indent_characters = ' ' * tab_size
        else:
            indent_characters = ''

        # Prefix the text with desired indentation level, and comments if desired
        if len(comment) > 1:
            prefixed = prefixed.replace('\n', '\n' + indent + indent_characters)
            prefixed = comment[0] + '\n' + indent + indent_characters + prefixed + '\n' + indent + comment[1] + '\n'
        else:
            prefixed = prefixed.replace('\n', '\n' + indent + comment[0] + indent_characters)
            prefixed = comment[0] + indent_characters + prefixed  # add needed indent for first line

        match = re.search('^(\s*)', original)
        prefix = match.groups()[0]
        match = re.search('(\s*)\Z', original)
        suffix = match.groups()[0]
        return remove_trailing_ws(prefixed)
