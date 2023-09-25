
def to_sv_hex(value:int)->str:
    sv_int = int(str(value), 16) 
    return f"'h{sv_int:x}"

def sv_hex_to_py_int(value:str)->int:
    return value.split['h'][1]

class Field:
    def __init__(self, name: str, field_access: str, reset_value: int, bitpos_end: int,
                 bitpos_start: int, function: str = None):
        self.name = name
        self.field_access = field_access
        self.reset_value = to_sv_hex(reset_value)
        self.bitpos_end = int(bitpos_end)
        self.bitpos_start = int(bitpos_start)
        self.function = function
        self.bits_width = self.bitpos_end - self.bitpos_start + 1

    def __str__(self) -> str:
        s = f"{self.name}: {self.field_access}: {self.reset_value}: {self.bits_width}"
        if not pd.isna(self.function):
            s += f": {function}"
        return s


class Memory:
    def __init__(self, name: str, size: int, n_bits: int, offset: int):
        self.name = name
        self.size = to_sv_hex(size)
        self.n_bits = n_bits
        self.offset = to_sv_hex(offset)

    def __str__(self) -> str:
        s = f"{self.name}: {to_sv_hex(sv_hex_to_py_int(self.offset)+sv_hex_to_py_int(self.size))}: {self.n_bits}"
        return s


class Register:
    def __init__(self, name: str, address: int, reg_access: str):
        self.name = name
        self.address = to_sv_hex(address)
        self.reg_access = reg_access
        self.fields = []
        self.__fields_declare__ = []
        self.__fields_create__ = []
        self.__fields_config__ = []
        self.__fields_coverpoint__ = []

    def __str__(self) -> str:
        s = f"{self.name}: {self.address}"
        if self.fields:
            s += '\n' + '\n'.join(str(f) for f in self.fields)
        return s

    def add_field(self, field: Field):
        self.fields.append(field)
        self.__fields_declare__.append(
            f'\n\t\trand uvm_reg_field {field.name};')
        self.__fields_coverpoint__.append(
            f'\n\t\t\t{field.name}: coverpoint {field.name}.value[{field.bitpos_end}:{field.bitpos_start}];')
        self.__fields_create__.append(
            f'\n\t\t\t{field.name} = uvm_reg_field::type_id::create("{field.name}");')
        '''
        function void configure(
 uvm_reg parent,
 int unsigned size,
 int unsigned lsb_pos,
 string access,
 bit volatile,
 uvm_reg_data_t reset,
 bit has_reset,
 bit is_rand,
 bit individually_accessible
)
        '''
        self.__fields_config__.append(
            f'\n\t\t\t{field.name}.configure(this, {field.bits_width}, {field.bitpos_start}, "{field.field_access.upper()}", 0, {field.reset_value}, 1, 0, 0);')

    def print_register_in_sv(self) -> list:
        lines = []
        lines.append(f'\n\tclass {self.name}_reg extends uvm_reg;')
        lines.append('\n')
        lines.append(f'\n\t\t`uvm_object_utils({self.name}_reg)')
        lines.append('\n')
        lines.extend(self.__fields_declare__)
        lines.append('\n')
        lines.append(f'\n\t\tcovergroup value_cg;')
        lines.append(f'\n\t\t\toption.per_instance = 1;')
        lines.extend(self.__fields_coverpoint__)
        lines.append('\n\t\tendgroup')
        lines.append('\n')
        lines.append(f'\n\t\tfunction new(string name = "{self.name}_reg");')
        lines.append('\n\t\t\tsuper.new(name, 32, UVM_CVR_ALL);')
        lines.append('\n\t\t\tvoid\'(set_coverage(UVM_CVR_FIELD_VALS));')
        lines.append('\n\t\t\tif(has_coverage(UVM_CVR_FIELD_VALS)) begin')
        lines.append('\n\t\t\t\tvalue_cg = new();')
        lines.append('\n\t\t\tend')
        lines.append('\n\t\tendfunction')
        lines.append('\n')
        lines.append('\n\t\tvirtual function void build();')
        lines.extend(self.__fields_create__)
        lines.extend(self.__fields_config__)
        lines.append('\n\t\tendfunction')
        lines.append('\n')
        lines.append(
            '\n\t\tfunction void sample(uvm_reg_data_t data, uvm_reg_data_t byte_en, bit is_read, uvm_reg_map map);')
        lines.append('\n\t\t\tsuper.sample(data, byte_en, is_read, map);')
        lines.append('\n\t\t\tsample_values();')
        lines.append('\n\t\tendfunction')
        lines.append('\n')
        lines.append('\n\t\tfunction void sample_values();')
        lines.append('\n\t\t\tsuper.sample_values();')
        lines.append('\n\t\t\tif (get_coverage(UVM_CVR_FIELD_VALS)) begin')
        lines.append('\n\t\t\t\tvalue_cg.sample();')
        lines.append('\n\t\t\tend')
        lines.append('\n\t\tendfunction')
        lines.append('\n')
        lines.append('\n\tendclass\n')
        return lines


