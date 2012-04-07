import sublime, sublime_plugin, os, re
from pyfiglet import Figlet

class FigletCommand( sublime_plugin.TextCommand ):
	"""
		@todo Load Settings...
    	Iterate over selections
    		convert selection to ascii art
    		preserve OS line endings and spaces/tabs
    		update selections
	"""
	def run( self, edit ):
		newSelections = []

		# Create an() edit object, demarcating an undo group.
		edit = self.view.begin_edit( 'ASCII Decorator' )

		# Loop through user selections.
		for currentSelection in self.view.sel():
			# Decorate the selection to ASCII Art.
			newSelections.append( self.decorate( edit, currentSelection ) )

		# Clear selections since they've been modified.
		self.view.sel().clear()

		for newSelection in newSelections:
			self.view.sel().add( newSelection )

		# A corresponding call to end_edit() is required.
		self.view.end_edit( edit )

	"""
		Take input and use FIGlet to convert it to ASCII art.
		Normalize converted ASCII strings to use proper line endings and spaces/tabs.
	"""
	def decorate( self, edit, currentSelection ):
		# Convert the input range to a string, this represents the original selection.
		original = self.view.substr( currentSelection );
		# Construct a local path to the fonts directory.
		fontsDir = os.path.join(sublime.packages_path(), 'ASCII Decorator', 'pyfiglet', 'fonts')
		# Convert the input string to ASCII Art.
		settings = sublime.load_settings('ASCII Decorator.sublime-settings')
		f = Figlet( dir=fontsDir, font=settings.get('ascii_decorator_font') )
		output = f.renderText( original );

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

		print indent
		# Strip whitespace from the prefixed version so we get it right
		#prefixed = prefixed.strip()
		#prefixed = re.sub(re.compile('^\s+', re.M), '', prefixed)

		# Indent the prefixed version to the right level
		settings = self.view.settings()
		use_spaces = settings.get('translate_tabs_to_spaces')
		tab_size = int(settings.get('tab_size', 8))
		indent_characters = '\t'
		if use_spaces:
			indent_characters = ' ' * tab_size
		prefixed = prefixed.replace('\n', '\n' + indent + indent_characters)
		prefixed = indent_characters + prefixed  # add needed indent for first line

		match = re.search('^(\s*)', original)
		prefix = match.groups()[0]
		match = re.search('(\s*)\Z', original)
		suffix = match.groups()[0]
		return prefixed
