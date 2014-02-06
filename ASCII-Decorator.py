import sublime, sublime_plugin, os, re, sys
if sys.version_info < (3,0,0):
    from pyfiglet import Figlet
else:
    from .pyfiglet import Figlet


def get_comment(view, pt):
    """
    Ripped from Sublime's Default.comment.py
    """

    shell_vars = view.meta_info("shellVariables", pt)
    if not shell_vars:
        return ('')

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


class FigletStatus(object):
    error = False


class FigletMenuCommand( sublime_plugin.TextCommand ):
    def run( self, edit ):
        self.undo = False
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        fontsDir = os.path.join(sublime.packages_path(), 'ASCII Decorator', 'pyfiglet', 'fonts')
        self.options = []
        for f in os.listdir(fontsDir):
            if os.path.isfile(os.path.join(fontsDir, f)) and f.endswith(".flf"):
                self.options.append(f[:-4])
        if len(self.options):
            self.view.window().show_quick_panel(
                self.options,
                self.apply_figlet,
                on_highlight=self.preview if bool(settings.get("show_preview", False)) else None
            )

    def preview(self, value):
        if value != -1:
            if self.undo:
                if FigletStatus.error:
                    FigletStatus.error = False
                else:
                    self.view.run_command("undo")
            else:
                self.undo = True
            self.view.run_command("figlet", {"font": self.options[value]})

    def apply_figlet(self, value):
        if value != -1:
            self.view.run_command("figlet", {"font": self.options[value]})
        else:
            if self.undo:
                if FigletStatus.error:
                    FigletStatus.error = False
                else:
                    self.view.run_command("undo")


class FigletCommand( sublime_plugin.TextCommand ):
    """
        @todo Load Settings...
        Iterate over selections
            convert selection to ascii art
            preserve OS line endings and spaces/tabs
            update selections
    """
    def run( self, edit, font=None ):
        FigletStatus.error = False

        self.edit = edit
        newSelections = []

        # Loop through user selections.
        for currentSelection in self.view.sel():
            # Decorate the selection to ASCII Art.
            newSelections.append( self.decorate( self.edit, currentSelection, font ) )

        # Clear selections since they've been modified.
        self.view.sel().clear()

        for newSelection in newSelections:
            self.view.sel().add( newSelection )


    """
        Take input and use FIGlet to convert it to ASCII art.
        Normalize converted ASCII strings to use proper line endings and spaces/tabs.
    """
    def decorate( self, edit, currentSelection, font ):
        # Convert the input range to a string, this represents the original selection.
        original = self.view.substr( currentSelection );
        # Construct a local path to the fonts directory.
        fontsDir = os.path.join(sublime.packages_path(), 'ASCII Decorator', 'pyfiglet', 'fonts')
        # Convert the input string to ASCII Art.
        settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        if font is None or not os.path.exists(os.path.join(fontsDir, font + ".flf")):
            font = settings.get('ascii_decorator_font')

        try:
            f = Figlet( dir=fontsDir, font=font )
            output = f.renderText( original );
        except:
            # Set the global error status
            # This will allow the quick panel
            # function to be aware that something
            # went wrong during preview
            FigletStatus.error = True
            raise

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