class Block:
    def __init__(self, name: str, offset: int):
        self.name = name
        self.offset = to_sv_hex(offset)

        self.registers = []
        self.sub_blocks = []
        self.memorys = []

        self.__registers_declare__ = []
        self.__registers_create__ = []
        self.__registers_config__ = []
        self.__registers_build__ = []
        self.__registers_add_map__ = []
        self.__registers_add_hdl_path__ = []
        self.__registers_exclude_self_test__ = []

        self.__sub_blocks_declare__ = []
        self.__sub_blocks_create__ = []
        self.__sub_blocks_config__ = []
        self.__sub_blocks_build__ = []
        self.__sub_blocks_add_map__ = []
        self.__sub_blocks_lock__ = []

        self.__memorys_declare__ = []
        self.__memorys_create__ = []
        self.__memorys_config__ = []
        self.__memorys_build__ = []
        self.__memorys_add_map__ = []
        self.__memorys_add_hdl_path__ = []

    def __str__(self):
        sub_blocks_str = '\n'.join(
            str(b) for b in self.sub_blocks) if self.sub_blocks else ''
        registers_str = '\n'.join(str(r)
                                  for r in self.registers) if self.registers else ''
        memorys_str = '\n'.join(str(m)
                                for m in self.memorys) if self.memorys else ''
        return f"{self.name}: {self.offset}\n{sub_blocks_str}\n{registers_str}\n{memorys_str}"

    def add_register(self, register: Register):
        self.registers.append(register)

        # generate code for __registers_declare__
        self.__registers_declare__ = [
            f'\n\t\trand {register.name}_reg {register.name};'
            for register in self.registers]

        # generate code for __registers_create__
        self.__registers_create__ = [
            f'\n\t\t\t{register.name} = {register.name}_reg::type_id::create("{register.name}");'
            for register in self.registers]

        # generate code for __registers_config__
        self.__registers_config__ = [
            f'\n\t\t\t{register.name}.configure(this);'
            for register in self.registers]

        # generate code for __registers_build__
        self.__registers_build__ = [
            f'\n\t\t\t{register.name}.build();'
            for register in self.registers]

        # generate code for __registers_add_map__
        self.__registers_add_map__ = [
            f'\n\t\t\tmap.add_reg({register.name}, {register.address}, "{register.reg_access.upper()}");'
            for register in self.registers]

        # generate code for __registers_exclude_self_test__
        self.__registers_exclude_self_test__ = [
            f'\n\t\t\tuvm_resource_db#(bit)::set({{"REG::", {register.name}.get_full_name()}}, "{no_name}", 1, this);'
            for no_name in ('NO_REG_BIT_BASH_TEST', 'NO_REG_ACCESS_TEST')
            for register in self.registers
            if register.reg_access == 'ro']

        # generate code for __registers_add_hdl_path__
        self.__registers_add_hdl_path__ = [
            f'\n\t\t\t// {register.name}.add_hdl_path_slice("{field.name}", {field.bitpos_start}, {field.bits_width});'
            for register in self.registers
            for field in register.fields
            if 'reserve' not in field.name]

        # generate code for __registers_exclude_self_test__
        self.__registers_exclude_self_test__.extend([
            f'\n\t\t\tuvm_resource_db#(bit)::set({{"REG::", {register.name}.{field.name}.get_full_name()}}, "{no_name}", 1, this);'
            for no_name in ('_NO_REG_BIT_BASH_TEST', '_NO_REG_ACCESS_TEST')
            for register in self.registers
            for field in register.fields
            if 'reserve' in field.name and register.reg_access != 'ro'])

    def add_sub_block(self, sub_block: 'Block'):
        self.sub_blocks.append(sub_block)
        self.__sub_blocks_declare__ = [
            f'\n\t\trand {sub_block.name}_rgm {sub_block.name};'
            for sub_block in self.sub_blocks]

        self.__sub_blocks_create__ = [
            f'\n\t\t\t{sub_block.name} = {sub_block.name}_rgm::type_id::create("{sub_block.name}");'
            for sub_block in self.sub_blocks]

        self.__sub_blocks_config__ = [
            f'\n\t\t\t{sub_block.name}.configure(this/*, hdl_path*/);'
            for sub_block in self.sub_blocks]

        self.__sub_blocks_build__ = [
            f'\n\t\t\t{sub_block.name}.build();'
            for sub_block in self.sub_blocks]

        self.__sub_blocks_add_map__ = [
            f'\n\t\t\tmap.add_submap({sub_block.name}.map, {sub_block.offset});'
            for sub_block in self.sub_blocks]

        self.__sub_blocks_lock__ = [
            f'\n\t\t\t{sub_block.name}.lock_model();'
            for sub_block in self.sub_blocks]

    def add_memory(self, memory: Memory):
        self.memorys.append(memory)
        self.__memorys_declare__ = [
            f'\n\t\trand uvm_mem {memory.name};'
            for memory in self.memorys]
        self.__memorys_create__ = [
            f'\n\t\t\t{memory.name} = new("{memory.name}", {memory.offset}, {memory.n_bits});'
            for memory in self.memorys]
        self.__memorys_config__ = [
            f'\n\t\t\t{memory.name}.configure(this);'
            for memory in self.memorys]
        self.__memorys_add_hdl_path__ = [
            f'\n\t\t\t{memory.name}.add_hdl_path_slice("{memory.name}", {memory.offset}, {memory.size});'
            for memory in self.memorys]
        self.__memorys_add_map__ = [
            f'\n\t\t\tmap.add_mem({memory.name}, {memory.offset});'
            for memory in self.memorys]

    def print_block_in_sv(self) -> list:
        lines = []
        lines.extend([f'\n\tclass {self.name}_rgm extends uvm_reg_block;'
                      f'\n\t\t`uvm_object_utils({self.name}_rgm)',
                      *self.__registers_declare__,
                      *self.__memorys_declare__,
                      *self.__sub_blocks_declare__,
                      '\n\t\tuvm_reg_map map;'
                      f'\n\t\tfunction new(string name="{self.name}_rgm");'
                      '\n\t\t\tsuper.new(name, UVM_NO_COVERAGE);'
                      '\n\t\tendfunction'
                      '\n\t\tvirtual function void build();',
                      '\n\t\t\tmap = create_map("map", \'h0, 4, UVM_LITTLE_ENDIAN);',
                      *self.__registers_create__,
                      *self.__registers_config__,
                      *self.__registers_build__,
                      *self.__registers_add_map__,
                      *self.__memorys_create__,
                      *self.__memorys_config__,
                      *self.__memorys_add_hdl_path__,
                      *self.__memorys_add_map__,
                      *self.__sub_blocks_create__,
                      *self.__sub_blocks_config__,
                      *self.__sub_blocks_build__,
                      *self.__sub_blocks_lock__,
                      *self.__sub_blocks_add_map__])
        if self.registers:
            lines.extend(['\n\t\t\t// TODO: add hdl path to access registers backdoor',
                          *self.__registers_add_hdl_path__])
            if self.__registers_exclude_self_test__:
                lines.append('\n\t\t\texclude_rg_fd_st();')
        lines.append('\n\t\tendfunction')
        if self.registers and self.__registers_exclude_self_test__:
            lines.extend(['\n\t\tvirtual function void exclude_rg_fd_st();',
                          *self.__registers_exclude_self_test__,
                          '\n\t\tendfunction'])
        lines.append('\n\tendclass')
        return lines

    def print_block_file(self) -> list:
        lines = [
            f'\n`ifndef __{self.name.upper()}_RGM_PKG_SV__',
            f'\n`define __{self.name.upper()}_RGM_PKG_SV__',
            f'\npackage {self.name}_rgm_pkg;',
            '\n\timport uvm_pkg::*;',
            '\n\t`include "uvm_macros.svh"'
        ]
        for sub_block in self.sub_blocks:
            lines.append(f'\n\timport {sub_block.name}_rgm_pkg::*;')
        for rg in self.registers:
            lines.extend(rg.print_register_in_sv())
        lines.extend(self.print_block_in_sv())
        lines.extend(['\nendpackage', '`endif'])
        with open(f'{self.name}_rgm_pkg.sv', 'w') as f:
            f.writelines(lines)
        return lines

    def print_file_list(self) -> list:
        lines = []
        if self.sub_blocks:
            for sb in self.sub_blocks:
                lines.extend(sb.print_file_list())
        lines.append(f'{self.name}_rgm_pkg.sv\n')
        return lines

