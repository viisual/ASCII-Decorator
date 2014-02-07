import sublime, sublime_plugin, os, re, sys
if sys.version_info < (3,0,0):
    ST2 = True
    from pyfiglet import Figlet
    from pyfiglet import faux_pkg_resources
    FONT_MODULE = "pyfiglet.fonts"
else:
    ST2 = False
    from .pyfiglet import Figlet
    from .pyfiglet import faux_pkg_resources
    FONT_MODULE = "ASCII Decorator.pyfiglet.fonts"


PACKAGE_LOCATION = os.path.abspath(os.path.dirname(__file__))


def get_comment(view, pt):
    """
    Ripped from Sublime's Default.comment.py
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


class UpdateFigletPreviewCommand(sublime_plugin.TextCommand):
    preview = None
    def run(self, edit, font, dir):
        preview = UpdateFigletPreviewCommand.get_buffer()
        if preview is not None:
            self.view.replace(edit, sublime.Region(0, self.view.size()), preview)
            sel = self.view.sel()
            sel.clear()
            sel.add(sublime.Region(0, self.view.size()))
            self.view.run_command("figlet", {"font": font, "dir": dir})
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
        if ST2:
            faux_pkg_resources.set_relative_path(PACKAGE_LOCATION)
        self.undo = False
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        self.options = []
        fonts = FONT_MODULE.rsplit('.', 1)
        for f in faux_pkg_resources.resource_listdir(*fonts):
            if f.endswith(('.flf', '.tlf')):
                self.options.append(f)
        if len(self.options):
            if ST2:
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
        if value != -1:
            sel = self.view.sel()
            example = None
            for s in sel:
                if s.size():
                    example = self.view.substr(s)
            if example is None:
                return
            syntax = self.view.settings().get('syntax')
            view = self.view.window().get_output_panel('figlet_preview')
            view.settings().set('syntax', syntax)
            self.view.window().run_command("show_panel", {"panel": "output.figlet_preview"})
            UpdateFigletPreviewCommand.set_buffer(example)
            view.run_command(
                "update_figlet_preview",
                {
                    "font": self.options[value][:-4],
                    "dir": FONT_MODULE
                }
            )

    def apply_figlet(self, value):
        self.view.window().run_command("hide_panel", {"panel": "output.figlet_preview"})
        if value != -1:
            self.view.run_command(
                "figlet",
                {
                    "font": self.options[value][:-4],
                    "dir": FONT_MODULE
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
    def run( self, edit, font=None, dir=None ):
        if ST2:
            faux_pkg_resources.set_relative_path(PACKAGE_LOCATION)
        self.edit = edit
        newSelections = []

        # Loop through user selections.
        for currentSelection in self.view.sel():
            # Decorate the selection to ASCII Art.
            newSelections.append( self.decorate( self.edit, currentSelection, font, dir ) )

        # Clear selections since they've been modified.
        self.view.sel().clear()

        for newSelection in newSelections:
            self.view.sel().add( newSelection )


    """
        Take input and use FIGlet to convert it to ASCII art.
        Normalize converted ASCII strings to use proper line endings and spaces/tabs.
    """
    def decorate( self, edit, currentSelection, font, dir):
        # Convert the input range to a string, this represents the original selection.
        original = self.view.substr( currentSelection );

        settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        if font is None:
            font = settings.get('ascii_decorator_font')

        # Convert the input string to ASCII Art.
        found = False
        for ext in ("flf", "tlf"):
            if faux_pkg_resources.resource_exists(FONT_MODULE, "%s.%s" % (font, ext)):
                found = True
                break

        assert found is True
        f = Figlet( dir=FONT_MODULE, font=font )
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
        plugin_settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        comment = ('',)
        if plugin_settings.get("insert_as_comment", False):
            comment_style = plugin_settings.get("comment_style_preference", "block")
            if comment_style is None or comment_style not in ["line", "block"]:
                comment_style = "line"
            comments = get_comment(self.view, sel.begin())
            if len(comments[0]):
                comment = comments[0][0]
            if (comment_style == "block" or len(comments[0]) == 0) and len(comments[1]):
                comment = comments[1][0]

        # Indent the prefixed version to the right level
        settings = self.view.settings()
        use_spaces = settings.get('translate_tabs_to_spaces')
        tab_size = int(settings.get('tab_size', 8))
        if plugin_settings.get("use_additional_indent", True):
            indent_characters = '\t'
            if use_spaces:
                indent_characters = ' ' * tab_size
        else:
            indent_characters = ''
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
