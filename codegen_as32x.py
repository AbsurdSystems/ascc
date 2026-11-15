
import math
import sys
import copy
import pprint
import os
import optparse
import string


class AS1602_Codegen:
	def __init__(self):
		self.curr_asilfile = None
		self.procedures = {}
		self.global_list = {}
		self.literal_list = {}
		self.reset_regs()
		self.initialized_data = {}
		self.settings = {}

	def reset_regs(self):
		#self.free_regs = ['R7','R6','R5','R4','R3','R2','R1','R0']
		self.free_regs = ['R7','R6','R5','R4','R3','R2','R1','R0']
		self.reg_mapping = {}

	def print_reg_usage(self):
		print("Reg Mapping: ", self.reg_mapping)
		print("Free Regs: ", self.free_regs)

	def get_temp_reg(self, placeholder, offset = 0):
		if(placeholder == "ZERO"):
			the_reg = "R0"
		else:
			print("Get temp reg: ", placeholder)
			mapping = self.reg_mapping[placeholder]
			the_reg = mapping[offset]
		#if(offset >= len(mapping)):
		#	the_reg = mapping[len(mapping)-1]
		#else:
		#	the_reg = mapping[offset]
		return the_reg

	def transfer_reg(self, proc_namespace, old_placeholder, new_placeholder, offset = 0):
		print("Transfer Reg: ", old_placeholder, " =>",  new_placeholder)
		the_regs = self.reg_mapping[old_placeholder]
		#del self.reg_mapping[old_placeholder]
		if old_placeholder == new_placeholder:
			return the_regs
		if new_placeholder in self.reg_mapping:
			if offset in self.reg_mapping[new_placeholder]:
				print("\t\tTransfer Reg: copying value from %s to placeholder %s" % (old_placeholder, new_placeholder))
				dest_reg = self.get_temp_reg(new_placeholder, offset)
				src_reg = self.get_temp_reg(old_placeholder, offset)
				if dest_reg != src_reg:
					proc_namespace['code'].append('load.r %s, %s' % (dest_reg, src_reg))
				#proc_namespace['code'].append('load.r %s, %s' % (self.get_temp_reg(new_placeholder, offset), self.get_temp_reg(old_placeholder, offset)))
				self.checkin_reg(proc_namespace, old_placeholder, offset)
				return the_regs
			else:
				print("\t\tTransfer Reg: moving regs from %s to placeholder %s" % (old_placeholder, new_placeholder))
				self.reg_mapping[new_placeholder][offset] =  the_regs[offset]
				del self.reg_mapping[old_placeholder]
				#del self.reg_mapping[old_placeholder][offset]
				return the_regs 
		else:
			print("\t\tTransfer Reg: moving regs from %s to placeholder %s" % (old_placeholder, new_placeholder))
			self.reg_mapping[new_placeholder] = { offset: the_regs[offset]}
			del self.reg_mapping[old_placeholder]
			#del self.reg_mapping[old_placeholder][offset]
			return the_regs

	#def checkin_placeholder(self, proc_namespace, placeholder):
	#	if placeholder == "NONE":
	#		return
	#	if proc_namespace['reg_vars'].has_key(placeholder):
	#		return self.reg_mapping[placeholder]
	#	if not self.reg_mapping.has_key(placeholder):
	#		return
	#	print "\t\tRetiring register mappings %s " % (placeholder)
	#	del self.reg_mapping[placeholder]

	def checkin_reg(self, proc_namespace, placeholder, offset = 0):
		print("\t\tCheckin reg: placeholder %s" % (placeholder,))
		print("\t\tCheckin regs: Current register mappings: ", self.reg_mapping)
		print("\t\tCurrent available registers: ", self.free_regs)
		if placeholder in ("NONE","ZERO"):
			print("\t\tplaceholder is None")
			return placeholder
		if placeholder in proc_namespace['reg_vars']:
			print("\t\tRegister Variable not checking in for placeholder %s" % (placeholder,))
			return self.reg_mapping[placeholder][offset]
		if placeholder not in self.reg_mapping:
			print("\t\tNo mapping found for placeholder %s" % (placeholder,))
			return "NONE"
		if self.reg_mapping[placeholder] is None or len(self.reg_mapping[placeholder]) == 0:
			print("\t\tDeleting empty placeholder %s" % (placeholder,))
			del self.reg_mapping[placeholder]
			return "NONE"
		the_regs = self.reg_mapping[placeholder]
		the_reg = the_regs[offset]
		print("\t\tCheckin register %s for placeholder %s" % (the_reg, placeholder))
		if(the_reg not in ('RTNV')):
			self.free_regs.append(the_reg)
		del self.reg_mapping[placeholder][offset]
		if len(self.reg_mapping[placeholder]) == 0:
			del self.reg_mapping[placeholder]
		return the_regs

	def checkout_reg(self, proc_namespace, placeholder, offset = 0):
		if placeholder in proc_namespace['reg_vars']:
			the_reg = self.reg_mapping[placeholder][offset]
			proc_namespace['used_regs'][the_reg] += 1
			return the_reg
		print("\t\tPrevious available registers: ", self.free_regs)
		the_reg = self.free_regs.pop()
		if the_reg in proc_namespace['used_regs']:
			proc_namespace['used_regs'][the_reg] += 1
		else:
			proc_namespace['used_regs'][the_reg] = 1
		if placeholder in self.reg_mapping:
			self.reg_mapping[placeholder][offset] = the_reg
		else:
			self.reg_mapping[placeholder] = { offset: the_reg}
		print("\t\tCurrent available registers: ", self.free_regs)
		print("\t\tCheckout register %s for placeholder %s" % (the_reg, placeholder))
		print("\t\tCurrent register mappings: ", self.reg_mapping)
		return the_reg 


	def process_file(self, filename):
		with open(filename) as infile:
			self.curr_asilfile = infile
			self.process_lines()
		pass


	def optimize_procedure(self, proc_namespace):
		last_instr_index = 0
		new_code_lines = []
		for line_index in range(0, len(proc_namespace['code'])):
			#print "Optimize line %d : %s" % (line_index, proc_namespace['code'][line_index])
			cur_instr = proc_namespace['code'][line_index].split(' ')
			if cur_instr[0] == 'lda' and cur_instr[1] in proc_namespace['used_regs']:
				prev_instr = proc_namespace['code'][last_instr_index].split(' ')
				if prev_instr[0] == 'sta' and cur_instr[1] == prev_instr[1]:
					new_code_lines.pop()
					proc_namespace['used_regs'][cur_instr[1]] -= 1
					#if proc_namespace['used_regs'][cur_instr[1]] > 1:
					#	proc_namespace['used_regs'][cur_instr[1]] -= 1
					#else:
					#	del proc_namespace['used_regs'][cur_instr[1]]
				else:
					new_code_lines.append(proc_namespace['code'][line_index])
			elif cur_instr[0] == 'lda' and cur_instr[1] == '#0':
				new_code_lines.append('clra')
			else:
				new_code_lines.append(proc_namespace['code'][line_index])
			last_instr_index = line_index
		proc_namespace['code'] = new_code_lines
				

	def process_lines(self):
		while(True):
			curr_line = self.curr_asilfile.readline()
			if not curr_line:
				break
			if curr_line.strip() == '':
				continue
			tokens = curr_line.strip('\n').split('\t')

			if(tokens[0] == 'start'):
				self.settings['start_proc'] = tokens[1]
			elif(tokens[0] == 'alloc_global'):
				self.process_global(tokens)
			elif(tokens[0] == 'alloc_literal'):
				self.literal_list[tokens[1]] = tokens[2]
			elif(tokens[0] == 'proc'):
				self.procedures[tokens[1]] = {'locals': {}, 'params': {}, 'param_order': {}, 'param_count': 0, 'used_regs': {}, 'reg_vars':{}, 'code': []}
				self.reset_regs()
				self.process_procedure(tokens[1], self.procedures[tokens[1]])
				#self.optimize_procedure(self.procedures[tokens[1]])
			else:
				pass

			print(tokens)

	def process_global(self, tokens):
		if(len(tokens) > 3):
			if(tokens[3] == 'list'):
				self.global_list[tokens[1]] = {'size': int(tokens[2]), 'type': tokens[4], 'initvalues': tokens[5].split(',')}
			else:
				self.global_list[tokens[1]] = {'size': int(tokens[2]), 'type': tokens[3], 'initvalues': [tokens[4]]}
		else:
			self.global_list[tokens[1]] = {'size': int(tokens[2])}


	def process_procedure(self, proc_name, proc_namespace):
		while(True):
			curr_line = self.curr_asilfile.readline()
			if not curr_line:
				return
			if curr_line.strip() == '':
				continue
			tokens = curr_line.strip('\n').split('\t')

			if(tokens[0] == 'endproc'):
				if(tokens[1] == proc_name):
					return
				else:
					self.errormsg("Invalid end proc not matching proc name")
			elif(tokens[0][:1] == ":"):
				proc_namespace['code'].append("@%s:" % (tokens[0][1:],))
			elif(tokens[0] == ''):
				if(tokens[1] == 'alloc_local'):
					proc_namespace['locals'][tokens[2]] = int(tokens[3])
				elif(tokens[1] == 'alloc_param'):
					proc_namespace['params'][tokens[2]] = 4
					proc_namespace['param_order'][proc_namespace['param_count']] = tokens[2]
					proc_namespace['param_count']+=1
				elif(tokens[1] == 'alloc_register'):
					for index in range(0,(int(math.ceil(int(tokens[3])/4.0)))):
						self.checkout_reg(proc_namespace, tokens[2], index)
					proc_namespace['reg_vars'][tokens[2]] = []
				else:
					proc_namespace['code'].append("; "+curr_line.strip('\n'))
					self.handle_instruction(tokens[1:], proc_namespace)



	#def instr_move(self, proc_namespace, dest, op1, offset = 0):
	#	dest_parts = self.parse_item(dest)
	#	op1_parts = self.parse_item(op1)
	#	if(dest_parts[0] == '~'):
	#		if(op1_parts[0] == '~'):
	#			if(self.get_temp_reg(dest_parts[1]) == self.get_temp_reg(op1_parts[1])):
	#				proc_namespace['code'].append('; ### movr %s, %s' % (self.get_temp_reg(dest_parts[1]), self.get_temp_reg(op1_parts[1])))
	#				return
	#			if(offset == 0 or op1_parts[2] == 'u32'):
	#				proc_namespace['code'].append('movr %s, %s' % (self.get_temp_reg(dest_parts[1],offset), self.get_temp_reg(op1_parts[1],offset)))
	#			else:
	#				proc_namespace['code'].append('movi %s, 0' % (self.get_temp_reg(dest_parts[1],offset)))
	#			self.checkin_reg(proc_namespace, op1_parts[1])
	#		else:
	#			the_item = self.fetch_right_operand(proc_namespace,op1,dest_parts[1], offset)
	#			self.store_result(proc_namespace,dest, the_item, offset)
	#			self.checkin_reg(proc_namespace, the_item, offset)
	#	else:
	#		the_item = self.fetch_right_operand(proc_namespace,op1,'TEMPREG',offset)
	#		self.store_result(proc_namespace,dest, the_item,offset)
	#		self.checkin_reg(proc_namespace, the_item,offset)

	def instr_condbranch(self, proc_namespace, opcode, op1, op2, label):
		op1_info = self.fetch_operand_register(proc_namespace,op1, placeholder = "OP1")
		if opcode in ('beq','bne'):
			op2_info = self.fetch_operand_register(proc_namespace,op2, placeholder = "OP2", allow_small_imm = True)
			branch_instr = "%s.%s" % (opcode, op2_info[0])
		else:
			op2_info = self.fetch_operand_register(proc_namespace,op2, placeholder = "OP2")
			branch_instr = opcode
		proc_namespace['code'].append('%s %s, %s, @%s' % (branch_instr, op1_info[1], op2_info[1], label))
		self.checkin_reg(proc_namespace, op1_info[2])
		self.checkin_reg(proc_namespace, op2_info[2])

	def instr_select(self, proc_namespace, operand, cases, default):
		#	select	*in_char:u8	#13:u8@L15|#10:u8@L16|#127:u8@L17|#8:u8@L18	L19
		op_info = self.fetch_operand_register(proc_namespace,operand)
		for case_select in cases.split("|"):
			case_info = case_select.split("@")
			val_info = self.fetch_operand_register(proc_namespace,case_info[0], allow_small_imm = True)
			proc_namespace['code'].append('beq.%s %s, %s, @%s' % (val_info[0], op_info[1], val_info[1], case_info[1]))
			self.checkin_reg(proc_namespace, val_info[2])
		proc_namespace['code'].append('bra @%s' % (default,))
		self.checkin_reg(proc_namespace, op_info[2])


	def instr_return(self, proc_namespace, operand):
		ref_info = self.get_operand_reference(proc_namespace, operand)
		if not (ref_info[0] == 'r' and ref_info[1] == 'RTNV'):
			proc_namespace['code'].append('load.%s RTNV, %s' % (ref_info[0], ref_info[1],))
		proc_namespace['code'].append('bra @proc_end')



	def instr_storemem(self, proc_namespace, opcode, dest, op1, offset = 0):
		memory_op_dict = {'storemem8': 'b', 'storemem16': 'h', 'storemem32': 'w'}
		memory_op = memory_op_dict[opcode]
		dest_parts = dest.split('@')
		dest_info = self.parse_item(dest_parts[0])
		if len(dest_parts) == 2:
			if (self.is_local_register(proc_namespace, dest_parts[0]) and self.get_item_type(dest_parts[1]) == '#'):
				addr_placeholder = self.get_item_name(dest_parts[0])
				addr_reg = self.get_temp_reg(addr_placeholder)
				#the_reg = self.fetch_operand_register(proc_namespace, op1)
				memory_op += 'x'
				addr_reg = "%s[%s]" % (addr_reg, self.get_item_name(dest_parts[1]))
			else:
				if(dest_info[0] == '~'):
					addr_placeholder = self.get_item_name(dest_parts[0])
					addr_reg = self.get_temp_reg(addr_placeholder)
				else:	
					addr_placeholder = 'TEMPADDR'
					addr_reg = self.checkout_reg(proc_namespace, addr_placeholder)
					ref_info = self.get_operand_reference(proc_namespace, dest_parts[0])
					proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], addr_reg, ref_info[1],))
				index_info = self.get_operand_reference(proc_namespace, dest_parts[1])
				#the_reg = self.fetch_operand_register(proc_namespace, op1)
				if index_info[0] == 'i':
					placeholder = dest_info[1]
					memory_op += 'x'
					addr_reg = "%s[%s]" % (addr_reg, index_info[1])
				else:
					proc_namespace['code'].append('add.%s %s, %s' % (index_info[0], addr_reg, index_info[1],))
		else:
			if(dest_info[0] == '~' or self.is_local_register(proc_namespace, dest_parts[0])):
				addr_placeholder = self.get_item_name(dest_parts[0])
				addr_reg = self.get_temp_reg(addr_placeholder)
				#the_reg = self.fetch_operand_register(proc_namespace, op1)	
			else:
				addr_placeholder = 'TEMPADDR'
				addr_reg = self.checkout_reg(proc_namespace, addr_placeholder)
				ref_info = self.get_operand_reference(proc_namespace, dest_parts[0])
				proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], addr_reg, ref_info[1],))
				#the_reg = self.fetch_operand_register(proc_namespace, op1)
		the_reg = self.fetch_operand_register(proc_namespace, op1)
		self.checkin_reg(proc_namespace, addr_placeholder)
		self.checkin_reg(proc_namespace, the_reg[2])
		proc_namespace['code'].append('store.%s %s, %s' % (memory_op, addr_reg, the_reg[1],))
		return




	def instr_readmem(self, proc_namespace, opcode, dest, op1, offset = 0):
		memory_op_dict = {'readmem8': 'b', 'readmem16': 'h', 'readmem32': 'w'}
		memory_op = memory_op_dict[opcode]
		op1_parts = op1.split('@')
		op1_info = self.parse_item(op1_parts[0])
		if len(op1_parts) == 2:
			if (self.is_local_register(proc_namespace, op1_parts[0]) and self.get_item_type(op1_parts[1]) == '#'):
				addr_placeholder = self.get_item_name(op1_parts[0])
				addr_reg = self.get_temp_reg(addr_placeholder)
				memory_op += 'x'
				addr_reg = "%s[%s]" % (addr_reg, self.get_item_name(op1_parts[1]))
			else:
				if(op1_info[0] == '~'):
					addr_placeholder = self.get_item_name(op1_parts[0])
					addr_reg = self.get_temp_reg(addr_placeholder)
				else:	
					addr_placeholder = 'TEMPADDR'
					addr_reg = self.checkout_reg(proc_namespace, addr_placeholder)
					ref_info = self.get_operand_reference(proc_namespace, op1_parts[0])
					proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], addr_reg, ref_info[1],))
				index_info = self.get_operand_reference(proc_namespace, op1_parts[1])
				if index_info[0] == 'i':
					placeholder = op1_info[1]
					memory_op += 'x'
					addr_reg = "%s[%s]" % (addr_reg, index_info[1])
				else:
					proc_namespace['code'].append('add.%s %s, %s' % (index_info[0], addr_reg, index_info[1],))
		else:
			if(op1_info[0] == '~' or self.is_local_register(proc_namespace, op1_parts[0])):
				addr_placeholder = self.get_item_name(op1_parts[0])
				addr_reg = self.get_temp_reg(addr_placeholder)
			else:
				addr_placeholder = 'TEMPADDR'
				addr_reg = self.checkout_reg(proc_namespace, addr_placeholder)
				ref_info = self.get_operand_reference(proc_namespace, op1_parts[0])
				proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], addr_reg, ref_info[1],))
		the_reg = self.checkout_reg(proc_namespace, 'DEST')
		proc_namespace['code'].append('load.%s %s, %s' % (memory_op, the_reg, addr_reg,))
		self.checkin_reg(proc_namespace, addr_placeholder)
		self.store_result(proc_namespace,dest, 'DEST')
		return


