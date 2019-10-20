from PIL import Image, ImageOps, ImageFont, ImageDraw
import glob
import sys
import logging
import os
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

def resize_image( image, base, height ):
    orig_base, orig_height = image.size
    if orig_base == base and orig_height == height:
        logging.info('Img not resized')
        return(image)
    logging.info('Resizing img')
    return(image.resize((base,height), Image.ANTIALIAS))

def createStrip(images_array, strip_name, delimiter=False):
    num_elements = len(images_array)
    onesize = images_array[0].size[0]

    if delimiter:
        line = 5
        logging.info("Show Delimiter")
    else:
        line = 0

    strip_size = ( ( ( onesize * num_elements) + (line * 3)), ( onesize + line ) )
    strip = Image.new("RGB", strip_size, color=("Black"))
    goforward = 0
    for image in images_array:
        logging.info("image base {} height {}".format(image.size[0],image.size[1]))
        strip.paste(image, (goforward + line, line))
        goforward = goforward + onesize + line

    logging.info('saving strip {}'.format(strip_name))
    strip.save('output/' + strip_name)

# Main
strip_num = 1
squares = []

logging.basicConfig(level=logging.INFO)

parser = OptionParser()
parser.add_option("-d", "--directory", dest="src_dir", default=False, type="string", help="Source files directory")
parser.add_option("-r", "--row", dest="row_num", type="int", default=2, help="Number of element in a row")
parser.add_option("-D", "--delimiter", dest="delimiter", default=True, action='store_true', help="Show delimiter")
parser.add_option("-t", "--add-text", dest="add_text", default=False, help="Text to add to bottom to the polaroid")
(options, args) = parser.parse_args()

if options.src_dir == False:
    parser.print_help()
    parser.error( "Give source image path" )

logging.info("Source Directory: {}, Element in row: {}, Delimiter: {}, Text: {}".format(options.src_dir, options.row_num, options.delimiter, options.add_text))

# Get all images
for filename in glob.glob(options.src_dir + '/*.jpg'):
    print(filename)
    squares.append(createSquare(filename))

# Define biggest images square size
img_size_array = []
for image in squares:
    img_size_array.append(image.size[0])

biggest_img = max(img_size_array)
logging.info('Biggest size is {}'.format(str(biggest_img)))

# Create squares with same size
for idx, image in enumerate(squares):
    if biggest_img != image.size[0]:
        squares[idx] = resize_image( image, biggest_img, biggest_img )

# adding white border
border = int( ( biggest_img * 11 ) / 100 )
for idx, image in enumerate(squares):
    polaroid = ImageOps.expand(image, border=border, fill='white')
    squares[idx] = polaroid

# adding text
if options.add_text != False:
    logging.info("Drawing text '{}' to fotos".format(options.add_text))
    for idx, image in enumerate(squares):
        editing_polaroid = ImageDraw.Draw(image)
        related_font_size = int(border / 1.9)
        font = ImageFont.truetype('fonts/Laila-Medium.ttf', size=related_font_size)
        w_text, h_text = font.getsize(options.add_text)
        center_h =  ( image.size[1] - ( h_text / 2 ) ) - ( border / 2 )
        center_w = ( image.size[0] - w_text ) / 2
        editing_polaroid.text( ( center_w, center_h ), options.add_text, fill="black", font=font)

# Create strip
line = 5
strip_num = 1
images_for_strip = []

logging.info("create strip with {} images".format(options.row_num))
for idx, image in enumerate(squares):
    logging.info("appending image for strip")
    images_for_strip.append(image)
    if len(images_for_strip) == options.row_num:
        strip_name = 'strip_' + str(strip_num) + '.jpg'
        createStrip(images_for_strip, strip_name, options.delimiter)
        images_for_strip = []
        strip_num += 1
