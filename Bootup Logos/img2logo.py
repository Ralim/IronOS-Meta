#!/usr/bin/env python
# coding=utf-8
from __future__ import division
import argparse
import os, sys

from output_hex import HexOutput
from output_dfu import DFUOutput

try:
    from PIL import Image, ImageOps
except ImportError as error:
    raise ImportError(
        "{}: {} requres Python Imaging Library (PIL). "
        "Install with `pip` (pip3 install pillow) or OS-specific package "
        "management tool.".format(error, sys.argv[0])
    )

VERSION_STRING = "1.0"

LCD_WIDTH = 96
LCD_HEIGHT = 16
LCD_NUM_BYTES = LCD_WIDTH * LCD_HEIGHT // 8
LCD_PAGE_SIZE = 1024


class MiniwareSettings:
    IMAGE_ADDRESS = 0x0800F800
    DFU_TARGET_NAME = b"IronOS-dfu"
    DFU_PINECIL_ALT = 0
    DFU_PINECIL_VENDOR = 0x1209
    DFU_PINECIL_PRODUCT = 0xDB42


class PinecilSettings:
    IMAGE_ADDRESS = 0x0801F800
    DFU_TARGET_NAME = b"Pinecil"
    DFU_PINECIL_ALT = 0
    DFU_PINECIL_VENDOR = 0x28E9
    DFU_PINECIL_PRODUCT = 0x0189


def img2hex(
    input_filename,
    preview_filename=None,
    threshold=128,
    dither=False,
    negative=False,
    isPinecil=False,
    output_filename_base="out",
):
    """
    Convert 'input_filename' image file into Intel hex format with data
        formatted for display on  LCD and file object.
    Input image is converted from color or grayscale to black-and-white,
        and resized to fit  LCD screen as necessary.
    Optionally write resized/thresholded/black-and-white preview image
        to file specified by name.
    Optional `threshold' argument 8 bit value; grayscale pixels greater than
        this become 1 (white) in output, less than become 0 (black).
    Unless optional `dither', in which case PIL grayscale-to-black/white
        dithering algorithm used.
    Optional `negative' inverts black/white regardless of input image type
        or other options.
    """

    try:
        image = Image.open(input_filename)
    except BaseException as e:
        raise IOError('error reading image file "{}": {}'.format(input_filename, e))

    # convert to luminance
    # do even if already black/white because PIL can't invert 1-bit so
    #   can't just pass thru in case --negative flag
    # also resizing works better in luminance than black/white
    # also no information loss converting black/white to grayscale
    if image.mode != "L":
        image = image.convert("L")
    # Resize to lcd size using bicubic sampling
    if image.size != (LCD_WIDTH, LCD_HEIGHT):
        image = image.resize((LCD_WIDTH, LCD_HEIGHT), Image.BICUBIC)

    if negative:
        image = ImageOps.invert(image)
        threshold = 255 - threshold  # have to invert threshold as well

    if dither:
        image = image.convert("1")
    else:
        image = image.point(lambda pixel: 0 if pixel < threshold else 1, "1")

    if preview_filename:
        image.save(preview_filename)

    """ DEBUG
    for row in range(LCD_HEIGHT):
        for column in range(LCD_WIDTH):
            if image.getpixel((column, row)): sys.stderr.write('1')
            else:                             sys.stderr.write('0')
        sys.stderr.write('\n')
    """

    # pad to this size (also will be repeated in output Intel hex file)
    data = [0] * LCD_PAGE_SIZE

    # magic/required header in endian-reverse byte order
    data[0] = 0x55
    data[1] = 0xAA
    data[2] = 0x0D
    data[3] = 0xF0

    # convert to  LCD format
    for ndx in range(LCD_WIDTH * 16 // 8):
        bottom_half_offset = 0 if ndx < LCD_WIDTH else 8
        byte = 0
        for y in range(8):
            if image.getpixel((ndx % LCD_WIDTH, y + bottom_half_offset)):
                byte |= 1 << y
        # store in endian-reversed byte order
        data[4 + ndx + (1 if ndx % 2 == 0 else -1)] = byte
    deviceSettings = MiniwareSettings
    if isPinecil:
        deviceSettings = PinecilSettings
    # Generate both possible outputs
    DFUOutput.writeFile(
        output_filename_base + ".dfu",
        data,
        deviceSettings.IMAGE_ADDRESS,
        deviceSettings.DFU_TARGET_NAME,
        deviceSettings.DFU_PINECIL_ALT,
        deviceSettings.DFU_PINECIL_PRODUCT,
        deviceSettings.DFU_PINECIL_VENDOR,
    )
    HexOutput.writeFile(
        output_filename_base + ".hex", data, deviceSettings.IMAGE_ADDRESS
    )


def parse_commandline():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Convert image file for display on  LCD " "at startup",
    )

    def zero_to_255(text):
        value = int(text)
        if not 0 <= value <= 255:
            raise argparse.ArgumentTypeError("must be integer from 0 to 255 ")
        return value

    parser.add_argument("input_filename", help="input image file")

    parser.add_argument("output_filename", help="output file base name")

    parser.add_argument(
        "-P",
        "--preview",
        help="filename of image preview",
    )

    parser.add_argument(
        "-n",
        "--negative",
        action="store_true",
        help="photo negative: exchange black and white " "in output",
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=zero_to_255,
        default=128,
        help="0 to 255: gray (or color converted to gray) "
        "above this becomes white, below becomes black; "
        "ignored if using --dither",
    )

    parser.add_argument(
        "-d",
        "--dither",
        action="store_true",
        help="use dithering (speckling) to convert gray or " "color to black and white",
    )

    parser.add_argument(
        "-f", "--force", action="store_true", help="force overwriting of existing files"
    )

    parser.add_argument(
        "-p", "--pinecil", action="store_true", help="generate files for Pinecil"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s version " + VERSION_STRING,
        help="print version info",
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_commandline()

    if os.path.exists(args.output_filename) and not args.force:
        sys.stderr.write(
            'Won\'t overwrite existing file "{}" (use --force '
            "option to override)\n".format(args.output_filename)
        )
        sys.exit(1)

    if args.preview and os.path.exists(args.preview) and not args.force:
        sys.stderr.write(
            'Won\'t overwrite existing file "{}" (use --force '
            "option to override)\n".format(args.preview)
        )
        sys.exit(1)

    try:
        img2hex(
            args.input_filename,
            args.preview,
            args.threshold,
            args.dither,
            args.negative,
            output_filename_base=args.output_filename,
            isPinecil=args.pinecil,
        )
    except BaseException as error:
        sys.stderr.write("Error converting file: {}\n".format(error))
        sys.exit(1)
