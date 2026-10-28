ENTRY(lobby_hook)
SECTIONS {
  . = 0x023d0000;
  .text : { *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) }
  . = ALIGN(4);
  .bss : { *(.bss*) *(COMMON) }
  .modstate 0x023df000 (NOLOAD) : { *(.modstate) }
  payload_end = .;
  /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
