"""
Generates jpg patches from .czi format whole slide images.
Run python cziPy.py --help to see possible arguments.

Requires javabridge, bioformats and PIL.

Code by Craig Myles (cggm1@st-andrews.ac.uk)
Inspired by code from Jessica Cooper (jmc31@st-andrews.ac.uk)
"""

import argparse
import glob
import os
from pathlib import Path
from tqdm import tqdm
from time import process_time
import logging
import numpy as np
from PIL import Image
import cv2

import bioformats
import javabridge
from utils.silence_javabridge_util import silence_javabridge
from utils.patch_validator import is_valid_patch

parser = argparse.ArgumentParser()
parser.add_argument('--patch_dim', type=int, default=256, help='Patch dimension, 256/512 etc. (Default is 256)')
parser.add_argument('--overlap', type=int, default=0,  help='By how many pixels patches should overlap. (Default is 0)')
parser.add_argument('--series', type=int, default=0, help='Czi series/zoom level. Lower number = higher resolution. (Default is 0)')
parser.add_argument('--czi_dir', default='imgs/czis', help='Path to czi files. ("./imgs/czis" by default)')
parser.add_argument('--log_dir', default='log.txt', help='Path to log file. (./log.txt by default)')
parser.add_argument('--patch_dir', default='imgs/patches', help='Where to save generated patches. ("./imgs/patches" by default)')
parser.add_argument('--jpg_wsi', action='store_true', 
                    help='Whether or not to save jpgs of whole slide images. False by default (Large series may cause memory issues when true)')
parser.add_argument('--jpg_dir', default='imgs/jpgs', help='Where to save entire slide jpgs. ("./imgs/jpgs" by default)')
parser.add_argument('--save_blank', action='store_true', help='Whether or not to save blank patches (i.e. no pixel variation, such as at edge of slides)')
parser.add_argument('--no_patch', action='store_true', help='Create a wsi jpg without patches. Set the series value high to avoid crashing.')
parser.add_argument('--resize', default="0,0", 
                    help='Optionally provide image dimensions separated by a comma, e.g. h,w, '
                        'which will be used to size the entire slide jpg (with rotation and padding if necessary). '
                        'If not provided, the jpg dimensions will reflect the czi dimensions and series. (0,0 by default')

args = parser.parse_args()

log_location = args.log_dir
print("Starting cziPy.py, check "+log_location+" for progress...")

javabridge.start_vm(class_path=bioformats.JARS, max_heap_size="2G")
#silence javabridge debug messages
jb_logger = silence_javabridge()

PATCH_DIM = args.patch_dim
SERIES = args.series

im_names = glob.glob("{}/*.czi".format(args.czi_dir))

logging.basicConfig(filename=log_location, filemode='a', format='%(asctime)s: %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]', level=logging.INFO)

def normalise(x):
    if x.max() - x.min() == 0:
        return x
    return (x - x.min()) / (x.max() - x.min())

def resize(im, target_height, target_width):
    print('Image dimensions:', im.size)
    old_width, old_height = im.size
    target_orientation = 'P' if target_height > target_width else 'L'
    old_orientation = 'P' if old_height > old_width else 'L'

    if old_orientation != target_orientation:
        print('Rotating image...')
        im = im.rotate(90, expand=True)
        old_width, old_height = im.size

    print('Resizing image...')
    if target_height == target_width:
        ratio = target_width / max(old_width, old_height)
    else:
        ratio = min(target_width, target_height) / min(old_width, old_height)
    new_width = int(old_width * ratio)
    new_height = int(old_height * ratio)
    im = im.resize((new_width, new_height), resample=Image.LANCZOS)
    new_im = Image.new(im.mode, (target_width, target_height))
    new_im.paste(im, ((target_width - new_width) // 2, (target_height - new_height) // 2))
    return new_im

generated_patches = []

logging.info("Launching cziPy.py with args: "+str(args))
for i in tqdm(im_names):
        
    logging.info("Beginning processing on file "+i+"...")
    
    t1_start = process_time()
    wsi = i.split('/')[-1].split('.')[0]

    # Check if mask does not already exists
    if not os.path.exists(args.patch_dir+"/masks/"+wsi+'_binary_map.png'):

        if not args.no_patch:
            
            with bioformats.ImageReader(i) as reader:
                reader.rdr.setSeries(SERIES)
                x_dim, y_dim = reader.rdr.getSizeX(), reader.rdr.getSizeY()
                
                #Binary mask of pixels
                binary_map = np.zeros((round(y_dim//PATCH_DIM), round(x_dim//PATCH_DIM)))
                #Create file req file paths
                Path(""+args.patch_dir+"/"+wsi).mkdir(parents=True, exist_ok=True)
                Path(""+args.patch_dir+"/masks").mkdir(parents=True, exist_ok=True)
                Path(""+args.patch_dir+"/masks"+"/npy").mkdir(parents=True, exist_ok=True)
                logging.info("Generating patches...")
                for x in tqdm(range(0, x_dim - PATCH_DIM, PATCH_DIM - args.overlap), desc=wsi+" row"):
                    # for y in tqdm(range(0, y_dim - PATCH_DIM, PATCH_DIM - args.overlap), desc=wsi+" column"): #use this line for more verbose progress bar
                    for y in range(0, y_dim - PATCH_DIM, PATCH_DIM - args.overlap):
                        patch = normalise(reader.read(XYWH=(x, y, PATCH_DIM, PATCH_DIM))) * 255

                        #CHECK IF PATCH IS USEFUL
                        #if value ranges anywhere across a patch, save, otherwise skip (unless save_blank is set)
                        if (is_valid_patch(patch)) or args.save_blank:
                            patch_name = '{}/{}/{}_{}_{}_{}.png'.format(\
                                    args.patch_dir, wsi, wsi, \
                                    SERIES, x, y)

                            # OpenCV save patch:
                            cv2.imwrite(patch_name, patch)

                            generated_patches.append(patch_name)
                            #Pixel at current binary map location should be black (1)
                            binary_map[y//PATCH_DIM][x//PATCH_DIM] = 1

                t1_stop = process_time()
                #Save binary segmentation map as .png and .npy
                binary_map_img = Image.fromarray(np.uint8(binary_map * 255) , 'L')
                binary_map_img.save('{}/{}/{}_binary_map.png'.format(args.patch_dir, "masks", wsi))
                np.save('{}/{}/{}/{}_binary_map.npy'.format(args.patch_dir, "masks", "npy", wsi),binary_map)
                logging.info(i+' patching completed at level '+str(SERIES)+' in '+str((t1_stop-t1_start))+' seconds.')

        #STORE WSI AS JPEG
        if args.jpg_wsi:
            try:
                img = normalise(bioformats.load_image(i, series=SERIES)) * 255
                img = Image.fromarray(img.astype('uint8'))
                img.save('{}/{}_S{}.jpg'.format(args.jpg_dir, i.split('/')[-1], SERIES))
                if args.resize != "0,0":
                    img = resize(img, int(args.resize.split(',')[0]), int(args.resize.split(',')[1]))
                    img.save('{}/{}_{}_RESIZED.jpg'.format(args.jpg_dir, i.split('/')[-1], SERIES))
            except Exception:
                print("Could not save entire czi as jpg - it's probably too big. Try using a higher series value.")
                logging.info("Exception error on "+i+" at series "+str(SERIES))
        
        logging.info("Completed processing on file "+i)
    else:
        logging.info("File "+i+" already has a mask (and therefore already patched). Skipping.")

javabridge.kill_vm()
logging.info("Killing JavaBridge")
# print(generated_patches)
print('Successfully generated {} patches!'.format(len(generated_patches)))