#	def instr_readmem(self, proc_namespace, opcode, dest, op1, offset = 0):
#		memory_op_dict = {'readmem8': 'b', 'readmem16': 'h', 'readmem32': 'w'}
#		memory_op = memory_op_dict[opcode]
#		op1_parts = op1.split('@')
#		addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR')
#		ref_info = self.get_operand_reference(proc_namespace, op1_parts[0])
#		proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], addr_reg, ref_info[1],))
#		if len(op1_parts) == 2:
#			ref_info = self.get_operand_reference(proc_namespace, op1_parts[1])
#			if ref_info[0] == 'i':
#				memory_op += 'x'
#				addr_reg = "%s[%s]" % (addr_reg, ref_info[1])
#			else:
#				proc_namespace['code'].append('add.%s %s, %s' % (ref_info[0], addr_reg, ref_info[1],))
#		the_reg = self.checkout_reg(proc_namespace, 'SRC')
#		proc_namespace['code'].append('load.%s %s, %s' % (memory_op, the_reg, addr_reg,))
#		self.checkin_reg(proc_namespace, 'TEMPADDR')
#		self.store_result(proc_namespace,dest, 'SRC')
#		return


	def instr_move(self, proc_namespace, dest, op1, offset = 0):
		print("Move instruction: ", dest, " <= ", op1)
		self.print_reg_usage()
		dest_parts = dest.split('@')
		dest_info = self.parse_item(dest_parts[0])
		if (dest_info[0] == '~' or self.is_local_register(proc_namespace, dest_parts[0])):
			#self.store_result(proc_namespace,dest, op1_info[1], offset)
			dest_reg = self.checkout_reg(proc_namespace, dest_info[1], offset)
			ref_info = self.get_operand_reference(proc_namespace, op1, offset)
			proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], dest_reg, ref_info[1],))
		else:
			the_reg = self.checkout_reg(proc_namespace, 'SRC', offset)
			ref_info = self.get_operand_reference(proc_namespace, op1, offset)
			proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], the_reg, ref_info[1],))
			self.store_result(proc_namespace,dest, 'SRC', offset)
		return


	def instr_loadlocaladdr(self, proc_namespace, dest, item):
		print("Move instruction: ", dest)
		self.print_reg_usage()
		item_info = self.parse_item(item)
		addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR')
		proc_namespace['code'].append("load.r %s, FRP" % (addr_reg))
		proc_namespace['code'].append("add.i %s, @%s" % (addr_reg, item_info[1]))
		self.store_result(proc_namespace,dest, 'TEMPADDR')
		return


	def instr_loadglobaladdr(self, proc_namespace, dest, item):
		print("Move instruction: ", dest)
		self.print_reg_usage()
		item_info = self.parse_item(item)
		addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR')
		proc_namespace['code'].append("lea %s, %s" % (addr_reg, item_info[1]))
		self.store_result(proc_namespace,dest, 'TEMPADDR')
		return


	def instr_result(self, proc_namespace, dest):
		print("Move instruction: ", dest)
		self.print_reg_usage()
		self.reg_mapping['RTNV'] = { 0: 'RTNV'}
		self.store_result(proc_namespace,dest, 'RTNV')
		return

	def instr_param(self, proc_namespace, operand):
		print("Push instruction: ", operand)
		self.print_reg_usage()
		op_info = self.fetch_operand_register(proc_namespace,operand)
		proc_namespace['code'].append('push %s' % (op_info[1],))
		self.checkin_reg(proc_namespace, op_info[2])
		return


	def instr_alu(self, proc_namespace, opcode, dest, op1, op2, offset = 0):
		print(opcode, " instruction: ", dest, " <= ", op1, " + ", op2)
		self.print_reg_usage()
		dest_reg = self.fetch_left_operand(proc_namespace,dest,op1,'DEST',offset)
		ref_info = self.get_operand_reference(proc_namespace, op2, offset)
		proc_namespace['code'].append('%s.%s %s, %s' % (opcode, ref_info[0], self.get_temp_reg(dest_reg, offset), ref_info[1],))
		self.store_result(proc_namespace,dest,dest_reg, offset)
		return



	def instr_mult(self, proc_namespace, dest, op1, op2, offset = 0):
		print("Multiply instruction: ", dest, " <= ", op1, " + ", op2)
		self.print_reg_usage()
		#ref_info = self.get_operand_reference(proc_namespace, op2, offset)
		op2_info = self.parse_item(op2)
		if (op2_info[0] == '#' and math.log2(int(op2_info[1])).is_integer() and math.log2(int(op2_info[1])) < 16.0):
			dest_reg = self.fetch_left_operand(proc_namespace,dest,op1,'DEST',offset)
			proc_namespace['code'].append('shl.i %s, %s' % (self.get_temp_reg(dest_reg, offset), str(int(math.log2(int(op2_info[1])))),))	
			self.store_result(proc_namespace,dest,dest_reg, offset)
		else:
			self.instr_param(proc_namespace, op1)
			self.instr_param(proc_namespace, op2)
			proc_namespace['code'].append('call __unsigned_multiply__')
			self.instr_result(proc_namespace, dest)	
		return


	def instr_div(self, proc_namespace, dest, op1, op2, offset = 0):
		print("Divide instruction: ", dest, " <= ", op1, " + ", op2)
		self.print_reg_usage()
		#ref_info = self.get_operand_reference(proc_namespace, op2, offset)
		op2_info = self.parse_item(op2)
		if (op2_info[0] == '#' and math.log2(int(op2_info[1])).is_integer() and math.log2(int(op2_info[1])) < 16.0):
			dest_reg = self.fetch_left_operand(proc_namespace,dest,op1,'DEST',offset)
			proc_namespace['code'].append('shr.i %s, %s' % (self.get_temp_reg(dest_reg, offset), str(int(math.log2(int(op2_info[1])))),))	
			self.store_result(proc_namespace,dest,dest_reg, offset)
		else:
			self.instr_param(proc_namespace, op1)
			self.instr_param(proc_namespace, op2)
			proc_namespace['code'].append('call __unsigned_divide__')
			self.instr_result(proc_namespace, dest)	
		return


	def instr_shift(self, proc_namespace, opcode, dest, op1, op2, offset = 0):
		dest_reg = self.fetch_left_operand(proc_namespace,dest,op1,'DEST',offset)
		ref_info = self.fetch_operand_register(proc_namespace, op2, allow_small_imm = True)
		proc_namespace['code'].append('%s.%s %s, %s' % (opcode, ref_info[0], self.get_temp_reg(dest_reg, offset), ref_info[1],))
		self.checkin_reg(proc_namespace, ref_info[2])
		self.store_result(proc_namespace,dest,dest_reg, offset)
		return


	def handle_instruction(self, tokens, proc_namespace):
		print("Handle Instruction: ", tokens)
		#if(tokens[0] == 'storereg'):
		#	self.fetch_operand(proc_namespace,tokens[2])
		#	self.push_result(proc_namespace,tokens[1])

		if(tokens[0] == 'move'):
			self.instr_move(proc_namespace, tokens[1], tokens[2])
		elif(tokens[0] == 'param'):
			self.instr_param(proc_namespace, tokens[2])
		elif(tokens[0] == 'add'):
			self.instr_alu(proc_namespace, 'add', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'sub'):
			self.instr_alu(proc_namespace, 'sub', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'or'):
			self.instr_alu(proc_namespace, 'or', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'xor'):
			self.instr_alu(proc_namespace, 'xor', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'and'):
			self.instr_alu(proc_namespace, 'and', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'mult'):
			self.instr_mult(proc_namespace, tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'div'):
			self.instr_div(proc_namespace, tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'shl'):
			self.instr_shift(proc_namespace, 'shl', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'shr'):
			self.instr_shift(proc_namespace, 'shr', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'branchneq'):
			self.instr_condbranch(proc_namespace, 'bne', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'brancheq'):
			self.instr_condbranch(proc_namespace, 'beq', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'branchlte'):
			self.instr_condbranch(proc_namespace, 'blte', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'branchgte'):
			self.instr_condbranch(proc_namespace, 'blte', tokens[2], tokens[1], tokens[3])
		elif(tokens[0] == 'branchgt'):
			self.instr_condbranch(proc_namespace, 'blt', tokens[2], tokens[1], tokens[3])
		elif(tokens[0] == 'branchlt'):
			self.instr_condbranch(proc_namespace, 'blt', tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'branch'):
			proc_namespace['code'].append('bra @%s' % (tokens[1],))
		elif(tokens[0] == 'select'):
			self.instr_select(proc_namespace, tokens[1], tokens[2], tokens[3])
		elif(tokens[0] == 'trash'):
			self.checkin_reg(proc_namespace,tokens[1])
		elif(tokens[0] == 'increment'):
			if(self.parse_item(tokens[1])[2] == 'u32'):
				self.instr_add(proc_namespace, tokens[1], tokens[1], '#1:u8', 0)
				self.instr_add(proc_namespace, tokens[1], tokens[1], '#0:u8', 1)
			else:
				self.instr_add(proc_namespace, tokens[1], tokens[1], '#1:u8')
		elif(tokens[0] in ('result8','result16','result32')):
			self.instr_result(proc_namespace, tokens[1])
		elif(tokens[0] in ('return8','return16','return32')):
			self.instr_return(proc_namespace, tokens[1])
		elif(tokens[0] == 'return'):
			proc_namespace['code'].append('bra @proc_end')
		elif(tokens[0] == 'call'):
			proc_namespace['code'].append('call %s' % (tokens[1],))
		elif(tokens[0] == 'pop'):
			self.store_result(proc_namespace,tokens[1]) 
		elif(tokens[0] == 'push'):
			self.push_item(proc_namespace,tokens[1]) 
		elif(tokens[0] == 'loadlocaladdr'):
			self.instr_loadlocaladdr(proc_namespace, tokens[1], tokens[2])
		elif(tokens[0] == 'loadglobaladdr'):
			self.instr_loadglobaladdr(proc_namespace, tokens[1], tokens[2])
		elif(tokens[0] == 'loadliteraladdr'):
			self.instr_loadglobaladdr(proc_namespace, tokens[1], tokens[2])
		elif(tokens[0] in ('storemem8','storemem16','storemem32')):
			self.instr_storemem(proc_namespace, tokens[0], tokens[1], tokens[2])
		elif(tokens[0] in ('readmem8','readmem16','readmem32')):
			self.instr_readmem(proc_namespace, tokens[0], tokens[1], tokens[2])
		else:
			self.errormsg("Instruction not found \"%s\"" % (tokens[0],))



	def get_dest_placeholder(self, proc_namespace, item, placeholder = 'TEMPREG', offset = 0):
		item_parts = item.split('@')
		item_info = self.parse_item(item_parts[0])
		if len(item_parts) == 1:
			print("\tGet Dest operand: ", item_info)
			#if item_info[2] == 'u8':
			if item_info[0] == '~':
				the_reg = self.checkout_reg(proc_namespace, item_info[1], offset)
				return item_info[1]
			else:
				the_reg = self.checkout_reg(proc_namespace, placeholder, offset)
				return placeholder
		else:
			the_reg = self.checkout_reg(proc_namespace, placeholder, offset)
			return placeholder


	def fetch_left_operand(self, proc_namespace, dest, item, placeholder = 'TEMPREG', offset = 0):
		dest_info = self.parse_item(dest)
		item_info = self.parse_item(item)
		print("\tFetch operand: ", item_info, " placeholder: ", placeholder)
		offset_text = "" if offset == 0 else "+%d" % (offset*2,)
		if(item_info[0] == '~'):
			return item_info[1]
		elif(((dest_info[0] == '~' and item_info[0] == '~') or item_info[1] in proc_namespace['reg_vars']) and dest_info[1] == item_info[1]):
			the_reg = self.checkout_reg(proc_namespace, item_info[1], offset)
			return item_info[1]
		else:
			the_reg = self.checkout_reg(proc_namespace, placeholder, offset)
			ref_info = self.get_operand_reference(proc_namespace, item, offset)
			proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], the_reg, ref_info[1],))
			return placeholder



	def fetch_operand_register(self, proc_namespace, operand, placeholder = "SRC", allow_small_imm = False):
		operand_parts = operand.split('@')
		#placeholder = "SRC"
		operand_info = self.parse_item(operand_parts[0])
		if (operand_info[0] == '~' or (operand_info[0] == '*' and operand_info[1] in proc_namespace['reg_vars'])):
			the_reg = self.get_temp_reg(operand_info[1])
			placeholder = operand_info[1]
			#self.checkin_reg(proc_namespace, operand_info[1])
		elif (allow_small_imm and operand_info[0] == '#' and (int(operand_info[1]) < 16)):
			return ['i', operand_info[1],"NONE"]
		else:
			the_reg = self.checkout_reg(proc_namespace, placeholder)
			ref_info = self.get_operand_reference(proc_namespace, operand)
			proc_namespace['code'].append('load.%s %s, %s' % (ref_info[0], the_reg, ref_info[1],))
			#self.checkin_reg(proc_namespace, 'SRC')
		return ['r', the_reg, placeholder]



	def get_operand_reference(self, proc_namespace, item, offset = 0):
		item_parts = item.split('@')
		offset_text = "" if offset == 0 else "+%d" % (offset*2,)
		item_info = self.parse_item(item_parts[0])
		if len(item_parts) == 1:
			print("\tFetch operand: ", item_info)
			#if item_info[2] == 'u8':
			if (item_info[0] == '~' or (item_info[0] == '*' and item_info[1] in proc_namespace['reg_vars'])):
				print("Item info: ", item_info)
				the_reg = self.get_temp_reg(item_info[1])
				self.checkin_reg(proc_namespace, item_info[1], offset)
				return ['r',the_reg]
			elif item_info[0] in ('*','&'):
				if item_info[2] == 'u8':
					suffix = 'bux'
				elif item_info[2] == 'u16':
					suffix = 'hux'
				else:
					suffix = 'wx'
				return [suffix,"FRP[@%s%s]" % (item_info[1], offset_text)]
			elif item_info[0] == '$':
				the_reg = self.checkout_reg(proc_namespace, 'TEMPADDR', offset)
				proc_namespace['code'].append("lea %s, %s" % (the_reg, item_info[1]))
				if item_info[2] == 'u8':
					suffix = 'bu'
				elif item_info[2] == 'u16':
					suffix = 'hu'
				else:
					suffix = 'w'
				self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
				return [suffix, the_reg]
			elif item_info[0] == '#':
				return ['i', item_info[1]]
			else:
				self.errormsg()
		else:
			index_info = self.parse_item(item_parts[1])
			if item_info[0] == '$':
				addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR', offset)
				proc_namespace['code'].append("lea %s, %s" % (addr_reg, item_info[1]))
				if index_info[0] == '#':
					if item_info[2] == 'u8':
						suffix = 'bux'
					elif item_info[2] == 'u16':
						suffix = 'hux'
					else:
						suffix = 'wx'
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					return [suffix,"%s[%s]" % (addr_reg, index_info[1])]
				else:
					calc_parts = self.get_operand_reference(proc_namespace, item_parts[1], offset)
					proc_namespace['code'].append("add.%s %s, %s" % (calc_parts[0], addr_reg, calc_parts[1]))
					if item_info[2] == 'u8':
						suffix = 'bu'
					elif item_info[2] == 'u16':
						suffix = 'hu'
					else:
						suffix = 'w'
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					return [suffix, addr_reg]
					self.errormsg()
			elif item_info[0] in ('*','&'):
				addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR', offset)
				proc_namespace['code'].append("load.r %s, FRP" % (addr_reg))
				proc_namespace['code'].append("add.i %s, @%s" % (addr_reg, item_info[1]))
				#self.checkin_reg(proc_namespace, index_info[1], offset)
				if index_info[0] == '#':
					if item_info[2] == 'u8':
						suffix = 'bux'
					elif item_info[2] == 'u16':
						suffix = 'hux'
					else:
						suffix = 'wx'
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					return [suffix,"%s[%s]" % (addr_reg, index_info[1])]
				else:
					calc_parts = self.get_operand_reference(proc_namespace, item_parts[1], offset)
					proc_namespace['code'].append("add.%s %s, %s" % (calc_parts[0], addr_reg, calc_parts[1]))
					if item_info[2] == 'u8':
						suffix = 'bu'
					elif item_info[2] == 'u16':
						suffix = 'hu'
					else:
						suffix = 'w'
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					return [suffix, addr_reg]
					self.errormsg()
			else:
				self.errormsg()




	def store_result(self, proc_namespace, item, placeholder = 'TEMPREG', offset = 0):
		item_parts = item.split('@')
		offset_text = "" if offset == 0 else "+%d" % (offset*2,)
		item_info = self.parse_item(item_parts[0])
		# ###
		print("\tStore Result: ", item_info)
		if(len(item_parts) == 1):
			if (item_info[0] == '~' or item_info[1] in proc_namespace['reg_vars']):
				return self.transfer_reg(proc_namespace, placeholder, item_info[1], offset)
				#return self.get_temp_reg(proc_namespace, placeholder)
			elif item_info[0] in ('*','&'):
				the_reg = self.get_temp_reg(placeholder, offset)
				if item_info[2] == 'u8':
					proc_namespace['code'].append('store.bx FRP[@%s%s], %s' % (item_info[1], offset_text, the_reg))
				elif item_info[2] == 'u16':
					proc_namespace['code'].append('store.hx FRP[@%s%s], %s' % (item_info[1], offset_text, the_reg))
				else:
					proc_namespace['code'].append('store.wx FRP[@%s%s], %s' % (item_info[1], offset_text, the_reg))
				self.checkin_reg(proc_namespace, placeholder, offset)
				return the_reg
			elif item_info[0] == '$':
				the_reg = self.get_temp_reg(placeholder, offset)
				addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR', offset)
				proc_namespace['code'].append("lea %s, %s" % (addr_reg, item_info[1]))
				if item_info[2] == 'u8':
					proc_namespace['code'].append('store.b %s, %s' % (addr_reg, the_reg))
				elif item_info[2] == 'u16':
					proc_namespace['code'].append('store.h %s, %s' % (addr_reg, the_reg))
				else:
					proc_namespace['code'].append('store.w %s, %s' % (addr_reg, the_reg))
				self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
				self.checkin_reg(proc_namespace, placeholder, offset)
				return the_reg
			else:
				self.errormsg()
		else:
			index_info = self.parse_item(item_parts[1])
			the_reg = self.get_temp_reg(placeholder, offset)
			if item_info[0] == '$':
				addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR', offset)
				proc_namespace['code'].append("lea %s, %s" % (addr_reg, item_info[1]))
				if index_info[0] == '#':
					if item_info[2] == 'u8':
						proc_namespace['code'].append('store.bx %s[%s%s], %s' % (addr_reg, index_info[1], offset_text, the_reg))
					elif item_info[2] == 'u16':
						proc_namespace['code'].append('store.hx %s[%s%s], %s' % (addr_reg, index_info[1], offset_text, the_reg))
					else:
						proc_namespace['code'].append('store.wx %s[%s%s], %s' % (addr_reg, index_info[1], offset_text, the_reg))
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					self.checkin_reg(proc_namespace, placeholder, offset)
					return the_reg
				else:
					calc_parts = self.get_operand_reference(proc_namespace, item_parts[1], offset)
					proc_namespace['code'].append("add.%s %s, %s" % (calc_parts[0], addr_reg, calc_parts[1]))
					if item_info[2] == 'u8':
						proc_namespace['code'].append('store.b %s, %s' % (addr_reg, the_reg))
					elif item_info[2] == 'u16':
						proc_namespace['code'].append('store.h %s, %s' % (addr_reg, the_reg))
					else:
						proc_namespace['code'].append('store.w %s, %s' % (addr_reg, the_reg))
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					self.checkin_reg(proc_namespace, placeholder, offset)
					return the_reg
			elif item_info[0] == '*':
				addr_reg = self.checkout_reg(proc_namespace, 'TEMPADDR', offset)
				proc_namespace['code'].append("load.r %s, FRP" % (addr_reg))
				proc_namespace['code'].append("add.i %s, @%s" % (addr_reg, item_info[1]))
				if index_info[0] == '#':
					if item_info[2] == 'u8':
						proc_namespace['code'].append('store.bx %s[%s%s], %s' % (addr_reg, index_info[1], offset_text, the_reg))
					elif item_info[2] == 'u16':
						proc_namespace['code'].append('store.hx %s[%s%s], %s' % (addr_reg, index_info[1], offset_text, the_reg))
					else:
						proc_namespace['code'].append('store.wx %s[%s%s], %s' % (addr_reg, index_info[1], offset_text, the_reg))
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					self.checkin_reg(proc_namespace, placeholder, offset)
					return the_reg
				else:
					calc_parts = self.get_operand_reference(proc_namespace, item_parts[1], offset)
					proc_namespace['code'].append("add.%s %s, %s" % (calc_parts[0], addr_reg, calc_parts[1]))
					if item_info[2] == 'u8':
						proc_namespace['code'].append('store.b %s, %s' % (addr_reg, the_reg))
					elif item_info[2] == 'u16':
						proc_namespace['code'].append('store.h %s, %s' % (addr_reg, the_reg))
					else:
						proc_namespace['code'].append('store.w %s, %s' % (addr_reg, the_reg))
					self.checkin_reg(proc_namespace, 'TEMPADDR', offset)
					self.checkin_reg(proc_namespace, placeholder, offset)
					return the_reg
			else:
				self.errormsg()



	def push_item(self, proc_namespace, item):
		item_info = self.parse_item(item)
		#print "Fetch to accumulator: ", item_info
		if item_info[0] == '~':
			if item_info[2] == 'u8':
				proc_namespace['code'].append('lda @%s' % (self.checkin_reg(proc_namespace,item_info[1]),))
				proc_namespace['code'].append('pha')
			else:
				proc_namespace['code'].append('ldc @%s' % (self.checkin_reg(proc_namespace,item_info[1]),))
				proc_namespace['code'].append('phc')
		elif item_info[0] in ('*','&'):
			if item_info[2] == 'u8':
				proc_namespace['code'].append('lda @%s' % (item_info[1],))
				proc_namespace['code'].append('pha')
			else:
				proc_namespace['code'].append('ldc @%s' % (item_info[1],))
				proc_namespace['code'].append('phc')
		elif item_info[0] in ('$'):
			if item_info[2] == 'u8':
				proc_namespace['code'].append('lda %s' % (item_info[1],))
				proc_namespace['code'].append('pha')
			else:
				proc_namespace['code'].append('ldc %s' % (item_info[1],))
				proc_namespace['code'].append('phc')
		elif item_info[0] == '#':
			proc_namespace['code'].append('phi #%s' % (item_info[1],))
		else:
			pass


	def handle_indexing(self, proc_namespace, instr, ref_item, index_item, offset = 0):
		print("Handle Indexing Ref_item: ", ref_item)
		print("Handle Indexing index_item: ", index_item)
		index_parts = self.parse_item(index_item)
		ref_parts = self.parse_item(ref_item)
		print("Index_item: ", index_parts)
		if ref_parts[0] == '~':
			if index_parts[0] == '~':
				if index_parts[2] == 'u8':
					proc_namespace['code'].append('ldy @%s' % (self.checkin_reg(proc_namespace,index_parts[1]),))
					return ("%s (@%s),Y" % (instr, self.checkin_reg(proc_namespace,ref_parts[1])))
				else:
					proc_namespace['code'].append('ldy #0')
					self.instr_adc16(proc_namespace, "~TEMPADDR:u16", index_parts[1], ref_parts[1])
					return ("%s (@%s)" % (instr, self.get_temp_reg(proc_namespace,"TEMPADDR")))
			elif index_parts[0] in ('*','&'):
				if index_parts[2] == 'u8':
					proc_namespace['code'].append('ldy @%s' % (index_parts[1],))
					return ("%s (@%s),Y" % (instr, self.checkin_reg(proc_namespace,ref_parts[1])))
				else:
					proc_namespace['code'].append('ldy #0')
					self.instr_adc16(proc_namespace, "~TEMPADDR:u16", index_parts[1], ref_parts[1])
					return ("%s (@%s)" % (instr, self.get_temp_reg(proc_namespace,"TEMPADDR")))
			elif index_parts[0] in ('$'):
				if index_parts[2] == 'u8':
					proc_namespace['code'].append('ldy @%s' % (index_parts[1],))
					return ("%s (@%s),Y" % (instr, self.checkin_reg(proc_namespace,ref_parts[1])))
				else:
					proc_namespace['code'].append('ldy #0')
					self.instr_adc16(proc_namespace, "~TEMPADDR:u16", index_parts[1], ref_parts[1])
					return ("%s (@%s)" % (instr, self.get_temp_reg(proc_namespace,"TEMPADDR")))
			elif index_parts[0] == '#':
				if index_parts[2] == 'u8':
					proc_namespace['code'].append('ldy #%s' % (index_parts[1],))
					return ("%s (@%s),Y" % (instr, self.checkin_reg(proc_namespace,ref_parts[1])))
				else:
					proc_namespace['code'].append('ldz #%s' % (index_parts[1],))
					return ("%s (@%s),Z" % (instr, self.checkin_reg(proc_namespace,ref_parts[1])))
			else:
				self.errormsg()
		elif ref_parts[0] == '#':
			if index_parts[0] == '~':
				proc_namespace['code'].append('lea %s' % (ref_parts[1],))
				proc_namespace['code'].append('add %s' % (self.checkin_reg(proc_namespace,index_parts[1]),))
				proc_namespace['code'].append('sta %s' % (self.checkout_reg(proc_namespace,'TMPADDR'),))
				return ("%s [%s]" % (instr, self.checkin_reg(proc_namespace,'TMPADDR')))
			elif index_parts[0] == '#':
				return ("%s %d" % (instr, int(ref_parts[1])+int(index_parts[1])))
			else:
				self.errormsg()
		elif ref_parts[0] == '$':
			if index_parts[2] == 'u8':				
				if offset > 0:
					proc_namespace['code'].append('iny') 
				elif index_parts[0] == '~':
					proc_namespace['code'].append('ldy @%s' % (self.checkin_reg(proc_namespace,index_parts[1]),))
				elif index_parts[0] in ('*','&'):
					proc_namespace['code'].append('ldy @%s' % (index_parts[1],))
				elif index_parts[0] == '#':
					proc_namespace['code'].append('ldy #%s' % (index_parts[1],))
				return ("%s %s,Y" % (instr, ref_parts[1]))
			else:
				imm_addr_item = "#" + ref_item[1:] 
				if offset == 0:
					self.instr_adc16(proc_namespace, "~TEMPADDR:u16", imm_addr_item, index_item)
					return ("%s (@%s)" % (instr, self.get_temp_reg(proc_namespace,"TEMPADDR"))) 
				else:
					proc_namespace['code'].append('ldy #%d' % (offset,))
					return ("%s (@%s),Y" % (instr, self.get_temp_reg(proc_namespace,"TEMPADDR"))) 
		else:
			self.errormsg()


	def handle_pointer(self, proc_namespace, ref_item):
		if ref_item[0] == '~':
			return ("%s [%s]" % (instr, self.checkin_reg(proc_namespace,ref_item[1])))
		elif ref_item[0] == '#':
			return ("%s %s" % (instr, ref_item[1]))
		else:
			self.errormsg()

	def is_local_register(self, proc_namespace, item):
		item_info = self.parse_item(item)
		if (item_info[0] == '*' and item_info[1] in proc_namespace['reg_vars']):
			return True
		else:
			return False


	def get_item_type(self, item):
		return self.parse_item(item)[0]

	def get_item_name(self, item):
		return self.parse_item(item)[1]

	def get_item_datatype(self, item):
		return self.parse_item(item)[1]

	def parse_item(self, item):
		split_item = item.split('@') 
		split_item = split_item[0].split(':') 
		return [split_item[0][0], split_item[0][1:], split_item[1]]
		#if item.find('@') >= 0:
		#	index_split = item.split('@')
		#	split_item = index_split[0].split(':') 
		#	return [split_item[0][0], split_item[0][1:], split_item[1], index_split[1]]
		#else: 
		#	split_item = item.split(':') 
		#	return [split_item[0][0], split_item[0][1:], split_item[1]]

	def output_asm(self, outfile_handle):
		#outfile_handle.write(".include \"stdlib.inc\"\n\n")
		#outfile_handle.write("\n.section startup\n")
		#outfile_handle.write("start_program:\n")
		#outfile_handle.write("\tcall %s\n" % (self.settings['start_proc'],))
		#outfile_handle.write("\tjump start_program\n")

		outfile_handle.write("\n.section code\n")
		for proc_name in list(self.procedures.keys()):
			outfile_handle.write("\n\n%s:\n\tinit_frame\n" % (proc_name,))
			for reg_name in self.procedures[proc_name]['used_regs']:
				reg_use_count = self.procedures[proc_name]['used_regs'][reg_name]
				outfile_handle.write("\treserve_register %s  ;Used %d times \n" % (reg_name, reg_use_count))
			for local_name in self.procedures[proc_name]['locals']:
				outfile_handle.write("\tdeclare_local @%s, %d\n" % (local_name, self.procedures[proc_name]['locals'][local_name]))
			param_list = list(self.procedures[proc_name]['param_order'].keys())
			param_list.sort(reverse=True)
			for param_ord in param_list:
				outfile_handle.write("\tdeclare_parameter @%s\n" % (self.procedures[proc_name]['param_order'][param_ord],))
			#for param_name in self.procedures[proc_name]['params']:
			#	outfile_handle.write("\tdeclare_parameter @%s\n" % (param_name,))
			outfile_handle.write("\tstart_frame\n@start:\n")
			for code_line in self.procedures[proc_name]['code']:
				print(" > ", code_line)
				if code_line.endswith(":"):
					outfile_handle.write("%s\n" % (code_line,))
				else:
					outfile_handle.write("\t%s\n" % (code_line,))
			outfile_handle.write("@proc_end:\n")
			outfile_handle.write("\tend_frame\n\tret\n")

		outfile_handle.write("\n.section rodata\n")
		for literal_name in self.literal_list:
			outfile_handle.write("%s:\n" % (literal_name,))
			outfile_handle.write("\t.byte %s\n" % (self.literal_list[literal_name],))

		outfile_handle.write("\n.section data\n")
		for global_name in self.global_list:
			if ('initvalues' in self.global_list[global_name]):
				outfile_handle.write("%s:\n" % (global_name,))
				print(self.global_list[global_name])
				outfile_handle.write("\t.%s %s\n" % (self.global_list[global_name]['type'], ", ".join(self.global_list[global_name]['initvalues']),))

		outfile_handle.write("\n.section bss\n")
		for global_name in self.global_list:
			if not ('initvalues' in self.global_list[global_name]):
				outfile_handle.write("%s:\n" % (global_name,))
				outfile_handle.write("\t.buffer %d\n" % (self.global_list[global_name]['size'],))
			

	def output_internals(self, outfile_handle):
		outfile_handle.write("Globals\n")
		pprint.pprint(self.global_list, stream = outfile_handle)
		outfile_handle.write("Settings\n")
		pprint.pprint(self.settings, stream = outfile_handle)
		outfile_handle.write("Procedures\n")
		pprint.pprint(self.procedures, stream = outfile_handle)


