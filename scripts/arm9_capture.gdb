# Run from the project root: gdb -nx -q -x scripts/arm9_capture.gdb
set architecture arm
set endian little
set pagination off
set confirm off
set logging file workbench/captures/arm9-session.log
set logging overwrite off
set logging enabled on
set remotetimeout 10
target remote localhost:3333

define nc3-snapshot
  info registers
  x/12i $pc
  x/24wx $sp
  dump binary memory workbench/captures/mainram-live.bin 0x02000000 0x02400000
end
document nc3-snapshot
Record registers, current instructions, stack words, and a main RAM snapshot.
Copy the dump to a scene-specific filename before taking another snapshot.
end

# Hardware-register watchpoints may not trap emulated I/O. Prefer a proven
# cached-input or actor RAM address once a live instruction identifies it.
define nc3-watch
  watch -l *(unsigned short *)$arg0
end
document nc3-watch
nc3-watch ADDRESS: stop on writes to a candidate 16-bit RAM field.
On a hit record registers/disassembly, the memory address, and visual effect.
end

echo Connected. Use nc3-snapshot at a reproducible paused scene.\n
echo Connection and snapshot commands validated; actor watchpoints remain untested.\n
