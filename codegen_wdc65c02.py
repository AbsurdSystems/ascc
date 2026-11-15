
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
      self.reset_regs()
      self.initialized_data = {}
      self.settings = {}

   def reset_regs(self):
      #self.free_regs = ['R7','R6','R5','R4','R3','R2','R1','R0']
      self.free_regs = ['_TEMP7','_TEMP6','_TEMP5','_TEMP4','_TEMP3','_TEMP2','_TEMP1','_TEMP0']
      self.reg_mapping = {}

   def get_temp_reg(self, proc_namespace, placeholder):
      the_reg = self.reg_mapping[placeholder]
      return the_reg

   def checkin_reg(self, proc_namespace, placeholder):
      if placeholder == "NONE":
         return placeholder
      if placeholder in proc_namespace['reg_vars']:
         return self.reg_mapping[placeholder]
      if placeholder not in self.reg_mapping:
         return "NONE"
      print(self.reg_mapping)
      the_reg = self.reg_mapping[placeholder]
      self.free_regs.append(the_reg)
      del self.reg_mapping[placeholder]
      return the_reg

   def checkout_reg(self, proc_namespace, placeholder):
      if placeholder in proc_namespace['reg_vars'] or placeholder in self.reg_mapping:
         the_reg = self.reg_mapping[placeholder]
         proc_namespace['used_regs'][the_reg] += 1
         return the_reg
      the_reg = self.free_regs.pop()
      if the_reg in proc_namespace['used_regs']:
         proc_namespace['used_regs'][the_reg] += 1
      else:
         proc_namespace['used_regs'][the_reg] = 1
      self.reg_mapping[placeholder] = the_reg
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
               #   proc_namespace['used_regs'][cur_instr[1]] -= 1
               #else:
               #   del proc_namespace['used_regs'][cur_instr[1]]
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
            self.global_list[tokens[1]] = int(tokens[2])
         elif(tokens[0] == 'proc'):
            self.procedures[tokens[1]] = {'locals': {}, 'params': {}, 'used_regs': {}, 'reg_vars':{}, 'code': []}
            self.reset_regs()
            self.process_procedure(tokens[1], self.procedures[tokens[1]])
            #self.optimize_procedure(self.procedures[tokens[1]])
         else:
            pass

         print(tokens)

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
               if(tokens[3] == 'P'):
                  proc_namespace['locals'][tokens[2]] = 2
               else:
                  proc_namespace['locals'][tokens[2]] = int(tokens[3])
            elif(tokens[1] == 'alloc_param'):
               proc_namespace['params'][tokens[2]] = 2
            elif(tokens[1] == 'alloc_register'):
               the_reg = self.free_regs.pop()
               proc_namespace['reg_vars'][tokens[2]] = the_reg
               proc_namespace['used_regs'][the_reg] = 0
               self.reg_mapping[tokens[2]] = the_reg
            #elif(tokens[1] == 'alloc_register'):
            #   proc_namespace['registers'][tokens[2]] = 0
            else:
               proc_namespace['code'].append("; "+curr_line.strip('\n'))
               self.handle_instruction(tokens[1:], proc_namespace)


   def instr_adc8(self, proc_namespace, dest, op1, op2):
      op_info = self.fetch_imm_operand(proc_namespace,op2)
      lval_item = self.fetch_operand(proc_namespace,op1)
      proc_namespace['code'].append('clc')
      proc_namespace['code'].append('adc %s' % (op_info['reference'],))
      self.checkin_reg(proc_namespace, lval_item)
      self.checkin_reg(proc_namespace, op_info['placeholder'])
      self.store_result(proc_namespace,dest)
      return

   def instr_adc16(self, proc_namespace, dest, op1, op2):
      op_info = self.fetch_imm_operand(proc_namespace,op2)
      lval_item = self.fetch_operand(proc_namespace,op1)
      proc_namespace['code'].append('clc')
      proc_namespace['code'].append('adc %s' % (op_info['reference'],))
      self.store_result(proc_namespace,dest)
      op_info = self.fetch_imm_operand(proc_namespace,op2,1)
      self.fetch_operand(proc_namespace,op1,1)
      proc_namespace['code'].append('adc %s' % (op_info['reference'],))
      self.store_result(proc_namespace,dest,1)
      self.checkin_reg(proc_namespace, lval_item)
      self.checkin_reg(proc_namespace, op_info['placeholder'])
      return

   def instr_sbc8(self, proc_namespace, dest, op1, op2):
      op_info = self.fetch_imm_operand(proc_namespace,op2)
      lval_item = self.fetch_operand(proc_namespace,op1)
      proc_namespace['code'].append('sec')
      proc_namespace['code'].append('sbc %s' % (op_info['reference'],))
      self.checkin_reg(proc_namespace, lval_item)
      self.checkin_reg(proc_namespace, op_info['placeholder'])
      self.store_result(proc_namespace,dest)
      return

   def instr_sbc16(self, proc_namespace, dest, op1, op2):
      op_info = self.fetch_imm_operand(proc_namespace,op2)
      lval_item = self.fetch_operand(proc_namespace,op1)
      proc_namespace['code'].append('sec')
      proc_namespace['code'].append('sbc %s' % (op_info['reference'],))
      self.store_result(proc_namespace,dest)
      op_info = self.fetch_imm_operand(proc_namespace,op2,1)
      self.fetch_operand(proc_namespace,op1,1)
      proc_namespace['code'].append('sbc %s' % (op_info['reference'],))
      self.store_result(proc_namespace,dest,1)
      self.checkin_reg(proc_namespace, lval_item)
      self.checkin_reg(proc_namespace, op_info['placeholder'])
      return

   def instr_cmp8(self, proc_namespace, op1, op2, label, cond_instr):
      op_info = self.fetch_imm_operand(proc_namespace,op2)
      lval_item = self.fetch_operand(proc_namespace,op1)
      proc_namespace['code'].append('cmp %s' % (op_info['reference'],))
      self.checkin_reg(proc_namespace, lval_item)
      self.checkin_reg(proc_namespace, op_info['placeholder'])
      proc_namespace['code'].append('%s @%s' % (cond_instr,label))
      return

   def instr_cmp16(self, proc_namespace, op1, op2, label, cond_instr):
      op_info = self.fetch_imm_operand(proc_namespace,op2)
      lval_item = self.fetch_operand(proc_namespace,op1)
      proc_namespace['code'].append('cmp %s' % (op_info['reference'],))
      proc_namespace['code'].append('%s @%s' % (cond_instr,label))
      op_info = self.fetch_imm_operand(proc_namespace,op2,1)
      self.fetch_operand(proc_namespace,op1,1)
      proc_namespace['code'].append('cmp %s' % (op_info['reference'],))
      self.checkin_reg(proc_namespace, lval_item)
      self.checkin_reg(proc_namespace, op_info['placeholder'])
      proc_namespace['code'].append('%s @%s' % (cond_instr,label))
      return


   def instr_shl8(self, proc_namespace, dest, op1, op2):
      the_item = self.fetch_operand(proc_namespace,op1)
      self.store_result(proc_namespace,dest)
      self.checkin_reg(proc_namespace, the_item)
      dest_parts = self.parse_item(dest) 
      if dest_parts[0] in ('~','*','&'):
         proc_namespace['code'].append('asl @%s,X' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      elif item_info[0] == '$':
         proc_namespace['code'].append('asl %s' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      else:
         pass
      return

   def instr_shl16(self, proc_namespace, dest, op1, op2):
      the_item = self.fetch_operand(proc_namespace,op1)
      self.store_result(proc_namespace,dest)
      self.fetch_operand(proc_namespace,op1,1)
      self.store_result(proc_namespace,dest,1)
      self.checkin_reg(proc_namespace, the_item)
      dest_parts = self.parse_item(dest) 
      if dest_parts[0] in ('~','*','&'):
         proc_namespace['code'].append('asl @%s,X' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
         proc_namespace['code'].append('rol @%s+1,X' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      elif item_info[0] == '$':
         proc_namespace['code'].append('asl %s' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
         proc_namespace['code'].append('rol %s+1' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      else:
         pass
      return

   def instr_shr8(self, proc_namespace, dest, op1, op2):
      the_item = self.fetch_operand(proc_namespace,op1)
      self.store_result(proc_namespace,dest)
      self.checkin_reg(proc_namespace, the_item)
      dest_parts = self.parse_item(dest) 
      if dest_parts[0] in ('~','*','&'):
         proc_namespace['code'].append('lsr @%s,X' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      elif item_info[0] == '$':
         proc_namespace['code'].append('lsr %s' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      else:
         pass
      return

   def instr_shr16(self, proc_namespace, dest, op1, op2):
      the_item = self.fetch_operand(proc_namespace,op1)
      self.store_result(proc_namespace,dest)
      self.fetch_operand(proc_namespace,op1,1)
      self.store_result(proc_namespace,dest,1)
      self.checkin_reg(proc_namespace, the_item)
      dest_parts = self.parse_item(dest) 
      if dest_parts[0] in ('~','*','&'):
         proc_namespace['code'].append('lsr @%s,X' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
         proc_namespace['code'].append('ror @%s+1,X' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      elif item_info[0] == '$':
         proc_namespace['code'].append('lsr %s' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
         proc_namespace['code'].append('ror %s+1' % (self.get_temp_reg(proc_namespace, dest_parts[1])))
      else:
         pass
      return


   def handle_instruction(self, tokens, proc_namespace):
      print("Handle Instruction: ", tokens)
      #if(tokens[0] == 'storereg'):
      #   self.fetch_operand(proc_namespace,tokens[2])
      #   self.push_result(proc_namespace,tokens[1])

      if(tokens[0] == 'move'):
         dest_type = self.parse_item(tokens[1])[2]
         src_type = self.parse_item(tokens[2])[2]
         if dest_type in ('u16','P'):
            the_item = self.fetch_operand(proc_namespace,tokens[2])
            self.store_result(proc_namespace,tokens[1])
            self.fetch_operand(proc_namespace,tokens[2],1)
            self.store_result(proc_namespace,tokens[1],1)
            self.checkin_reg(proc_namespace, the_item)
         else:
            the_item = self.fetch_operand(proc_namespace,tokens[2])
            self.checkin_reg(proc_namespace, the_item)
            self.store_result(proc_namespace,tokens[1])
      elif(tokens[0] == 'param'):
         param_position = self.parse_item(tokens[1])
         src_type = self.parse_item(tokens[2])[2]
         if src_type in ('u16','P'):
            the_item = self.fetch_operand(proc_namespace,tokens[2])
            proc_namespace['code'].append('sta PARAMS-%s,X' % (param_position[1],))
            self.fetch_operand(proc_namespace,tokens[2],1)
            proc_namespace['code'].append('sta PARAMS-%s,X' % (param_position[1],))
            self.checkin_reg(proc_namespace, the_item)
         else:
            the_item = self.fetch_operand(proc_namespace,tokens[2])
            self.checkin_reg(proc_namespace, the_item)
            proc_namespace['code'].append('sta PARAMS-%s,X' % (param_position[1],))
      elif(tokens[0] == 'add'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_adc8(proc_namespace, tokens[1], tokens[2], tokens[3])
         else:
            self.instr_adc16(proc_namespace, tokens[1], tokens[2], tokens[3])
      elif(tokens[0] == 'sub'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_sbc8(proc_namespace, tokens[1], tokens[2], tokens[3])
         else:
            self.instr_sbc16(proc_namespace, tokens[1], tokens[2], tokens[3])
      elif(tokens[0] == 'shl'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_shl8(proc_namespace, tokens[1], tokens[2], tokens[3])
         else:
            self.instr_shl16(proc_namespace, tokens[1], tokens[2], tokens[3])
      elif(tokens[0] == 'shr'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_shr8(proc_namespace, tokens[1], tokens[2], tokens[3])
         else:
            self.instr_shr16(proc_namespace, tokens[1], tokens[2], tokens[3])
      elif(tokens[0] == 'branchneq'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_cmp8(proc_namespace, tokens[1], tokens[2], tokens[3], "bne")           
         else:
            self.instr_cmp16(proc_namespace, tokens[1], tokens[2], tokens[3], "bne")           
      elif(tokens[0] == 'brancheq'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_cmp8(proc_namespace, tokens[1], tokens[2], tokens[3], "beq")           
         else:
            self.instr_cmp16(proc_namespace, tokens[1], tokens[2], tokens[3], "beq")           
      elif(tokens[0] == 'branchlte'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_cmp8(proc_namespace, tokens[1], tokens[2], tokens[3], "bmi")           
         else:
            self.instr_cmp16(proc_namespace, tokens[1], tokens[2], tokens[3], "bmi")           
      elif(tokens[0] == 'branchgte'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_cmp8(proc_namespace, tokens[1], tokens[2], tokens[3], "bpl")           
         else:
            self.instr_cmp16(proc_namespace, tokens[1], tokens[2], tokens[3], "bpl")           
      elif(tokens[0] == 'branchgt'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_cmp8(proc_namespace, tokens[1], tokens[2], tokens[3], "bpl")           
         else:
            self.instr_cmp16(proc_namespace, tokens[1], tokens[2], tokens[3], "bpl")           
      elif(tokens[0] == 'branchlt'):
         if(self.parse_item(tokens[1])[2] == 'u8'):
            self.instr_cmp8(proc_namespace, tokens[1], tokens[2], tokens[3], "bmi")           
         else:
            self.instr_cmp16(proc_namespace, tokens[1], tokens[2], tokens[3], "bmi")           
      elif(tokens[0] == 'branch'):
         proc_namespace['code'].append('jmp @%s' % (tokens[1],))
         #op_info = self.fetch_imm_operand(proc_namespace,tokens[2])
         #self.fetch_operand(proc_namespace,tokens[1])
         #if(self.parse_item(tokens[1])[2] == 'u8'):
         #   proc_namespace['code'].append('cmp %s' % (op_info,))
         #else:
         #   proc_namespace['code'].append('cmpc %s' % (op_info,)) 
         #proc_namespace['code'].append('bmi @%s' % (tokens[3],))
      elif(tokens[0] == 'trash'):
         self.checkin_reg(proc_namespace,tokens[1])
      elif(tokens[0] == 'mult'):
         #op_info = self.fetch_imm_operand(proc_namespace,tokens[3])
         #self.fetch_operand(proc_namespace,tokens[2])
         self.push_item(proc_namespace,tokens[3]) 
         self.push_item(proc_namespace,tokens[2]) 
         proc_namespace['code'].append('call _stdlib_mult')
         self.store_result(proc_namespace,tokens[1])
      elif(tokens[0] == 'cmp'):
         pass
      elif(tokens[0] == 'increment'):
         item_info = self.parse_item(tokens[1])
         #print "Store accumulator: ", item_info
         if item_info[0] == '~':
            proc_namespace['code'].append('inc @%s,X' % (self.checkout_reg(proc_namespace,item_info[1]),))
         elif item_info[0] in ('*','&'):
            proc_namespace['code'].append('inc @%s,X' % (item_info[1],))
         else:
            self.errormsg()
      elif(tokens[0] == 'return'):
         self.fetch_operand(proc_namespace,tokens[1]) 
         proc_namespace['code'].append('jmp @proc_end')
      elif(tokens[0] == 'call'):
         proc_namespace['code'].append('call %s' % (tokens[1],))
      elif(tokens[0] == 'result'):
         self.store_result(proc_namespace,tokens[1])
      elif(tokens[0] == 'pop'):
         self.store_result(proc_namespace,tokens[1]) 
      elif(tokens[0] == 'push'):
         self.push_item(proc_namespace,tokens[1]) 
      elif(tokens[0] == 'loadglobaladdr'):
         dest_info = self.parse_item(tokens[2])
         if dest_info[0] == '$':
            proc_namespace['code'].append('ldc #%s' % (dest_info[1],))
         self.store_result(proc_namespace,tokens[1])
      elif(tokens[0] == 'storemem8'):
         #dest_info = self.parse_item(tokens[1])
         reference_parts = tokens[1].split('@')
         if(len(reference_parts) == 2):
            store_code = self.handle_indexing(proc_namespace,'sta',reference_parts[0],reference_parts[1])
            self.fetch_operand(proc_namespace,tokens[2]) 
            proc_namespace['code'].append(store_code)
            self.checkin_reg(proc_namespace, "TEMPADDR")
         else:
            pass
      elif(tokens[0] == 'storemem16'):
         reference_parts = tokens[1].split('@')
         if(len(reference_parts) == 2):
            store_code = self.handle_indexing(proc_namespace,'sta',reference_parts[0],reference_parts[1])
            self.fetch_operand(proc_namespace,tokens[2]) 
            proc_namespace['code'].append(store_code)
            store_code = self.handle_indexing(proc_namespace,'sta',reference_parts[0],reference_parts[1],1)
            self.fetch_operand(proc_namespace,tokens[2],1) 
            proc_namespace['code'].append(store_code)
            self.checkin_reg(proc_namespace, "TEMPADDR")
         else:
            pass
      elif(tokens[0] == 'readmem8'):
         reference_parts = tokens[2].split('@')
         if(len(reference_parts) == 2):
            proc_namespace['code'].append(self.handle_indexing(proc_namespace,'lda',reference_parts[0],reference_parts[1]))
            self.store_result(proc_namespace,tokens[1])
            self.checkin_reg(proc_namespace, "TEMPADDR")
         else:
            pass
      elif(tokens[0] == 'readmem16'):
         reference_parts = tokens[2].split('@')
         if(len(reference_parts) == 2):
            proc_namespace['code'].append(self.handle_indexing(proc_namespace,'lda',reference_parts[0],reference_parts[1]))
            self.store_result(proc_namespace,tokens[1])
            proc_namespace['code'].append(self.handle_indexing(proc_namespace,'lda',reference_parts[0],reference_parts[1],1))
            self.store_result(proc_namespace,tokens[1],1)
            self.checkin_reg(proc_namespace, "TEMPADDR")
         else:
            pass
      else:
         pass

   #def fetch_to_operand(self, proc_namespace, item):
   #   item_info = self.parse_item(item)
   #   #print "Fetch to operand: ", item_info
   #   if item_info[0] == '~':
   #      return self.checkin_reg(proc_namespace,item_info[1])     #item_info[1]
   #   elif item_info[0] == '#':
   #      return '#%s' % (item_info[1],)
   #   else:
   #      return '!'


   def fetch_imm_operand(self, proc_namespace, item, offset = 0, placeholder = "NONE"):
      item_info = self.parse_item(item)
      #print "Fetch to accumulator: ", item_info
      offset_text = '' if offset == 0 else "+%d" % (offset,)
      if item_info[0] == '~':
         the_reg = self.get_temp_reg(proc_namespace,item_info[1])     #item_info[1]
         return {'placeholder': item_info[1], 'reference': "@%s%s,X" % (the_reg, offset_text)}
         #proc_namespace['code'].append('lda %s' % (self.checkin_reg(proc_namespace,item_info[1]),))
      elif item_info[0] == '*':
         return {'placeholder': "NONE", 'reference': "@%s%s,X" % (item_info[1], offset_text)}
      elif item_info[0] == '&':
         return {'placeholder': "NONE", 'reference': "@%s%s,X" % (item_info[1], offset_text)}
      elif item_info[0] == '$':
         return {'placeholder': "NONE", 'reference': "%s%s" % (item_info[1], offset_text)}
      elif item_info[0] == '#':
         value = str((int(item_info[1]) >> (8*offset)) & 0xFF)
         return {'placeholder': "NONE", 'reference': "#%s" % (value,)}
      else:
         return {'placeholder': "NONE", 'reference': "ERROR"}

   def fetch_operand(self, proc_namespace, item, offset = 0, placeholder = "NONE"):
      item_info = self.parse_item(item)
      print("Fetch to accumulator: ", item_info)
      offset_text = '' if offset == 0 else "+%d" % (offset,)
      if item_info[0] == '~':
         proc_namespace['code'].append('lda @%s%s,X' % (self.get_temp_reg(proc_namespace,item_info[1]), offset_text))
         return item_info[1]
      elif item_info[0] == '*':
         proc_namespace['code'].append('lda @%s%s,X' % (item_info[1], offset_text))
         return "NONE"
      elif item_info[0] == '&':
         proc_namespace['code'].append('lda @%s%s,X' % (item_info[1], offset_text))
         return "NONE"
      elif item_info[0] == '$':
         proc_namespace['code'].append('lda %s%s' % (item_info[1], offset_text))
         return "NONE"
         #if item_info[2] == 'u8':
         #   proc_namespace['code'].append('%s %s' % (instr_code, item_info[1],))
         #else:
         #   proc_namespace['code'].append('lda %s+1' % (item_info[1],))
         #   proc_namespace['code'].append('xba')
         #   proc_namespace['code'].append('lda %s' % (item_info[1],)) 
      elif item_info[0] == '#':
         try:
            value = str((int(item_info[1]) >> (8*offset)) & 0xFF)
         except ValueError:
            if offset == 0:
               value = "<" + item_info[1]
            elif offset == 1:
               value = ">" + item_info[1]
            else:
               value = item_info[1]
         proc_namespace['code'].append('lda #%s' % (value,))
         return "NONE"
      else:
         return "NONE"

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

   def store_result(self, proc_namespace, item, offset = 0):
      item_info = self.parse_item(item)
      #print "Store accumulator: ", item_info
      offset_text = '' if offset == 0 else "+%d" % (offset,)
      #if item_info[2] == 'u8':
      if item_info[0] == '~':
         the_reg = self.checkout_reg(proc_namespace, item_info[1]) 
         proc_namespace['code'].append('sta @%s%s,X' % (the_reg, offset_text))
         #proc_namespace['code'].append('sta @%s' % (item_info[1],))
         #self.data_stack.append(item_info[1]) 
      elif item_info[0] == '*':
         proc_namespace['code'].append('sta @%s%s,X' % (item_info[1], offset_text))
      elif item_info[0] == '&':
         proc_namespace['code'].append('sta @%s%s,X' % (item_info[1], offset_text))
      elif item_info[0] == '$':
         proc_namespace['code'].append('sta %s%s' % (item_info[1], offset_text))
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


   def parse_item(self, item):
      split_item = item.split(':') 
      return [split_item[0][0], split_item[0][1:], split_item[1]]
      #if item.find('@') >= 0:
      #   index_split = item.split('@')
      #   split_item = index_split[0].split(':') 
      #   return [split_item[0][0], split_item[0][1:], split_item[1], index_split[1]]
      #else: 
      #   split_item = item.split(':') 
      #   return [split_item[0][0], split_item[0][1:], split_item[1]]

   def output_asm(self, outfile_handle):
      outfile_handle.write("start_program:\n")
      outfile_handle.write("\tcall %s\n" % (self.settings['start_proc'],))
      outfile_handle.write("\tjmp start_program\n")

      for proc_name in list(self.procedures.keys()):
         outfile_handle.write("\n\n%s:\n" % (proc_name,))
         for code_line in self.procedures[proc_name]['code']:
            print(" > ", code_line)
            if code_line.endswith(":"):
               outfile_handle.write("%s\n" % (code_line,))
            else:
               outfile_handle.write("\t%s\n" % (code_line,))
         outfile_handle.write("@proc_end:\n")
         outfile_handle.write("\trts\n")
         

   def output_internals(self, outfile_handle):
      outfile_handle.write("Globals\n")
      pprint.pprint(self.global_list, stream = outfile_handle)
      outfile_handle.write("Settings\n")
      pprint.pprint(self.settings, stream = outfile_handle)
      outfile_handle.write("Procedures\n")
      pprint.pprint(self.procedures, stream = outfile_handle)


def main_program():
   argparse = optparse.OptionParser(description="Absurd Systems ASIL Code Generator to AS1602 Native Code",
                                    usage="usage: codegen_as1602.py [options] src-file",
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


