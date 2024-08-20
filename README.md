# IronOS-Meta

Storing meta information for IronOS.
This are things that are not part of the core "OS".
This includes photographs of hardware, datasheets, schematics, original proprietary firmware and of course **bootup logos**.

This repository uses github actions to automagically build the logos for each device.
Periodically a "release" will be tagged and pre-compiled logo's will be put there as well to make it easy.

# Boot-Up Logos

The IronOS firmware supports a user created bootup logo.
By default, there is _not_ one included in the firmware. This means that once flashed they generally stay. If you want no logo again, you would have to flash a blank image to the bootup logo.

- Safe & Fun: will not over write your firmware
- Easy install: use dfu tool just like updating firmware (or Pine64 Updater if you have a Pinecil).

## Generating the Logo files

There are community logo's already converted and ready to use in [IronOS-Meta/releases](https://github.com/Ralim/IronOS-Meta/releases).
Download the zip for Pinecil or Miniware and then install using the instructions on the [main IronOS documentation](https://ralim.github.io/IronOS/Logo/).

Alternatively if you want to make your own logo files, there is also documentation on how best to do this in the [main IronOS documentation](https://ralim.github.io/IronOS/Logo/).
