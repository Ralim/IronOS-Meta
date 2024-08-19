#!/usr/bin/env python
# coding=utf-8
from __future__ import division
import argparse
import copy
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

DATA_PROGRAMMED_MARKER = 0xAA
FULL_FRAME_MARKER = 0xFF
EMPTY_FRAME_MARKER = (
    0xFE  # If this marker is used to start a frame, the frame is a 0-length delta frame
)


class MiniwareSettings:
    IMAGE_ADDRESS = 0x0800F800
    DFU_TARGET_NAME = b"IronOS-dfu"
    DFU_ALT = 0
    DFU_VENDOR = 0x1209
    DFU_PRODUCT = 0xDB42
    MINIMUM_HEX_SIZE = 4096


class S60Settings:
    IMAGE_ADDRESS = 0x08000000 + (62 * 1024)
    DFU_TARGET_NAME = b"IronOS-dfu"
    DFU_ALT = 0
    DFU_VENDOR = 0x1209
    DFU_PRODUCT = 0xDB42
    MINIMUM_HEX_SIZE = 1024


class TS101Settings:
    IMAGE_ADDRESS = 0x08000000 + (126 * 1024)
    DFU_TARGET_NAME = b"IronOS-dfu"
    DFU_ALT = 0
    DFU_VENDOR = 0x1209
    DFU_PRODUCT = 0xDB42
    MINIMUM_HEX_SIZE = 1024


class MHP30Settings:
    IMAGE_ADDRESS = 0x08000000 + (126 * 1024)
    DFU_TARGET_NAME = b"IronOS-dfu"
    DFU_ALT = 0
    DFU_VENDOR = 0x1209
    DFU_PRODUCT = 0xDB42
    MINIMUM_HEX_SIZE = 4096


class PinecilSettings:
    IMAGE_ADDRESS = 0x0801F800
    DFU_TARGET_NAME = b"Pinecil"
    DFU_ALT = 0
    DFU_VENDOR = 0x28E9
    DFU_PRODUCT = 0x0189
    MINIMUM_HEX_SIZE = 1024


class Pinecilv2Settings:
    IMAGE_ADDRESS = 1016 * 1024  # its 2 4k erase pages inset
    DFU_TARGET_NAME = b"Pinecilv2"
    DFU_ALT = 0
    DFU_VENDOR = 0x28E9  # These are ignored by blisp so doesnt matter what we use
    DFU_PRODUCT = 0x0189  # These are ignored by blisp so doesnt matter what we use
    MINIMUM_HEX_SIZE = 1024


