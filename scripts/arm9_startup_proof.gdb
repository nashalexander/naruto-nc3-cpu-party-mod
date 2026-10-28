# Start a fresh emulator at its startup break, then run from project root:
# gdb -nx -q -x scripts/arm9_startup_proof.gdb
# Use one connection per emulator run; 1.1 can spin on EOF after disconnect.
source scripts/arm9_capture.gdb
break *0x02000a78
continue
info registers pc lr sp cpsr
x/2i $lr-4
x/3i $pc
x/wx 0x02000b30
stepi 2
info registers pc lr r1
nc3-snapshot
dump binary memory workbench/captures/mainram-startup-02000a80.bin 0x02000000 0x02400000
delete breakpoints
echo Startup proof captured. Target remains paused; use continue to boot.\n
