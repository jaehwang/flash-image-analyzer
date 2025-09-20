#!/usr/bin/env python3
"""Create a very simple test sample."""

import struct

def create_simple_sample():
    """Create minimal test sample with ELF magic."""
    # Start with ELF magic (ARM binary)
    data = bytearray()

    # ELF header (simplified)
    data.extend(b'\x7F\x45\x4C\x46')  # ELF magic
    data.extend(b'\x01\x01\x01\x00')  # 32-bit, little-endian, SYSV ABI
    data.extend(b'\x00' * 8)          # padding
    data.extend(struct.pack('<H', 2)) # ET_EXEC
    data.extend(struct.pack('<H', 40)) # EM_ARM
    data.extend(struct.pack('<I', 1)) # EV_CURRENT
    data.extend(struct.pack('<I', 0x40000000)) # entry point
    data.extend(struct.pack('<I', 52))  # program header offset
    data.extend(struct.pack('<I', 0))   # section header offset
    data.extend(struct.pack('<I', 0))   # flags
    data.extend(struct.pack('<H', 52))  # ELF header size
    data.extend(struct.pack('<H', 32))  # program header size
    data.extend(struct.pack('<H', 1))   # program header count
    data.extend(struct.pack('<H', 0))   # section header size
    data.extend(struct.pack('<H', 0))   # section header count
    data.extend(struct.pack('<H', 0))   # string table index

    # Program header
    data.extend(struct.pack('<I', 1))   # PT_LOAD
    data.extend(struct.pack('<I', 0))   # offset
    data.extend(struct.pack('<I', 0x40000000)) # virtual address
    data.extend(struct.pack('<I', 0x40000000)) # physical address
    data.extend(struct.pack('<I', 1024))   # file size
    data.extend(struct.pack('<I', 1024))   # memory size
    data.extend(struct.pack('<I', 5))      # flags (R+X)
    data.extend(struct.pack('<I', 4))      # alignment

    # Add some fake code
    data.extend(b'BOOTCODE' * 100)  # ~800 bytes of fake boot code

    # Pad to make it exactly 1KB
    while len(data) < 1024:
        data.append(0)

    return bytes(data)

def main():
    sample = create_simple_sample()

    with open('samples/simple_test.bin', 'wb') as f:
        f.write(sample)

    print(f"Created simple test sample: {len(sample)} bytes")

if __name__ == '__main__':
    main()