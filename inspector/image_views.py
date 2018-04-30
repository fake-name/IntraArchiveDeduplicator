
import mimetypes

from PIL import Image

import io
from PIL import Image
import numpy
import scipy.fftpack

from flask import make_response

from . import reader_session_manager
from inspector import app
from inspector import db_pool

HASH_SIZE = 32

def guessItemMimeType(itemName):
	mime_type = mimetypes.guess_type(itemName)
	print("Inferred MIME type %s for file %s" % (mime_type,  itemName))
	if mime_type:
		return mime_type[0]
	return "application/unknown"

def get_image_handle_from_id(rowid):
	with db_pool.db_cursor() as cur:
		cur.execute("""
			SELECT
				fspath,
				internalpath
			FROM
				dedupitems
			WHERE
				dbid = %s
			;""", (rowid, ))

		row = cur.fetchone()

	if not row:
		return None, None

	fspath, intpath = row
	if fspath and not intpath:
		with open(fspath, "rb") as itemFileHandle:
			return fspath, itemFileHandle.read()

	elif fspath and intpath:
		session_manager = reader_session_manager.SessionPoolManager()
		session_manager[("dd", rowid)].checkOpenArchive(fspath)
		itemFileHandle, _ = session_manager[("dd", rowid)].getItemByInternalPath(intpath)
		return intpath, itemFileHandle.read()

	else:
		return None, None

def to_resource(img_path, image_ctnt):

	response = make_response(image_ctnt)
	response.headers['Content-Type']        = guessItemMimeType(img_path)
	response.headers['Content-Disposition'] = "inline; filename=" + img_path.split("/")[-1]
	return response

def get_full_deduper_resource(rowid):
	img_path, image_ctnt = get_image_handle_from_id(rowid)
	return to_resource(img_path, image_ctnt)

def get_resource_color_conversion(rowid):
	img_path, image_ctnt = get_image_handle_from_id(rowid)
	image = Image.open(io.BytesIO(image_ctnt))
	image = image.convert("L")

	out_barr = io.BytesIO()
	image.save(out_barr, format='PNG')
	out_img_ctnt = out_barr.getvalue()
	return to_resource(img_path, out_img_ctnt)

def get_resource_rescaled(rowid):
	img_path, image_ctnt = get_image_handle_from_id(rowid)
	image = Image.open(io.BytesIO(image_ctnt))
	image = image.convert("L")
	image = image.resize((HASH_SIZE, HASH_SIZE), Image.ANTIALIAS)

	# Scale back up with NN resampling, so we can actually look at the output more easily
	image = image.resize((HASH_SIZE * 8, HASH_SIZE * 8), Image.NEAREST)
	out_barr = io.BytesIO()
	image.save(out_barr, format='PNG')
	out_img_ctnt = out_barr.getvalue()
	return to_resource(img_path, out_img_ctnt)

def get_resource_dct_output(rowid):
	img_path, image_ctnt = get_image_handle_from_id(rowid)
	image = Image.open(io.BytesIO(image_ctnt))
	image = image.convert("L")
	image = image.resize((HASH_SIZE, HASH_SIZE), Image.ANTIALIAS)


	pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE, HASH_SIZE))
	dct = scipy.fftpack.dct(pixels)

	image = Image.fromarray(numpy.uint8(dct))

	# Scale back up with NN resampling, so we can actually look at the output more easily
	image = image.resize((HASH_SIZE * 8, HASH_SIZE * 8), Image.NEAREST)
	out_barr = io.BytesIO()
	image.save(out_barr, format='PNG')
	out_img_ctnt = out_barr.getvalue()
	return to_resource(img_path, out_img_ctnt)

def get_resource_truncated_dct(rowid):
	img_path, image_ctnt = get_image_handle_from_id(rowid)
	image = Image.open(io.BytesIO(image_ctnt))
	image = image.convert("L")
	image = image.resize((HASH_SIZE, HASH_SIZE), Image.ANTIALIAS)

	pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE, HASH_SIZE))
	dct = scipy.fftpack.dct(pixels)
	dctlowfreq = dct[:8, 1:9]
	image = Image.fromarray(numpy.uint8(dctlowfreq))

	# Scale back up with NN resampling, so we can actually look at the output more easily
	image = image.resize((HASH_SIZE * 8, HASH_SIZE * 8), Image.NEAREST)
	out_barr = io.BytesIO()
	image.save(out_barr, format='PNG')
	out_img_ctnt = out_barr.getvalue()
	return to_resource(img_path, out_img_ctnt)

def get_resource_truncated_dct_thresholded(rowid):
	img_path, image_ctnt = get_image_handle_from_id(rowid)
	image = Image.open(io.BytesIO(image_ctnt))
	image = image.convert("L")
	image = image.resize((HASH_SIZE, HASH_SIZE), Image.ANTIALIAS)

	pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE, HASH_SIZE))
	dct = scipy.fftpack.dct(pixels)

	image = Image.fromarray(numpy.uint8(dct))

	# Scale back up with NN resampling, so we can actually look at the output more easily
	image = image.resize((HASH_SIZE * 8, HASH_SIZE * 8), Image.NEAREST)
	out_barr = io.BytesIO()
	image.save(out_barr, format='PNG')
	out_img_ctnt = out_barr.getvalue()
	return to_resource(img_path, out_img_ctnt)



# def phash(image, hash_size=32):
# 	image = image.convert("L").resize((hash_size, hash_size), Image.ANTIALIAS)
# 	pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((hash_size, hash_size))
# 	dct = scipy.fftpack.dct(pixels)
# 	dctlowfreq = dct[:8, 1:9]
# 	avg = dctlowfreq.mean()
# 	diff = dctlowfreq > avg
# 	return ImageHash(diff), image
# im = Image.open(io.BytesIO(fContents))


@app.route('/debug/scraper_resource/whole_image/<int:rowid>', methods=['GET'])
def image_resource_original(rowid):
	return get_full_deduper_resource(rowid)


@app.route('/debug/scraper_resource/step_1/<int:rowid>', methods=['GET'])
def image_resource_color_conversion(rowid):
	return get_resource_color_conversion(rowid)

@app.route('/debug/scraper_resource/step_2/<int:rowid>', methods=['GET'])
def image_resource_rescaled(rowid):
	return get_resource_rescaled(rowid)

@app.route('/debug/scraper_resource/step_3/<int:rowid>', methods=['GET'])
def image_resource_dct_output(rowid):
	return get_resource_dct_output(rowid)

@app.route('/debug/scraper_resource/step_4/<int:rowid>', methods=['GET'])
def image_resource_truncated_dct(rowid):
	return get_resource_truncated_dct(rowid)

@app.route('/debug/scraper_resource/step_5/<int:rowid>', methods=['GET'])
def image_resource_truncated_dct_thresholded(rowid):
	return get_resource_truncated_dct_thresholded(rowid)



