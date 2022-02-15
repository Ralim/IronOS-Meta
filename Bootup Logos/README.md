## Boot up logo's are logos or animations shown on boot of IronOS

These are programmed into the device just like the normal firmware.
They can be (re)programmed as many times as desired after flashing the normal firmware.

### Data storage format

The data is stored into the second last page of flash, this gives 1024 bytes of space for the entire payload of bootup logo data.

The first byte is marked purely to indicate that the page is programmed and which revision of the boot logo logic it is
The next byte indicates the frame timing in milliseconds, or `0` to indicate only show first frame for whole bootloader duration (still image mode)
Then the OLED buffer is cleared to black, then every frame is encoded as either:

### Full frame updates

`[0xFF][Full framebuffer of data]`

### Delta frame update

`[count of updates][[index,data][index,data][index,data][index,data]]`
Where index is byte location into screen buffer, and data is the new byte to plonk down there
This just overwrites individual bytes in the output buffer
