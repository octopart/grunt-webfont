# Based on https://github.com/FontCustom/fontcustom/blob/master/lib/fontcustom/scripts/generate.py

import fontforge
import os
import argparse
import md5
import json
from subprocess import call
from distutils.spawn import find_executable


parser = argparse.ArgumentParser(description='Convert a directory of SVG and EPS files into a unified font file.')
parser.add_argument('input_dir', metavar='directory', type=unicode, help='directory of vector files')
parser.add_argument('output_dir', metavar='directory', type=unicode, help='output directory')
parser.add_argument('font', metavar='font', type=unicode, help='font name')
parser.add_argument('types', metavar='types', type=lambda s: s.split(','), help='output types')
parser.add_argument('--hashes', action='store_true', help='add hashes to file names')
args = parser.parse_args()


f = fontforge.font()
f.encoding = 'UnicodeFull'

m = md5.new()
cp = 0xf100
files = []

KERNING = 15

for dirname, dirnames, filenames in os.walk(args.input_dir):
	for filename in sorted(filenames):
		name, ext = os.path.splitext(filename)
		filePath = os.path.join(dirname, filename)
		size = os.path.getsize(filePath)

		if ext in ['.svg', '.eps']:
			if ext in ['.svg']:
				# HACK: Remove <switch> </switch> tags
				svgfile = open(filePath, 'r+')
				svgtext = svgfile.read()
				svgfile.seek(0)

				# Replace the <switch> </switch> tags with nothing
				svgtext = svgtext.replace('<switch>', '')
				svgtext = svgtext.replace('</switch>', '')

				# Remove all contents of file so that we can write out the new contents
				svgfile.truncate()
				svgfile.write(svgtext)
				svgfile.close()

			m.update(filename + str(size) + ';')
			glyph = f.createChar(cp)
			glyph.importOutlines(filePath)

			glyph.left_side_bearing = KERNING
			glyph.right_side_bearing = KERNING

			# possible optimization?
			# glyph.simplify()
			# glyph.round()

			files.append(name)
			cp += 1

fontfile = args.output_dir + '/' + args.font
if args.hashes:
	fontfile += '-' + m.hexdigest()

f.fontname = args.font
f.familyname = args.font
f.fullname = args.font

# TTF
f.generate(fontfile + '.ttf')

# SVG
if 'svg' in args.types:
	f.generate(fontfile + '.svg')

	# Fix SVG header for webkit (from: https://github.com/fontello/font-builder/blob/master/bin/fontconvert.py)
	svgfile = open(fontfile + '.svg', 'r+')
	svgtext = svgfile.read()
	svgfile.seek(0)
	svgfile.write(svgtext.replace('<svg>', '<svg xmlns="http://www.w3.org/2000/svg">'))
	svgfile.close()

scriptPath = os.path.dirname(os.path.realpath(__file__))

# WOFF
if 'woff' in args.types:
	call(['sfnt2woff', fontfile + '.ttf'])

# EOT
if 'eot' in args.types:
	# eotlitetool.py script to generate IE7-compatible .eot fonts
	call('python ' + scriptPath + '/eotlitetool.py ' + fontfile + '.ttf -o ' + fontfile + '.eot', shell=True)
	call('mv ' + fontfile + '.eotlite ' + fontfile + '.eot', shell=True)

# Hint the TTF file or delete it if not needed
# ttfautohint is optional
if 'ttf' in args.types:
	if find_executable('ttfautohint'):
		call('ttfautohint -s -n ' + fontfile + '.ttf ' + fontfile + '-hinted.ttf && mv ' + fontfile + '-hinted.ttf ' + fontfile + '.ttf', shell=True)
else:
	os.remove(fontfile + '.ttf')

print json.dumps({'file': fontfile, 'names': files})
