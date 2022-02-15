import struct, zlib


class DFUOutput:

    DFU_PREFIX_SIZE = 11
    DFU_SUFFIX_SIZE = 16

    @classmethod
    def compute_crc(cls, data):
        return 0xFFFFFFFF & -zlib.crc32(data) - 1

    @classmethod
    def writeFile(
        cls,
        file_name: str,
        data_in: bytearray,
        data_address: int,
        tagetName: str,
        alt_number: int,
        product_id: int,
        vendor_id: int,
    ):
        data: bytearray = bytearray(data_in)

        data = struct.pack("<2I", data_address, len(data)) + data
        data = (
            struct.pack(
                "<6sBI255s2I",
                b"Target",
                alt_number,
                1,
                tagetName,
                len(data),
                1,
            )
            + data
        )
        data = (
            struct.pack(
                "<5sBIB",
                b"DfuSe",
                1,
                cls.DFU_PREFIX_SIZE + len(data) + cls.DFU_SUFFIX_SIZE,
                1,
            )
            + data
        )
        data += struct.pack(
            "<4H3sB",
            0,
            product_id,
            vendor_id,
            0x011A,
            b"UFD",
            cls.DFU_SUFFIX_SIZE,
        )
        crc = cls.compute_crc(data)
        data += struct.pack("<I", crc)
        with open(file_name, "wb") as output:
            output.write(data)


if __name__ == "__main__":
    import sys

    print("DO NOT CALL THIS FILE DIRECTLY")
    sys.exit(1)
