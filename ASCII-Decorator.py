import sublime
import sublime_plugin
import os
import re
import sys
import traceback
from zipfile import ZipFile, is_zipfile

ST3 = int(sublime.version()) >= 3000

if not ST3:
    import pyfiglet
else:
    from . import pyfiglet

PACKAGE_LOCATION = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DIR = os.path.join(PACKAGE_LOCATION, "pyfiglet", "fonts")
USER_DIR = None


def get_comment(view, pt):
    """
    Ripped from Sublime's Default.comment.py to find comment convention
    """

    shell_vars = view.meta_info("shellVariables", pt)
    if not shell_vars:
        return ('',)

    # transform the list of dicts into a single dict
    all_vars = {}
    for v in shell_vars:
        if 'name' in v and 'value' in v:
            all_vars[v['name']] = v['value']

    line_comments = []
    block_comments = []

    # transform the dict into a single array of valid comments
    suffixes = [""] + ["_" + str(i) for i in range(1, 10)]
    for suffix in suffixes:
        start = all_vars.setdefault("TM_COMMENT_START" + suffix)
        end = all_vars.setdefault("TM_COMMENT_END" + suffix)

        if start and end is None:
            line_comments.append((start,))
        elif start and end:
            block_comments.append((start, end))


    return (line_comments, block_comments)


class SublimeFigletFont(pyfiglet.FigletFont):
    def __init__(self, font=pyfiglet.DEFAULT_FONT, directory=DEFAULT_DIR):
        self.font = font
        self.comment = ''
        self.chars = {}
        self.width = {}
        self.data = self.preloadFont(font, directory)
        self.loadFont()

    @classmethod
    def preloadFont(cls, font, directory=DEFAULT_DIR):
        """
        Load font file into memory. This can be overriden with
        a superclass to create different font sources.
        """

        fontPath = os.path.join(directory, font + '.flf')
        if not os.path.exists(fontPath):
            fontPath = os.path.join(directory, font + '.tlf')
            if not os.path.exists(fontPath):
                raise pyfiglet.FontNotFound("%s doesn't exist" % font)

        if is_zipfile(fontPath):
            z = None
            try:
                z = ZipFile(fontPath, 'r')
                data = z.read(z.getinfo(z.infolist()[0].filename))
                z.close()
                return data.decode('utf-8', 'replace') if ST3 else data
            except Exception as e:
                if z is not None:
                    z.close()
                raise pyfiglet.FontError("couldn't read %s: %s" % (fontPath, e))
        else:
            try:
                with open(fontPath, 'rb') as f:
                    data = f.read()
                return data.decode('utf-8', 'replace') if ST3 else data
            except Exception as e:
                raise pyfiglet.FontError("couldn't open %s: %s" % (fontPath, e))

        raise pyfiglet.FontNotFound(font)

    @classmethod
    def getFonts(cls, directory=DEFAULT_DIR):
        return [font[:-4] for font in os.walk(dir).next()[2] if font.endswith(('.flf', '.tlf'))]


class SublimeFiglet(pyfiglet.Figlet):
    def __init__(
        self, font=pyfiglet.DEFAULT_FONT, direction='auto',
        justify='auto', width=80, directory=DEFAULT_DIR
    ):
        self.font = font
        self._direction = direction
        self._justify = justify
        self.width = width
        self.setFont(directory=directory)
        self.engine = pyfiglet.FigletRenderingEngine(base=self)

    def setFont(self, **kwargs):
        directory = kwargs.get('directory', None)

        if 'font' in kwargs:
            self.font = kwargs['font']

        self.Font = SublimeFigletFont(font=self.font, directory=directory)

    def getFonts(self, directory=DEFAULT_DIR):
        return self.Font.getFonts(directory)


class UpdateFigletPreviewCommand(sublime_plugin.TextCommand):
    """
        A reasonable edit command that works in ST2 and ST3
    """

    preview = None
    def run(self, edit, font, directory=None):
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
                    "font": font, "directory": directory,
                    "use_additional_indent": False, "insert_as_comment": False
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


