
.include "stdlib.inc"

.define IOREG_STDOUT_CHAR = 0x0
.define IOREG_STDIN_CHAR = 0x0
.define IOREG_STDIN_AVAIL = 0x1


;extern print_string

.section startup
start_system:
	lea USP, stack_end
	lea TEMP, syscall_vectors
	mtc SYS_VCALL, TEMP
	lea TEMP, exception_vectors
	mtc SYS_VEXCEPT, TEMP
	lea TEMP, irq_vectors
	mtc SYS_VIRQ, TEMP
	lea TEMP, nmi_handler
	mtc SYS_VNMI, TEMP
	load.i GP, 0xFFFF0000  ;;I/O region loaded into Global Pointer
	call main
@endless_loop:
	wait
	bra @endless_loop

.section vectors
exception_vectors:
	.word default_exception_handler	;Break vector
	.word default_exception_handler	;Invalid bus condition
	.word default_exception_handler	;Cache miss exception
	.word default_exception_handler	;Illegal instruction
	.word default_exception_handler	;Privilege Violation 
	.word default_exception_handler	;Arithmetic Overflow
	.align 128
irq_vectors:
	.word default_irq_handler
	.word default_irq_handler
	.word default_irq_handler
	.word default_irq_handler
	.align 128
syscall_vectors:
	initialize_syscalls 0
	declare_syscall sys_print_char, SYSCALL_PRINT_CHAR
	declare_syscall sys_print_prog_string, SYSCALL_PRINT_PROG_STR
	declare_syscall sys_print_data_string, SYSCALL_PRINT_DATA_STR
	declare_syscall sys_get_input_char, SYSCALL_GET_INPUT_CHAR
	declare_syscall sys_get_input_count, SYSCALL_GET_INPUT_COUNT
	.align 256


.section routines
default_exception_handler:
	rti
default_irq_handler:
	rti
nmi_handler:
	rti

sys_print_char:
	store.bx GP[IOREG_STDOUT_CHAR], PARAM
@proc_end:
	rti

sys_print_data_string:
	load.b TEMP, PARAM
	addu.i PARAM, 1
	beq.i TEMP, 0, @proc_end
	beq.i TEMP, 10, @newline
	beq.i TEMP, 13, @newline
	store.bx GP[IOREG_STDOUT_CHAR], TEMP
	bra sys_print_data_string
@newline:
	load.i TEMP, 10
	store.bx GP[IOREG_STDOUT_CHAR], TEMP
	load.i TEMP, 13
	store.bx GP[IOREG_STDOUT_CHAR], TEMP
	bra sys_print_data_string
@proc_end:
	rti

sys_get_input_char:
	wait
	load.bux RTNV, GP[IOREG_STDIN_AVAIL]
	beq.i RTNV, 0, sys_get_input_char
	load.bux RTNV, GP[IOREG_STDIN_CHAR]
@proc_end:
	rti

sys_get_input_count:
	wait
	load.bux RTNV, GP[IOREG_STDIN_AVAIL]
@proc_end:
	rti


sys_print_prog_string:
	push R0
	push R1
	mfc R1, SYS_EPC
@loop:
	load.hp R0, R1
	load.i TEMP, 0xFF
	and.r TEMP, R0
	beq.i TEMP, 0, @proc_end
	store.bx GP[IOREG_STDOUT_CHAR], TEMP
	shr.i R0, 8
	and.i R0, 0xFF
	beq.i R0, 0, @proc_end
	store.bx GP[IOREG_STDOUT_CHAR], R0
	bra @loop
@proc_end:
	mtc SYS_EPC, R1
	pull R1
	pull R0
	rti

.section code

__unsigned_multiply__:
	init_frame
	declare_parameter @b
	declare_parameter @a
	start_frame
@start:
	; 	return16	#1:u8
	load.i RTNV, 1
	bra @proc_end
@proc_end:
	end_frame
	ret

__unsigned_divide__:
	init_frame
	declare_parameter @b
	declare_parameter @a
	start_frame
@start:
	; 	return16	#1:u8
	load.i RTNV, 1
	bra @proc_end
@proc_end:
	end_frame
	ret


input_char:
	syscall SYSCALL_GET_INPUT_CHAR
@proc_end:
	ret


print_char:
	init_frame
	declare_parameter @the_str
	start_frame
@start:
	load.wx PARAM, FRP[@the_str]
	syscall SYSCALL_PRINT_CHAR
@proc_end:
	end_frame
	ret

print_string:
	init_frame
	declare_parameter @the_str
	start_frame
@start:
	load.wx PARAM, FRP[@the_str]
	syscall SYSCALL_PRINT_DATA_STR
@proc_end:
	end_frame
	ret



.section stack
stack_end:
	.word 0


