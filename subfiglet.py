import sublime
import os
from zipfile import ZipFile, is_zipfile

ST3 = int(sublime.version()) >= 3000

if not ST3:
    import pyfiglet
else:
    from . import pyfiglet


PACKAGE_LOCATION = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DIR = os.path.join(PACKAGE_LOCATION, "pyfiglet", "fonts")
USER_DIR = None


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


def figlet_paths():
    font_locations = []
    for loc in [USER_DIR, DEFAULT_DIR]:
        if loc is not None:
            font_locations.append(loc)
    return font_locations


def plugin_loaded():
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


if not ST3:
    plugin_loaded()
