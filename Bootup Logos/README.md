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

## Logos preview

**Static logos**
|Logo           |Filename       |Note   |
|:-------------:|:-------------:|:-----:|
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/ad_maiora.png)|ad_maiora.png|English: "Towards greater things"|
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/arcade_galaga.png)|arcade_galaga.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/arcade_pac_man.png)|arcade_pac_man.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/bender.png)|bender.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/f1.png)|f1.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/halo_master_chief_helmet.png)|halo_master_chief_helmet.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/horror_vacui_IronOS.png)|horror_vacui_IronOS.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/IronOS.png)|IronOS.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/lot_of_tin_is_too_few_tin_IT.png)|lot_of_tin_is_too_few_tin_IT.png|English: "A lot of tin is too few tin"|
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/open_sw_hw_IronOS_logos.png)|open_sw_hw_IronOS_logos.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/skulls.png)|skulls.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/TS100.png)|TS100.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/TS80.png) |TS80.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/TS80P.png)|TS80P.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/wh_40k.png)|wh_40k.png||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/wwii_kilroy.png)|wwii_kilroy.png||

**Animated logos**
|Logo           |Filename       |Note   |
|:-------------:|:-------------:|:-----:|
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/CRT_horror_vacui.gif) |CRT_horror_vacui.gif||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/IronOS.gif)|IronOS.gif||
|![Alt text](https://github.com/Ralim/IronOS-Meta/blob/main/Bootup%20Logos/Images/terminal.gif)|terminal.gif||

_*click on logo to watch the full animation_
