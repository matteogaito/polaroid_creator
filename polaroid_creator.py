from PIL import Image, ImageOps, ImageFont, ImageDraw
import glob
import sys
import logging
import os
from pathlib import Path
from optparse import OptionParser

def GetImageInfos(filename):
    infos = {}
    original_im = Image.open(filename)
    original_size = original_im.size

    #Get lower side
    if original_size[0] > original_size[1]:
        side = original_size[1]
        factor = "landscape"
    else:
        side = original_size[0]
        factor = "portrait"

    logging.info("Factor: {}, Side: {}".format(factor,side))

    infos['factor'] = factor
    infos['side'] = side
    infos['filename'] = os.path.basename(filename)
    infos['extension'] = os.path.splitext(filename)[1]
    filename_w_ext = os.path.basename(filename)
    infos['filename'], infos['extension'] = os.path.splitext(filename_w_ext)
    return(infos)

def createSquare(filename):
    infos = GetImageInfos(filename)
    original_im = Image.open(filename)

    square_pic_size = (infos['side'], infos['side'])

    square_pic = Image.new("RGB", square_pic_size)
    # Put image in the center
    if infos['factor'] == "landscape":
        centring = int((infos['side'] - original_im.size[0])/2)
        square_pic.paste(original_im, (centring, 0))
    elif infos['factor'] == "portrait":
        centring = int((infos['side'] - original_im.size[1])/2)
        square_pic.paste(original_im, (0, centring))

    square_pic.save('squares/square_' + infos['filename'] + infos['extension'])
    return(square_pic)

def createImage(filename):
    infos = GetImageInfos(filename)
    original_im = Image.open(filename)
    return(original_im)

def resize_image( image, base=None, height=None ):
    orig_base, orig_height = image.size
    
    if base is None and height is None:
        logging.error('At least one of base or height must be specified')
        return image
    
    if base and height:
        if orig_base == base and orig_height == height:
            logging.info('Resizing img')
            return(image.resize((base,height), Image.Resampling.LANCZOS))

    if base:
        new_base = base
        new_height = int((new_base / orig_base) * orig_height)
    else:
        new_height = height
        new_base = int((new_height / orig_height) * orig_base)

    logging.info('Resizing img with calculated aspect ratio')
    return(image.resize((new_base,new_height), Image.Resampling.LANCZOS))

def get_biggest_sizes(images_array):
    h = []
    w = []
    biggests = []
    for image in images_array:
        w.append(image.size[0])
        h.append(image.size[1])

    biggests.append(max(w))
    biggests.append(max(h))
    return(biggests)


def createStrip(images_array, strip_name, delimiter=False):
    num_elements = len(images_array)
    w, h = get_biggest_sizes(images_array=images_array) 

    if delimiter:
        line = 5
        logging.info("Show Delimiter")
    else:
        line = 0

    strip_size = ( ( ( w * num_elements) + (line * 3)), ( h + line ) )
    strip = Image.new("RGB", strip_size, color=("Black"))
    goforward = 0
    for image in images_array:
        logging.info("image base {} height {}".format(image.size[0],image.size[1]))
        strip.paste(image, (goforward + line, line))
        goforward = goforward + w + line

    logging.info('saving strip {}'.format(strip_name))
    strip.save('output/' + strip_name)

# Main
strip_num = 1
squares = []

img_exts = [ 'JPG', 'jpg' ]

logging.basicConfig(level=logging.INFO)

parser = OptionParser()
parser.add_option("-d", "--directory", dest="src_dir", default=False, type="string", help="Source files directory")
parser.add_option("-r", "--row", dest="row_num", type="int", default=2, help="Number of element in a row")
parser.add_option("-D", "--delimiter", dest="delimiter", default=True, action='store_true', help="Show delimiter")
parser.add_option("-t", "--add-text", dest="add_text", default=False, help="Text to add to bottom to the polaroid")
parser.add_option("--use-filename-astext", dest="add_filenametext", default=False, action='store_true', help="Use the filename as text")
parser.add_option("--as_square", dest="as_square", default=False, action='store_true', help="cut to have square" )
(options, args) = parser.parse_args()

