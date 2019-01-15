from PIL import Image, ImageOps
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
        logging.info("Factor: {}, Side: {}".format(factor,side))
    else:
        side = original_size[0]
        factor = "portrait"

    infos['factor'] = factor
    infos['side'] = side
    infos['filename'] = os.path.basename(filename)
    infos['extension'] = os.path.splitext(filename)[1]
    filename_w_ext = os.path.basename(filename)
    infos['filename'], infos['extension'] = os.path.splitext(filename_w_ext)
    return(infos)

def createPolaroid(filename, border, save=False):
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

    # Create polaroid img
    polaroid = ImageOps.expand(square_pic, border=border, fill='white')
    if save:
      polaroid.save('output/polaroid_' + infos['filename'] + infos['extension'])

    return(polaroid)

def resize_image( image, base, height ):
    orig_base, orig_height = image.size
    if orig_base == base and orig_height == height:
        logging.info('Img not resized')
        return(image)
    logging.info('Resizing img')
    return(image.resize((base,height), Image.ANTIALIAS))

def createStrip(images_array, strip_name, delimiter=False):
    num_elements = len(images_array)

    img_size_array = []
    for image in images_array:
        img_size_array.append(image.size[0])
    biggest_img = max(img_size_array)
    logging.info('Biggest size is ' + str(biggest_img))

    if delimiter:
        line = 1
    else:
        line = 0
    strip_size = ( (biggest_img * num_elements + line), ( biggest_img + line ) )
    strip = Image.new("RGB", strip_size)
    goforward = 0
    for image in images_array:
        image_resized = resize_image(image, biggest_img, biggest_img)
        if goforward == 0:
            strip.paste(image_resized, (goforward, line))
        else:
            strip.paste(image_resized, (goforward + line, line))
        goforward = goforward + image_resized.size[0]

    logging.info('saving strip {}'.format(strip_name))
    strip.save('output/' + strip_name)

logging.basicConfig(level=logging.INFO)

parser = OptionParser()
parser.add_option("-d", "--directory", dest="src_dir", default=False, type="string", help="Source files directory")
parser.add_option("-r", "--row", dest="row_num", type="int", default=1, help="Number of element in a row")
parser.add_option("-D", "--delimiter", dest="delimiter", default=False, action='store_true', help="Show delimiter")
parser.add_option("-b", "--border-size", dest="border", default=200, help="Border size, default is 200" )
(options, args) = parser.parse_args()

if options.src_dir == False:
    parser.error( "Give source image path" )

images_array = []
strip_num = 1

for filename in glob.glob(options.src_dir + '/*.jpg'):
    if options.row_num == 1:
        logging.info('Printing single polaroid {}'.format(filename))
        polaroid = createPolaroid(filename, options.border, save=True)
    else:
        logging.info('Adding polaroid {} to array'.format(filename))
        images_array.append(createPolaroid(filename, options.border, save=True))

    if len(images_array) == options.row_num:
        strip_name = 'strip_' + str(strip_num) + '.jpg'
        createStrip(images_array, strip_name, options.delimiter)
        strip_num += 1
        images_array = []
