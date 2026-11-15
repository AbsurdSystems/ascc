
CC=python3 ../ascc.py -w 4
CG=python3 ../codegen_as32x.py
ASM=python3 ../../as32x/asm32x/asm32x.py
TARGET=snippet
ASMFLAGS=-m $(TARGET).map -I ../../as32x/common_libs
#CSTARTUP=../../as32x/bmbxos/bios.asm
CSTARTUP=./bios.s

#CG=python3 ../codegen_as1602.py
#CG=python3 ../codegen_wdc65c02.py
#CG=python3 ../codegen_asr1016.py
#CG=python3 ../codegen_ase6502.py

all: basic.hex



%.asil: %.c
	$(CC) -s listing.txt -o $@ $<

%.ll: %.c
	clang -S -m32 -emit-llvm $< -o $@

%.asm: %.asil
	$(CG) -o $@ $<
	
%.hex: %.asm
	$(ASM) $(ASMFLAGS) -o $(TARGET).hex -s $(TARGET).lst $(CSTARTUP) $<

debug:
	cp $(TARGET).hex ../../as32x/as32x_sim/

vm6502_sim: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS)

clean:
	rm *.lis *.lst *.hex *.asm *.asil *.ll yacctab.py lextab.py listing.txt