def still_image_to_bytes(
    image: Image, negative: bool, dither: bool, threshold: int, preview_filename
):
    # convert to luminance
    # do even if already black/white because PIL can't invert 1-bit so
    #   can't just pass thru in case --negative flag
    # also resizing works better in luminance than black/white
    # also no information loss converting black/white to greyscale
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
    # pad to this size (also will be repeated in output Intel hex file)
    data = []

    # convert to  LCD format
    for ndx in range(LCD_WIDTH * LCD_HEIGHT // 8):
        bottom_half_offset = 0 if ndx < LCD_WIDTH else 8
        byte = 0
        for y in range(8):
            if image.getpixel((ndx % LCD_WIDTH, y + bottom_half_offset)):
                byte |= 1 << y
        data.append(byte)

    """ DEBUG
    for row in range(LCD_HEIGHT):
        for column in range(LCD_WIDTH):
            if image.getpixel((column, row)): sys.stderr.write('█')
            else:                             sys.stderr.write(' ')
        sys.stderr.write('\n')
    """
    return data


def calculate_frame_delta_encode(previous_frame: bytearray, this_frame: bytearray):
    damage = []
    for i in range(0, len(this_frame)):
        if this_frame[i] != previous_frame[i]:
            damage.append(i)
            damage.append(this_frame[i])
    return damage


def get_screen_blob(previous_frame: bytearray, this_frame: bytearray):
    """
    Given two screens, returns the smaller representation
    Either a full screen update
    OR
    A delta encoded form
    """
    outputData = []
    delta = calculate_frame_delta_encode(previous_frame, this_frame)
    if len(delta) == 0:
        outputData.append(EMPTY_FRAME_MARKER)
    elif len(delta) < (len(this_frame)):
        outputData.append(len(delta))
        outputData.extend(delta)
        # print("delta encoded frame")
    else:
        outputData.append(FULL_FRAME_MARKER)
        outputData.extend(this_frame)
        # print("full encoded frame")
    return outputData


def animated_image_to_bytes(
    imageIn: Image, negative: bool, dither: bool, threshold: int, flip_frames
):
    """
    Convert the gif into our best effort startup animation
    We are delta-encoding on a byte by byte basis

    So we convert every frame into its binary representation
    The compare these to figure out the encoding

    The naïve implementation would save the frame 5 times
    But if we delta encode; we can make far more frames of animation for _some_ types of animations.
    This means reveals are better than moves.
    Data is stored in the byte blobs, so if you change one pixel, changing another pixel in that column on that row is "free"
    """

    frameData = []
    frameTiming = None
    for framenum in range(0, imageIn.n_frames):
        imageIn.seek(framenum)
        image = imageIn
        if flip_frames:
            image = image.rotate(180)

        frameb = still_image_to_bytes(image, negative, dither, threshold, None)
        frameData.append(frameb)
        # Store inter-frame duration
        frameDuration_ms = image.info["duration"]
        if frameTiming is None:
            frameTiming = frameDuration_ms
        else:
            delta = frameDuration_ms / frameTiming
            if delta > 1.05 or delta < 0.95:
                print(
                    f"ERROR: You have a frame that is different to the first frame time. Mixed rates are not supported"
                )
                sys.exit(-1)
    print(f"Found {len(frameData)} frames, interval {frameTiming}ms")
    frameTiming = frameTiming / 5
    if frameTiming <= 0 or frameTiming > 254:
        newTiming = max(frameTiming, 1)
        newTiming = min(newTiming, 254)

        print(
            f"Inter frame delay {frameTiming} is out of range, and is being adjusted to {newTiming*5}"
        )
        frameTiming = newTiming

    # We have now mangled the image into our framebuffers

    # Now we can build our output data blob
    # First we always start with a full first frame; future optimisation to check if we should or not
    outputData = [DATA_PROGRAMMED_MARKER]
    outputData.append(int(frameTiming))
    first_frame = get_screen_blob([0x00] * (LCD_NUM_BYTES), frameData[0])
    outputData.extend(first_frame)
    print(f"Frame 1 encoded to {len(first_frame)} bytes")

    """
    Format for each frame block is:
    [length][ [delta block][delta block][delta block][delta block] ]
    Where [delta block] is just [index,new value]
    
    OR
    [0xFF][Full frame data]
    """
    for id in range(1, len(frameData)):
        frameBlob = get_screen_blob(frameData[id - 1], frameData[id])
        if (len(outputData) + len(frameBlob)) > LCD_PAGE_SIZE:
            print(f"Truncating animation after {id} frames as we are out of space")
            break
        print(f"Frame {id + 1} encoded to {len(frameBlob)} bytes")
        outputData.extend(frameBlob)
    print(f"Total size used: {len(outputData)} of 1024 bytes")
    return outputData


def img2hex(
    input_filename,
    device_model_name: str,
    preview_filename=None,
    threshold=128,
    dither=False,
    negative=False,
    make_erase_image=False,
    output_filename_base="out",
    flip=False,
):
    """
    Convert 'input_filename' image file into Intel hex format with data
        formatted for display on  LCD and file object.
    Input image is converted from color or greyscale to black-and-white,
        and resized to fit  LCD screen as necessary.
    Optionally write resized/thresholded/black-and-white preview image
        to file specified by name.
    Optional `threshold' argument 8 bit value; greyscale pixels greater than
        this become 1 (white) in output, less than become 0 (black).
    Unless optional `dither', in which case PIL greyscale-to-black/white
        dithering algorithm used.
    Optional `negative' inverts black/white regardless of input image type
        or other options.
    """
    if make_erase_image:
        data = [0xFF] * 1024
    else:
        try:
            image = Image.open(input_filename)
        except BaseException as e:
            raise IOError('error reading image file "{}": {}'.format(input_filename, e))

        if getattr(image, "is_animated", False):
            data = animated_image_to_bytes(image, negative, dither, threshold, flip)
        else:
            if flip:
                image = image.rotate(180)
            # magic/required header
            data = [DATA_PROGRAMMED_MARKER, 0x00]  # Timing value of 0
            image_bytes = still_image_to_bytes(
                image, negative, dither, threshold, preview_filename
            )
            data.extend(get_screen_blob([0] * LCD_NUM_BYTES, image_bytes))

    # Pad up to the full page size
    if len(data) < LCD_PAGE_SIZE:
        pad = [0] * (LCD_PAGE_SIZE - len(data))
        data.extend(pad)

    # Set device settings depending on input `-m` argument
    device_name = device_model_name.lower()
    if (
        device_name == "miniware"
        or device_name == "ts100"
        or device_name == "ts80"
        or device_name == "ts80p"
    ):
        deviceSettings = MiniwareSettings
    elif device_name == "pinecilv1" or device_name == "pinecil":
        deviceSettings = PinecilSettings
    elif device_name == "pinecilv2":
        deviceSettings = Pinecilv2Settings
    elif device_name == "ts101":
        deviceSettings = TS101Settings
    elif device_name == "s60":
        deviceSettings = S60Settings
    elif device_name == "mhp30":
        deviceSettings = MHP30Settings
    else:
        print("Could not determine device type")
        sys.exit(-1)

    # Split name from extension so we can mangle in the _L suffix for flipped images
    split_name = os.path.splitext(os.path.basename(input_filename))

    if flip:
        base = split_name[0]
        ext = split_name[1]
        base = base + "_L"
        split_name = [base, ext]
    output_name = output_filename_base + split_name[0] + split_name[1]

    DFUOutput.writeFile(
        output_name + ".dfu",
        data,
        deviceSettings.IMAGE_ADDRESS,
        deviceSettings.DFU_TARGET_NAME,
        deviceSettings.DFU_ALT,
        deviceSettings.DFU_PRODUCT,
        deviceSettings.DFU_VENDOR,
    )

    HexOutput.writeFile(
        output_name + ".hex",
        data,
        deviceSettings.IMAGE_ADDRESS,
        deviceSettings.MINIMUM_HEX_SIZE,
    )


def parse_commandline():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Convert image file for display on IronOS OLED at startup",
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
        help="photo negative: exchange black and white in output",
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=zero_to_255,
        default=128,
        help="0 to 255: grey (or color converted to grey) "
        "above this becomes white, below becomes black; "
        "ignored if using --dither",
    )

    parser.add_argument(
        "-d",
        "--dither",
        action="store_true",
        help="use dithering (speckling) to convert grey or " "color to black and white",
    )

    parser.add_argument(
        "-E",
        "--erase",
        action="store_true",
        help="generate a logo erase file instead of a logo",
    )

    parser.add_argument("-m", "--model", help="device model name")
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

    if args.preview and os.path.exists(args.preview) and not args.force:
        sys.stderr.write(
            'Won\'t overwrite existing file "{}" (use --force '
            "option to override)\n".format(args.preview)
        )
        sys.exit(1)

    print(f"Converting {args.input_filename} => {args.output_filename}")

    img2hex(
        input_filename=args.input_filename,
        output_filename_base=args.output_filename,
        device_model_name=args.model,
        preview_filename=args.preview,
        threshold=args.threshold,
        dither=args.dither,
        negative=args.negative,
        make_erase_image=args.erase,
        flip=False,
    )

    img2hex(
        input_filename=args.input_filename,
        output_filename_base=args.output_filename,
        device_model_name=args.model,
        preview_filename=args.preview,
        threshold=args.threshold,
        dither=args.dither,
        negative=args.negative,
        make_erase_image=args.erase,
        flip=True,
    )
