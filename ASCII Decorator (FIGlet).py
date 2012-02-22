import sublime, sublime_plugin
import os, re
from pyfiglet import Figlet

class FigletCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for sel in self.view.sel():
			self.replace_selection(sel)

	def replace_selection(self, sel):
		tempDir = sublime.packages_path()+os.sep+'ASCII Decorator (FIGlet)'+os.sep+'pyfiglet'+os.sep+'fonts'
		f = Figlet(dir=tempDir, font='slant') # or zipfile=PATH
		original = self.view.substr(sel);
		result = f.renderText(original);
		edit = self.view.begin_edit('Figlet')
		#result = self.normalize_line_endings(result)
		(prefix, main, suffix) = self.fix_whitespace(original, '\n' + result, sel)
		self.view.replace(edit, sel, prefix + main + suffix)
		self.view.end_edit(edit)
		# Clear selections since they've been modified.
		self.view.sel().clear()  
		return

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

		# Indent the prefixed version to the right level
		settings = self.view.settings()
		use_spaces = settings.get('translate_tabs_to_spaces')
		tab_size = int(settings.get('tab_size', 8))
		indent_characters = '\t'
		if use_spaces:
			indent_characters = ' ' * tab_size
		prefixed = prefixed.replace('\n', '\n' + indent + indent_characters)

		match = re.search('^(\s*)', original)
		prefix = match.groups()[0]
		match = re.search('(\s*)\Z', original)
		suffix = match.groups()[0]

		return ('', prefixed, '')