class FigletMenuCommand( sublime_plugin.TextCommand ):
    def run( self, edit ):
        self.undo = False
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')

        # Find directory locations
        font_locations = []
        for loc in [USER_DIR, DEFAULT_DIR]:
            if loc is not None:
                font_locations.append(loc)

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


class FigletCommand( sublime_plugin.TextCommand ):
    """
        @todo Load Settings...
        Iterate over selections
            convert selection to ascii art
            preserve OS line endings and spaces/tabs
            update selections
    """

    def run(
        self, edit, font=None, directory=None,
        insert_as_comment=None, use_additional_indent=None, comment_style=None
        width=80, justify=None, direction=None
    ):
        self.edit = edit
        newSelections = []
        self.init(
            font, directory, insert_as_comment, use_additional_indent,
            comment_style, width, justify, direction
        )

        # Loop through user selections.
        for currentSelection in self.view.sel():
            # Decorate the selection to ASCII Art.
            if currentSelection.size():
                newSelections.append( self.decorate( self.edit, currentSelection ) )
            else:
                newSelections.append(currentSelection)

        # Clear selections since they've been modified.
        self.view.sel().clear()

        for newSelection in newSelections:
            self.view.sel().add( newSelection )

    def init(
        self, font, directory, insert_as_comment, use_additional_indent,
        comment_style, width, justify, direction
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

        self.font = settings.get('ascii_decorator_font', "slant") if font is None else font
        self.directory = directory

    def decorate( self, edit, currentSelection ):
        """
            Take input and use FIGlet to convert it to ASCII art.
            Normalize converted ASCII strings to use proper line endings and spaces/tabs.
        """

        # Convert the input range to a string, this represents the original selection.
        original = self.view.substr( currentSelection );

        if self.directory is None:
            # Create a list of locations to search
            font_locations = []
            for loc in [USER_DIR, DEFAULT_DIR]:
                if loc is not None:
                    font_locations.append(loc)
        else:
            font_locations = [self.directory]

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

        # Normalize line endings based on settings.
        output = self.normalize_line_endings( output )
        # Normalize whitespace based on settings.
        output = self.fix_whitespace( original, output, currentSelection )

        self.view.replace( edit, currentSelection, output )

        return sublime.Region( currentSelection.begin(), currentSelection.begin() + len(output) )

    def normalize_line_endings(self, string):
        string = string.replace('\r\n', '\n').replace('\r', '\n')
        line_endings = self.view.settings().get('default_line_ending')
        if line_endings == 'windows':
            string = string.replace('\n', '\r\n')
        elif line_endings == 'mac':
            string = string.replace('\n', '\r')
        return string

    def fix_whitespace(self, original, prefixed, sel):
        """
            Determine leading whitespace and comments if desired.
        """

        # Determine the indent of the CSS rule
        (row, col) = self.view.rowcol(sel.begin())
        indent_region = self.view.find('^\s+', self.view.text_point(row, 0))
        if indent_region and self.view.rowcol(indent_region.begin())[0] == row:
            indent = self.view.substr(indent_region)
        else:
            indent = ''

        # Strip whitespace from the prefixed version so we get it right
        #prefixed = prefixed.strip()
        #prefixed = re.sub(re.compile('^\s+', re.M), '', prefixed)

        # Get comments for current syntax if desired
        comment = ('',)
        if self.insert_as_comment:
            comments = get_comment(self.view, sel.begin())
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

        # Prefix the text with desired identation level, and comments if desired
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
        return prefixed


def setup_custom_font_dir():
    """
        Create custom doc folder if missing.  Set USER_DIR
        to None if anything goes wrong.
    """

    global USER_DIR
    USER_DIR = os.path.join(sublime.packages_path(), "User", "ASCII Decorator Fonts")

    if not os.path.exists(USER_DIR):
        try:
            os.makedirs(USER_DIR)
        except:
            pass

    if not os.path.exists(USER_DIR):
        USER_DIR = None


def plugin_loaded():
    """
        Setup plugin
    """
    setup_custom_font_dir()


if not ST3:
    plugin_loaded()
