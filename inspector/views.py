

# from guess_language import guess_language

import markdown
import os.path

from flask import render_template
from flask import send_file
from flask import g

import traceback


from inspector import app
import inspector.debug_views




@app.errorhandler(404)
def not_found_error(dummy_error):
	print("404. Wat?")
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(dummy_error):
	print("Internal Error!")
	print(dummy_error)
	print(traceback.format_exc())
	# print("500 error!")
	return render_template('500.html'), 500




@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():

	interesting = ""
	if os.path.exists("todo.md"):
		with open("todo.md", "r") as fp:
			raw_text = fp.read()
		interesting = markdown.markdown(raw_text, extensions=["linkify"])

	return render_template('index.html',
						   title               = 'Home',
						   interesting_links   = interesting,
						   )

@app.route('/favicon.ico')
def sendFavIcon():
	return send_file(
		"./static/favicon.ico",
		conditional=True
		)



