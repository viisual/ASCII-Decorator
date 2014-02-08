import sublime
import sublime_plugin
import os
import re
import sys
import traceback

ST3 = int(sublime.version()) >= 3000
FONT_MODULE = "pyfiglet.fonts" if not ST3 else "ASCII Decorator.pyfiglet.fonts"
USER_MODULE = "ASCII Decorator Fonts" if not ST3 else "User.ASCII Decorator Fonts"
PACKAGE_LOCATION = os.path.abspath(os.path.dirname(__file__))


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


class UpdateFigletPreviewCommand(sublime_plugin.TextCommand):
    """
        A reasonable edit command that works in ST2 and ST3
    """

    preview = None
    def run(self, edit, font, module):
        preview = UpdateFigletPreviewCommand.get_buffer()
        if not ST3:
            preview = preview.encode('UTF-8')
        if preview is not None:
            self.view.replace(edit, sublime.Region(0, self.view.size()), preview)
            sel = self.view.sel()
            sel.clear()
            sel.add(sublime.Region(0, self.view.size()))
            self.view.run_command("figlet", {"font": font, "module": module})
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

        # Find module locations
        font_locations = []
        for loc in [USER_MODULE, FONT_MODULE]:
            if loc is not None:
                font_locations.append(loc)

        # Find available fonts
        self.options = []
        for fl in font_locations:
            print(fl)
            for f in pkg_resources.resource_listdir(fl, ''):
                if f.endswith(('.flf', '.tlf')):
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
            syntax = self.view.settings().get('syntax')
            view = self.view.window().get_output_panel('figlet_preview')
            view.settings().set('syntax', syntax)
            self.view.window().run_command("show_panel", {"panel": "output.figlet_preview"})

            # Preview
            UpdateFigletPreviewCommand.set_buffer(example)
            view.run_command(
                "update_figlet_preview",
                {
                    "font": self.options[value][:-4],
                    "module": FONT_MODULE
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
                    "font": self.options[value][:-4],
                    "module": FONT_MODULE
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

    def run( self, edit, font=None, module=None ):
        self.edit = edit
        newSelections = []

        # Loop through user selections.
        for currentSelection in self.view.sel():
            # Decorate the selection to ASCII Art.
            if currentSelection.size():
                newSelections.append( self.decorate( self.edit, currentSelection, font, module ) )
            else:
                newSelections.append(currentSelection)

        # Clear selections since they've been modified.
        self.view.sel().clear()

        for newSelection in newSelections:
            self.view.sel().add( newSelection )

    def decorate( self, edit, currentSelection, font, module):
        """
            Take input and use FIGlet to convert it to ASCII art.
            Normalize converted ASCII strings to use proper line endings and spaces/tabs.
        """

        # Convert the input range to a string, this represents the original selection.
        original = self.view.substr( currentSelection );

        settings = sublime.load_settings('ASCII Decorator.sublime-settings')
        if font is None:
            font = settings.get('ascii_decorator_font')

        # Create a list of locations to search
        font_locations = []
        for loc in [USER_MODULE, FONT_MODULE]:
            if loc is not None:
                font_locations.append(loc)

        # Find where the font resides
        module = None
        found = False
        for ext in ("flf", "tlf"):
            for fl in font_locations:
                module = fl
                if pkg_resources.resource_exists(fl, "%s.%s" % (font, ext)):
                    found = True
                    break
            if found:
                break

        # Convert the input string to ASCII Art.
        assert found is True
        f = pyfiglet.Figlet( module=module, font=font )
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

        # Determine if additional indentation is desired
        if plugin_settings.get("use_additional_indent", True):
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


class CustomImport(object):
    """
        Sublime Text 2 imports plugin modules in a silly way.  The paths of all modules
        are not relative to the current working directory. This makes it so pkg_resources
        cannot resolve them.  This importer does not need to be used on ST3 since ST3 does
        things in a sane way.
    """

    def __init__(self, path):
        self.packages = path

    def load_module(self, module_name):
        """
            Load the module and ensure a sane path for modules that will be accessed
            via pkg_resources.
        """
        import warnings
        import imp

        # Determine the module file name
        file_name = os.path.join(self.packages, os.path.normpath(module_name.replace('.', '/')))
        is_dir = os.path.isdir(file_name)
        if is_dir:
            file_name = os.path.join(file_name, '__init__')
        else:
            filename = os.path.dirname(file_name)
        file_name += ".py"

        # Determine the module path
        path_name = os.path.join(self.packages, os.path.normpath(module_name.rsplit('.', 1)[0].replace('.', '/')))

        # @todo find a better reload methodology that works
        # currently remove and imp.remove have a difficult time with this
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Load the modulue
        with warnings.catch_warnings(record=True) as w:
            # Ignore warnings about plugin folder not being a python package
            warnings.simplefilter("always")
            module = imp.new_module(module_name)
            module.__loader__ = self
            module.__file__ = file_name
            module.__path__ = [path_name]
            sys.modules[module_name] = module
            source = None
            with open(file_name) as f:
                source = f.read().replace('\r', '')
            self.__execute_module(source, module_name)
            w = filter(lambda i: issubclass(i.category, UserWarning), w)
        return module

    def __execute_module(self, source, module_name):
        """
            Execute the module
        """

        exec(compile(source, module_name, 'exec'), sys.modules[module_name].__dict__)


def setup_custom_font_dir():
    """
        Create custom doc folder if missing and attempt to load the doc folder
        to ensure it is working, and pkg_resources can find it later.  Set USER_MODULE
        to None if anything goes wrong.
    """

    global USER_MODULE

    # Create custom font directory
    custom_dir = sublime.packages_path() if ST3 else os.path.join(sublime.packages_path(), "User")
    for part in USER_MODULE.split('.'):
        custom_dir = os.path.join(custom_dir, part)

    if not os.path.exists(custom_dir):
        try:
            os.makedirs(custom_dir)
        except:
            pass

    # Add __init__ file so the folder can be viewed as a module
    init_file = os.path.join(custom_dir, '__init__.py')
    if os.path.exists(custom_dir) and not os.path.exists(init_file):
        try:
            with open(init_file, "w") as f:
                f.write('')
        except:
            pass

    try:
        # See if custom font module can be loaded
        if not ST3:
            # Load up pyfiglet with custom importer for access with pkg_resources (ST2 only)
            CustomImport(os.path.join(sublime.packages_path(), "User")).load_module(USER_MODULE)
        else:
            __import__(USER_MODULE)
    except:
        # There was a problem loading custom font module. Do not use it.
        print(str(traceback.format_exc()))
        USER_MODULE = None


def setup_modules():
    """
        Load up pkg_resources and distutils if required.  Load up pyfiglet.
        Pyfiglet will be loaded via the special importer (ST2 only).
    """

    global pkg_resources
    global pyfiglet
    pyfiglet = None
    if not ST3:
        if "distutils" not in sys.modules:
            modules = os.path.join(PACKAGE_LOCATION, "modules", "ST2")
            if modules not in sys.path:
                sys.path.append(modules)

    if "pkg_resources" not in sys.modules:
        modules = os.path.join(PACKAGE_LOCATION, "modules")
        if modules not in sys.path:
            sys.path.append(modules)

    if not ST3:
        import pkg_resources
        # Register custom importer with pkg_resources
        pkg_resources.register_loader_type(CustomImport, pkg_resources.DefaultProvider)
        # Load up pyfiglet with custom importer for access with pkg_resources (ST2 only)
        pyfiglet = CustomImport(os.path.join(PACKAGE_LOCATION)).load_module("pyfiglet")
    else:
        import pkg_resources
        from . import pyfiglet


def plugin_loaded():
    """
        Setup plugin
    """
    setup_custom_font_dir()
    setup_modules()


if not ST3:
    plugin_loaded()