def main_program():
	argparse = optparse.OptionParser(description="Absurd Systems ASIL Code Generator to AS32X Native Code",
												usage="usage: codegen_as32x.py [options] src-file",
												version="version 0.5 by Michael Burns")

	argparse.add_option("-o","--outfile",dest="outfilename",default="NONE",help="Machine code output file")
	#argparse.add_option("-s","--listfile",dest="listfilename",default="NONE",help="Code and Symbol Listing file") 
	#argparse.add_option("-d","--definefile",dest="definefilename",default="NONE",help="Generate defines from Global symbols to file")
	#argparse.add_option("-f","--outfileformat",dest="fileformat",default="intelhex",help="Machine code file format(intelhex,srecord)")
	#argparse.add_option("-m","--outfilemask",dest="outmask",default="FFFF",help="Machine code output address mask")

	#command_line = "-o ../mikeos_sim/kernel.hex -s ../mikeos/kernel.lst ../mikeos/kernel.asm"
	#(options, args) = argparse.parse_args(args=command_line.split(" "))
	(options, args) = argparse.parse_args()
	if len(args) < 1:
		print("*** No input files given")
		return

	outfilename = options.outfilename
	#fileformat = options.fileformat
	#definefilename = options.definefilename
	#outaddrmask = int(options.outmask,16)


	codegen_inst = AS1602_Codegen()
	for infilename in args:
		full_filename = os.path.abspath(infilename)
		codegen_inst.process_file(full_filename)


	if outfilename != "NONE":
		with open(os.path.abspath(outfilename),'w') as outfile:
			codegen_inst.output_asm(outfile)
			#codegen_inst.output_internals(outfile)

if __name__ == "__main__":
	main_program()