if options.src_dir == False:
    parser.print_help()
    parser.error( "Give source image path" )

logging.info("Source Directory: {}, Element in row: {}, Delimiter: {}, Text: {}".format(options.src_dir, options.row_num, options.delimiter, options.add_text))

# Get all images
for filename in glob.glob(options.src_dir + '/*.*'):
    photo_path = Path(filename)
    logging.info("get {}".format(filename))
    file_ext = ((photo_path.suffix).upper()).replace(".","")
    filename_as_text = photo_path.stem.split('_')[0]
    if file_ext in img_exts:
        square = {}
        square['text'] = filename_as_text
        if options.as_square:
            square['img'] = createSquare(filename)
        else:
            square['img'] = createImage(filename) 
        squares.append(square)

### Getting size of images
images_array = []
for image in squares:
    images_array.append(image['img'])

biggest_w, biggest_h = get_biggest_sizes(images_array=images_array)
logging.info('Biggest size w is {}'.format(str(biggest_w)))
logging.info('Biggest size h is {}'.format(str(biggest_h)))

# Create squares with same size
for idx, image in enumerate(squares):
    if biggest_w != image['img'].size[0]:
        if options.as_square:
            squares[idx]['img'] = resize_image( image['img'], biggest_w, biggest_w) 
        else:
            squares[idx]['img'] = resize_image( image['img'], biggest_w) 

# adding white border
border = int( ( biggest_w * 11 ) / 100 )
for idx, image in enumerate(squares):
    polaroid = ImageOps.expand(image['img'], border=border, fill='white')
    squares[idx]['img'] = polaroid

# adding text
if options.add_text != False:
    logging.info("Drawing text '{}' to fotos".format(options.add_text))
    for idx, image in enumerate(squares):
        editing_polaroid = ImageDraw.Draw(image['img'])
        related_font_size = int(border / 2.0)
        font = ImageFont.truetype('fonts/RockSalt-Regular.ttf', size=related_font_size)
        bbox = editing_polaroid.textbbox((0, 0), options.add_text, font=font)
        w_text = bbox[2] - bbox[0]
        h_text = bbox[3] - bbox[1]
        center_h =  ( image.size[1] - ( h_text / 2 ) ) - ( border / 2 )
        center_w = ( image.size[0] - w_text ) / 2
        editing_polaroid.text( ( center_w, center_h ), options.add_text, fill="black", font=font)

if options.add_filenametext:
    for idx, image in enumerate(squares):
        logging.info("Drawing filename text {}".format(image['text']))
        editing_polaroid = ImageDraw.Draw(image['img'])
        related_font_size = int(border / 3.0)
        font = ImageFont.truetype('fonts/RockSalt-Regular.ttf', size=related_font_size)
        bbox = editing_polaroid.textbbox((0, 0), image['text'], font=font)
        w_text = bbox[2] - bbox[0]
        h_text = bbox[3] - bbox[1]
        center_h =  ( image['img'].size[1] - ( h_text / 2 ) ) - ( border / 1.5 )
        center_w = ( image['img'].size[0] - w_text ) / 2
        editing_polaroid.text( ( center_w, center_h ), image['text'], fill="black", font=font)

# Create strip
line = 5
strip_num = 1
images_for_strip = []

print(squares)

logging.info("create strip with {} images".format(options.row_num))
for idx, image in enumerate(squares):
    logging.info("appending image for strip")
    images_for_strip.append(image['img'])
    if len(images_for_strip) == options.row_num:
        logging.info("creating strip...")
        strip_name = 'strip_' + str(strip_num) + '.jpg'
        createStrip(images_for_strip, strip_name, options.delimiter)
        images_for_strip = []
        strip_num += 1