import pandas as pd

class BlockProcessor:
    def __init__(self, top_name:str, excel_name:str, exception_sheets = []):
        self.top_name = top_name
        self.excel_name = excel_name
        self.exception_sheets = [top_name] + exception_sheets
        self.workbook = pd.read_excel(excel_name, sheet_name=None)
        self.workbook[top_name].set_index('peripheral', inplace=True)
        self.reg_blocks = {}

    def process_reg_table(self, reg_table, reg_block):
        regs = {}
        cur_reg_name = ''

        for reg_name, address, reg_access, field_name, field_access, reset_value, bitpos_end, bitpos_start, function in reg_table.values:
            is_mem = not pd.isna(reg_name) and 'mem' in reg_name

            if is_mem:
                mem = Memory(reg_name, 0x40, 32, address.split('~')[0])
                reg_block.add_memory(mem)

            elif not pd.isna(reg_name):
                cur_reg_name = reg_name.lower()
                regs.setdefault(cur_reg_name, Register(cur_reg_name, address, reg_access))

            if not is_mem and not pd.isna(field_name):
                field = Field(field_name, field_access, reset_value, bitpos_end, bitpos_start)
                regs[cur_reg_name].add_field(field)

        for rg in regs.values():
            reg_block.add_register(rg)

    def process_peripheral(self, peripheral, reg_table, parent_block_name):
        header_row = reg_table.iloc[0]
        offset = self.workbook[parent_block_name].at[peripheral, 'offset']
        reg_block = Block(f"{peripheral}", offset)
        print(parent_block_name, "add sub_block", peripheral)

        if 'peripheral' in header_row and 'offset' in header_row:
            print(peripheral, "has sub_sub_block")
            reg_table.set_index('peripheral', inplace=True)
            for sub_block_name, sub_block_row in reg_table.iterrows():
                sub_block = self.process_peripheral(sub_block_name, self.workbook[sub_block_name], peripheral) # Recursively handle sub-blocks
                reg_block.add_sub_block(sub_block)
        else:
            print(peripheral, "is bottom block")
            self.process_reg_table(reg_table, reg_block)

        print("writing", reg_block.name, "model msg to file")
        reg_block.print_block_file()

        return reg_block

    def process_top_block(self):
        top_block = Block(self.top_name, 0)
        for peripheral, offset in self.workbook[self.top_name].iterrows():
            if peripheral not in self.exception_sheets:
                try:
                    self.reg_blocks[peripheral] = self.process_peripheral(peripheral, self.workbook[peripheral], self.top_name)
                    top_block.add_sub_block(self.reg_blocks[peripheral])
                except KeyError:
                    print("Can't find", peripheral, "sheet in", self.excel_name)
        top_block.print_block_file()
        # print rgms filelist
        with open(f'{top_block.name}_rgm_filelist.f', 'w') as f:
            f.writelines(top_block.print_file_list())

excel_name = 'test_regs.xlsx'
top_name = 'pulpino'
debug = False
exception_sheets = ['soc_ctrl_00']

import sys
import os
if debug:
    sys.stdout = sys.__stdout__
else:
    sys.stdout = open(os.devnull, 'w')
    
processor = BlockProcessor(top_name, excel_name, exception_sheets)
processor.process_top_block()