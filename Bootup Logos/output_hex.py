import zlib


class HexOutput:
    """
    Supports writing a blob of data out in the Intel Hex format
    """

    INTELHEX_DATA_RECORD = 0x00
    INTELHEX_END_OF_FILE_RECORD = 0x01
    INTELHEX_EXTENDED_LINEAR_ADDRESS_RECORD = 0x04
    INTELHEX_BYTES_PER_LINE = 16
    INTELHEX_MINIMUM_SIZE = 4096

    @classmethod
    def split16(cls, word):
        """return high and low byte of 16-bit word value as tuple"""
        return (word >> 8) & 0xFF, word & 0xFF

    @classmethod
    def compute_crc(cls, data):
        return 0xFFFFFFFF & -zlib.crc32(data) - 1

    @classmethod
    def intel_hex_line(cls, record_type, offset, data):
        """generate a line of data in Intel hex format"""
        # length, address offset, record type
        record_length = len(data)
        yield ":{:02X}{:04X}{:02X}".format(record_length, offset, record_type)

        # data
        for byte in data:
            yield "{:02X}".format(byte)

        # compute and write checksum (now using unix style line endings for DFU3.45 compatibility
        yield "{:02X}\n".format(
            (
                (
                    (
                        sum(
                            data,  # sum data ...
                            record_length  # ... and other ...
                            + sum(cls.split16(offset))  # ... fields ...
                            + record_type,
                        )  # ... on line
                        & 0xFF
                    )  # low 8 bits
                    ^ 0xFF
                )  # two's ...
                + 1
            )  # ... complement
            & 0xFF
        )  # low 8 bits

    @classmethod
    def writeFile(cls, file_name: str, data: bytearray, data_address: int):
        """write block of data in Intel hex format"""
        with open(file_name, "w", newline="\r\n") as output:

            def write(generator):
                output.write("".join(generator))

            if len(data) % cls.INTELHEX_BYTES_PER_LINE != 0:
                raise ValueError(
                    "Program error: Size of LCD data is not evenly divisible by {}".format(
                        cls.INTELHEX_BYTES_PER_LINE
                    )
                )

            address_lo = data_address & 0xFFFF
            address_hi = (data_address >> 16) & 0xFFFF

            write(
                cls.intel_hex_line(
                    cls.INTELHEX_EXTENDED_LINEAR_ADDRESS_RECORD,
                    0,
                    cls.split16(address_hi),
                )
            )

            size_written = 0
            while size_written < cls.INTELHEX_MINIMUM_SIZE:
                offset = address_lo
                for line_start in range(0, len(data), cls.INTELHEX_BYTES_PER_LINE):
                    write(
                        cls.intel_hex_line(
                            cls.INTELHEX_DATA_RECORD,
                            offset,
                            data[line_start : line_start + cls.INTELHEX_BYTES_PER_LINE],
                        )
                    )
                    size_written += cls.INTELHEX_BYTES_PER_LINE
                    if size_written >= cls.INTELHEX_MINIMUM_SIZE:
                        break
                    offset += cls.INTELHEX_BYTES_PER_LINE

            write(cls.intel_hex_line(cls.INTELHEX_END_OF_FILE_RECORD, 0, ()))


if __name__ == "__main__":
    import sys

    print("DO NOT CALL THIS FILE DIRECTLY")
    sys.exit(1)
