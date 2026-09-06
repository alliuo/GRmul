import os
import shutil
import itertools
import re
import numpy as np
from eda_tools import openroad_command, run_checked, run_logged, tool_path


def pp_ref(pp):
    name = pp.name.replace('*', '_')
    return f'~{name}' if pp.node_type == 2 else name


def code_full_adder(output_dir, fa_name, uncared_inputs):
    code = f"""
module {fa_name} (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire cout,
    output wire sum
);
    reg [1:0] tmp;

    always @ *
    case ({{a, b, cin}})
"""
    for input in range(2**3):
        input_tuple = tuple(map(int, f"{input:03b}")) # 5 -> (1, 0, 1), 3 -> (0, 1, 1)
        if input_tuple in uncared_inputs:
            code += f"        3'b{bin(input)[2:].zfill(3)} : tmp = 2'bx;\n"
        else:
            output = input%2 + input//2%2 + input//4
            code += f"        3'b{bin(input)[2:].zfill(3)} : tmp = 2'b{bin(output)[2:].zfill(2)};\n"
    code += """     endcase
    
    assign cout = tmp[1];
    assign sum = tmp[0];
endmodule
"""
    out_path = os.path.join(output_dir, f'{fa_name}.v')
    with open(out_path, 'w') as f:
        f.write(code)


def code_half_adder(output_dir, ha_name, uncared_inputs):
    code = f"""
module {ha_name} (
    input  wire a,
    input  wire b,
    output wire cout,
    output wire sum
);
    reg [1:0] tmp;

    always @ *
    case ({{a, b}})
"""
    for input in range(2**2):
        input_tuple = tuple(map(int, f"{input:02b}")) # 3 -> (1, 1)
        if input_tuple in uncared_inputs:
            code += f"        2'b{bin(input)[2:].zfill(2)} : tmp = 2'bx;\n"
        else:
            output = input%2 + input//2%2 + input//4
            code += f"        2'b{bin(input)[2:].zfill(2)} : tmp = 2'b{bin(output)[2:].zfill(2)};\n"
    code += """     endcase
    
    assign cout = tmp[1];
    assign sum = tmp[0];
endmodule
"""
    out_path = os.path.join(output_dir, f'{ha_name}.v')
    with open(out_path, 'w') as f:
        f.write(code)


def code_mul(output_dir, bw0, bw1, encoding, pp_dict, fa_dict, ha_dict):
    mul_name = f"mul{bw0}x{bw1}_RL"
    adder_name_list = []
    code = f"""module {mul_name} (
    input  wire [{bw0-1}:0]  a,
    input  wire [{bw1-1}:0]  b,
    output wire [{bw0+bw1-1}:0] product
);
"""
    # Generate partial products.
    if encoding == 'b2':
        # Radix-2 Booth encoding.
        code += f"    wire [{bw1-1}:0] one, neg;\n"
        code += f"    assign one[0] = 1'b0;\n"
        code += f"    assign neg[0] = b[0];\n"
        for i in range(1, bw1):
            code += f"    assign one[{i}] = ~b[{i}] & b[{i-1}];\n"
            code += f"    assign neg[{i}] = b[{i}] & ~b[{i-1}];\n"
        code += "    \n"
        for i in range(bw1):
            code += f"    wire [{bw0-1}:0] booth{i};\n"
            code += f"    assign booth{i} = ({{{bw0}{{one[{i}]}}}} & a) | ({{{bw0}{{neg[{i}]}}}} & ~a);\n"
        code += "    \n"
    
    elif encoding == 'b4':
        # Radix-4 Booth encoding.
        code += f"    wire [{bw1//2-1}:0] one, two, neg;\n"
        code += f"    assign one[0] = b[0];\n"
        code += f"    assign two[0] = b[1] & ~b[0];\n"
        code += f"    assign neg[0] = b[1];\n"
        for i in range(2, bw1, 2):
            code += f"    assign one[{i//2}] = b[{i}] ^ b[{i-1}];\n"
            code += f"    assign two[{i//2}] = (~b[{i+1}] & b[{i}] & b[{i-1}]) | (b[{i+1}] & ~b[{i}] & ~b[{i-1}]);\n"
            code += f"    assign neg[{i//2}] = b[{i+1}] & ~(b[{i}] & b[{i-1}]);\n"
        code += "    \n"
        code += f"    wire [{bw0}:0] ext_a, a2;\n"
        code += f"    assign ext_a = {{a[{bw0-1}], a}};\n"
        code += f"    assign a2 = {{a, 1'b0}};\n"
        code += "    \n"
        for i in range(bw1//2):
            code += f"    wire [{bw0}:0] booth{i};\n"        
            code += f"    assign booth{i} = (({{{bw0+1}{{one[{i}]}}}} & ext_a) | ({{{bw0+1}{{two[{i}]}}}} & a2)) ^ {{{bw0+1}{{neg[{i}]}}}};\n"
        code += "    \n"

    elif encoding == 'b4u':
        # Unsigned Radix-4 Booth encoding.
        code += f"    wire [{bw1//2-1}:0] one, two, neg;\n"
        code += f"    assign one[0] = b[0];\n"
        code += f"    assign two[0] = b[1] & ~b[0];\n"
        code += f"    assign neg[0] = b[1];\n"
        for i in range(2, bw1, 2):
            code += f"    assign one[{i//2}] = b[{i}] ^ b[{i-1}];\n"
            code += f"    assign two[{i//2}] = (~b[{i+1}] & b[{i}] & b[{i-1}]) | (b[{i+1}] & ~b[{i}] & ~b[{i-1}]);\n"
            code += f"    assign neg[{i//2}] = b[{i+1}] & ~(b[{i}] & b[{i-1}]);\n"
        code += "    \n"
        code += f"    wire [{bw0}:0] ext_a, a2;\n"
        code += f"    assign ext_a = {{1'b0, a}};\n"
        code += f"    assign a2 = {{a, 1'b0}};\n"
        code += "    \n"
        for i in range(bw1//2):
            code += f"    wire [{bw0}:0] booth{i};\n"        
            code += f"    assign booth{i} = (({{{bw0+1}{{one[{i}]}}}} & ext_a) | ({{{bw0+1}{{two[{i}]}}}} & a2)) ^ {{{bw0+1}{{neg[{i}]}}}};\n"
        code += f"    wire [{bw0-1}:0] booth{bw1//2};\n"        
        code += f"    assign booth{bw1//2} = ({{{bw0}{{b[{bw1-1}]}}}} & a);\n"
        code += "    \n"
        code += f"    wire [{bw1//2-1}:0] sign_ext;\n"
        code += f"    assign sign_ext = neg;\n"
        code += "    \n"

    else:
        for i in range(0, bw0):
            for j in range(0, bw1):
                code += f"    wire a{i}_b{j};\n"
                code += f"    assign a{i}_b{j} = a[{i}] & b[{j}];\n"
        code += "    \n"
     
    # Declare PPs and find CPA start points from exact-adder sum outputs.
    candidate_start_pp = []
    for pp in pp_dict.values():
        if pp.name.startswith('encode'):
            continue
        if pp.node_type==0 and len(pp.parents)in [2, 3]:
            if len(pp.parents) == 2:
                tmp_adder = ha_dict[pp.graph_idx]
                if tmp_adder.type=='half_adder' and not tmp_adder.name.startswith('encoder'):
                    candidate_start_pp.append(pp)
            else:
                tmp_adder = fa_dict[pp.graph_idx]
                if tmp_adder.type=='full_adder_acc' and not tmp_adder.name.startswith('encoder'):
                    candidate_start_pp.append(pp)
        at_first_level = pp.name.startswith('a') or pp.name.startswith('booth') or pp.name.startswith('neg') or pp.name.startswith('sign_ext')
        at_last_level = (pp.children == []) # Multiplier output.
        if pp.name.startswith('constant1'):
            code += f"    wire {pp.name};\n"
            code += f"    assign {pp.name} = 1'b1;\n"
        elif at_first_level and at_last_level: 
            # The initial PP is directly connected to the multiplier output.
            code += f"    assign product[{pp.weight}] = {pp_ref(pp)};\n"
        elif (not at_first_level) and (not at_last_level):
            # Declare the intermediate PP.
            code += f"    wire {pp.name};\n"
    code += "    \n"

    used_adder = []
    if bw0+bw1 > 8:
    # Implement the longest exact carry chain using '+'.
        max_length = 0
        for start_pp in candidate_start_pp:
            if len(start_pp.parents) == 2:
                current_adder = ha_dict[start_pp.graph_idx]
                tmp_cin = None
            else: # Full adder.
                current_adder = fa_dict[start_pp.graph_idx]
                tmp_cin = pp_ref(start_pp.parents[2])
            tmp_adders = [current_adder.name]
            tmp_input0 = [pp_ref(start_pp.parents[0])]
            tmp_input1 = [pp_ref(start_pp.parents[1])]
            sum_name = current_adder.sum.name if current_adder.sum.children != [] else f"product[{current_adder.sum.weight}]"
            tmp_output = [sum_name]
            tmp_delete = []
            carry = current_adder.cout
            while (carry is not None) and (not carry.name.startswith('encode')):
                if carry.children == []:
                    tmp_output.append(f"product[{carry.weight}]")
                    break
                for tmp_pp in carry.children:
                    if tmp_pp.node_type == 0:
                        pp = tmp_pp
                current_adder = ha_dict.get(pp.graph_idx)
                is_fa = False
                if current_adder is None:
                    current_adder = fa_dict.get(pp.graph_idx)
                    is_fa = True
                assert current_adder is not None
                if (is_fa and current_adder.type!='full_adder_acc') or (not is_fa and current_adder.type!='half_adder'):
                    tmp_output.append(carry.name)
                    break
                tmp_adders.append(current_adder.name)
                other_inputs = [p for p in pp.parents if p != carry]
                if is_fa:
                    tmp_input0.append(pp_ref(other_inputs[0]))
                    tmp_input1.append(pp_ref(other_inputs[1]))
                else:
                    tmp_input0.append(pp_ref(other_inputs[0]))
                    tmp_input1.append("1'b0")
                sum_name = current_adder.sum.name if current_adder.sum.children != [] else f"product[{current_adder.sum.weight}]"
                tmp_output.append(sum_name)
                tmp_delete.append(carry.name)
                carry = current_adder.cout
            if len(tmp_adders) > max_length:
                used_adder = tmp_adders
                cpa_input0 = tmp_input0
                cpa_input1 = tmp_input1
                cpa_cin    = tmp_cin
                cpa_output = tmp_output
                cpa_delete = tmp_delete
                max_length = len(tmp_adders)
                assert len(tmp_adders) == len(cpa_input0) == len(cpa_input1) == len(cpa_delete)+1
        if max_length > 0:
            # Carry-propagate adder with the longest carry chain.
            delete_line = tuple(f"wire {pp_name};" for pp_name in cpa_delete)
            code = "\n".join(
                line for line in code.splitlines()
                if not line.strip().startswith(delete_line)
            ) # Remove PP declarations that become intermediate CPA carries.
            code += f"\n    wire [{max_length-1}:0] cpa_input0;\n"
            code += f"    wire [{max_length-1}:0] cpa_input1;\n"
            code += f"    assign cpa_input0 = {{{', '.join(reversed(cpa_input0))}}};\n"
            code += f"    assign cpa_input1 = {{{', '.join(reversed(cpa_input1))}}};\n"
            cpa_cin_verilog = f" + {cpa_cin}" if cpa_cin is not None else ""
            if len(cpa_output) == len(cpa_input0): # No cout.
                code += f"    assign {{{', '.join(reversed(cpa_output))}}} = cpa_input0 + cpa_input1" + cpa_cin_verilog + ";\n"
            else:
                code += f"    assign {{{', '.join(reversed(cpa_output))}}} = {{1'b0, cpa_input0}} + {{1'b0, cpa_input1}}" + cpa_cin_verilog + ";\n"
            code += "    \n"
    
    # Full adders
    fa_name_idx = 0
    collected_combs = []
    for fa in fa_dict.values():
        if fa.name.startswith('encoder') or fa.name in used_adder:
            continue
        # Select adder type.
        if fa.type == 'unknown':
            # Reuse an already generated AFA when possible.
            not_in = True
            for p in itertools.permutations((0, 1, 2)):
                transformed_comb = set((comb[p[0]], comb[p[1]], comb[p[2]]) for comb in fa.missing_input_combinations)
                if transformed_comb in collected_combs:
                    not_in = False
                    fa_type = f'AFA_new{collected_combs.index(transformed_comb)}'
                    input_idx = p
                    break
            if not_in:
                # Generate a new AFA if needed.
                fa_type = f'AFA_new{fa_name_idx}'
                fa_name_idx += 1
                adder_name_list.append(fa_type)
                code_full_adder(output_dir, fa_type, fa.missing_input_combinations)
                collected_combs.append(set(fa.missing_input_combinations))
                input_idx = (0, 1, 2)
        else:
            fa_type = fa.type
            input_idx = fa.input_order
        # Input names.
        inputs = [pp_ref(pp) for pp in (fa.input0, fa.input1, fa.input2)]
        # Output names.
        if fa.sum.children != []: # Not a multiplier output.
            sum = fa.sum.name
        else:
            sum = f"product[{fa.sum.weight}]"
        if fa.cout is None:
            cout = ""
        elif fa.cout.children != []: # Not a multiplier output.
            cout = fa.cout.name
        else:
            cout = f"product[{fa.cout.weight}]"
        # Instantiate the adder.
        code += f"    {fa_type} {fa.name} (.a({inputs[input_idx[0]]}), .b({inputs[input_idx[1]]}), .cin({inputs[input_idx[2]]}), .sum({sum}), .cout({cout}));\n"
    code += "    \n"
    if collected_combs != []:
        print('[Unrecorded FA input combinations]', collected_combs)

    # Half adders
    ha_name_idx = 0
    collected_combs = []
    for ha in ha_dict.values():
        if ha.name.startswith('encoder') or ha.name in used_adder:
            continue
        # Select adder type.
        if ha.type == 'unknown':
            # Reuse an already generated AHA when possible.
            not_in = True
            for p in itertools.permutations((0, 1)):
                transformed_comb = set((comb[p[0]], comb[p[1]]) for comb in ha.missing_input_combinations)
                if transformed_comb in collected_combs:
                    not_in = False
                    ha_type = f'AHA_new{collected_combs.index(transformed_comb)}'
                    input_idx = p
                    break
            if not_in:
                # Generate a new AHA if needed.
                ha_type = f'AHA_new{ha_name_idx}'
                ha_name_idx += 1
                adder_name_list.append(ha_type)
                code_half_adder(output_dir, ha_type, ha.missing_input_combinations)
                collected_combs.append(set(ha.missing_input_combinations))
                input_idx = (0, 1)
        else:
            ha_type = ha.type
            input_idx = ha.input_order
        # Input names.
        inputs = [pp_ref(pp) for pp in (ha.input0, ha.input1)]
        # Output names.
        if ha.sum.children != []: # Not a multiplier output.
            sum = ha.sum.name
        else:
            sum = f"product[{ha.sum.weight}]"
        if ha.cout is None:
            cout = ""
        elif ha.cout.children != []: # Not a multiplier output.
            cout = ha.cout.name
        else:
            cout = f"product[{ha.cout.weight}]"
        # Instantiate the adder.
        code += f"    {ha_type} {ha.name} (.a({inputs[input_idx[0]]}), .b({inputs[input_idx[1]]}), .sum({sum}), .cout({cout}));\n"
    code += "endmodule"
    if collected_combs != []:
        print('[Unrecorded HA input combinations]', collected_combs)

    out_path = os.path.join(output_dir, f'{mul_name}.v')
    with open(out_path, 'w') as f:
        f.write(code)
    return mul_name, adder_name_list


def generate_abc_constr(output_dir):
    shutil.copy2(f'{os.path.dirname(__file__)}/config/abc_constr', output_dir)


def generate_yosys_script(output_dir, rtl_path, mul_name, target_delay):
    lib = f'{os.path.dirname(__file__)}/lib/NangateOpenCellLibrary_typical.lib'
    fa_ha_dir = f'{os.path.dirname(__file__)}/env/fa_ha'
    with open(f'{os.path.dirname(__file__)}/config/yosys_template.ys', 'r') as f:
        template = f.read()
    code = template.format(FA_HA_DIR=fa_ha_dir,
                           RTL_PATH=rtl_path,
                           MUL_NAME=mul_name,
                           LIB=lib,
                           DELAY=target_delay)
    out_path = os.path.join(output_dir, 'syn_with_target_delay.ys')
    with open(out_path, 'w') as fout:
        fout.write(code)


def generate_opensta_script(output_dir, mul_name):
    lef = f'{os.path.dirname(__file__)}/lib/NangateOpenCellLibrary.lef'
    lib = f'{os.path.dirname(__file__)}/lib/NangateOpenCellLibrary_typical.lib'
    with open(f'{os.path.dirname(__file__)}/config/opensta_template.tcl', 'r') as f:
        template = f.read()
    code = template.format(LEF=lef,
                           LIB=lib,
                           MUL_NAME=mul_name)
    out_path = os.path.join(output_dir, 'openroad_sta.tcl')
    with open(out_path, 'w') as fout:
        fout.write(code)


def build_syn_env(output_dir, rtl_path, mul_name, target_delay):
    generate_yosys_script(output_dir, rtl_path, mul_name, target_delay)
    generate_abc_constr(output_dir)
    generate_opensta_script(output_dir, mul_name)


def syn_unknown_adder(work_dir, rtl_path, adder_name_list):
    '''
    Synthesize unknown FA and HA cells.
    '''
    if adder_name_list == []:
        return

    adder_name_list = list(dict.fromkeys(adder_name_list))
    syn_rtl_path = os.path.join(work_dir, 'rtl')
    script_path = os.path.join(work_dir, 'script')
    lib = f'{os.path.dirname(__file__)}/lib/NangateOpenCellLibrary_typical.lib'
    os.makedirs(syn_rtl_path, exist_ok=True)
    os.makedirs(script_path, exist_ok=True)

    for adder_name in adder_name_list:
        src_v = os.path.join(syn_rtl_path, f'{adder_name}.v')
        mapped_v = os.path.join(rtl_path, f'{adder_name}_synthesized.v')
        shutil.move(os.path.join(rtl_path, f'{adder_name}.v'), src_v)
        script = f"""
read_verilog {src_v}
synth -top {adder_name}
proc
opt
synth
abc -D 50 -liberty {lib}
opt_clean
write_verilog -noattr {mapped_v}
"""
        ys_file = os.path.join(script_path, f'{adder_name}.ys')
        with open(ys_file, 'w') as f:
            f.write(script)
        run_checked([tool_path('yosys'), ys_file], cwd=work_dir)


def run_synthesis(ys_path):
    run_logged([tool_path('yosys'), './syn_with_target_delay.ys'], cwd=ys_path, log_name='yosys.log')
    run_logged(openroad_command('openroad_sta.tcl'), cwd=ys_path, log_name='openroad.log')


def _extract_braced_block(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise ValueError('Unmatched braces in Liberty file')


def _liberty_cell_model(lib_text, cell_name):
    m = re.search(rf'\n\s*cell\s*\({re.escape(cell_name)}\)\s*\{{', lib_text)
    if m is None:
        raise ValueError(f'Cell {cell_name} not found in Liberty file')
    block = _extract_braced_block(lib_text, m.end()-1)
    inputs, outputs = [], []
    for pin_m in re.finditer(r'\bpin\s*\(([^)]+)\)\s*\{', block):
        pin = pin_m.group(1).strip()
        pin_block = _extract_braced_block(block, pin_m.end()-1)
        direction = re.search(r'\bdirection\s*:\s*(\w+)\s*;', pin_block)
        if direction is None:
            continue
        if direction.group(1) == 'input':
            inputs.append(pin)
        elif direction.group(1) == 'output':
            function = re.search(r'\bfunction\s*:\s*"([^"]+)"\s*;', pin_block)
            if function is None:
                raise ValueError(f'Cell {cell_name}.{pin} has no combinational function')
            outputs.append((pin, function.group(1).replace('*', '&').replace('+', '|')))
    ports = inputs + [pin for pin, _ in outputs]
    code = [f"module {cell_name}({', '.join(ports)});"]
    code += [f"input {', '.join(inputs)};"] if inputs else []
    code += [f"output {', '.join(pin for pin, _ in outputs)};"] if outputs else []
    code += [f"assign {pin} = {function};" for pin, function in outputs]
    code += ["endmodule\n"]
    return '\n'.join(code)


def _write_used_nangate_cells(cell_path, sources):
    lib_path = f'{os.path.dirname(__file__)}/lib/NangateOpenCellLibrary_typical.lib'
    lib_text = open(lib_path, 'r').read()
    lib_cells = set(re.findall(r'\n\s*cell\s*\(([^)]+)\)\s*\{', lib_text))
    used_cells = set()
    for src in sources:
        for line in open(src, 'r', errors='ignore'):
            m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s+\S+\s*\(', line)
            if m and m.group(1) in lib_cells:
                used_cells.add(m.group(1))
    with open(cell_path, 'w') as f:
        f.write('\n'.join(_liberty_cell_model(lib_text, cell) for cell in sorted(used_cells)))


def verify_multiplier(work_dir, bw0, bw1, is_signed):
    """
    Multiplier verification.
    """
    work_dir = os.path.abspath(work_dir)
    rtl_path = os.path.join(os.path.dirname(work_dir), 'rtl')
    fa_ha_dir = f'{os.path.dirname(__file__)}/env/fa_ha'
    os.makedirs(work_dir, exist_ok=True)

    mul_name = f"mul{bw0}x{bw1}_RL"
    comb_file = os.path.join(work_dir, 'input_combs.csv')
    if bw0+bw1 <= 20:  # Exhaustive combinations.
        if is_signed:
            a = np.arange(-2**(bw0-1), 2**(bw0-1), dtype=np.int32)
            b = np.arange(-2**(bw1-1), 2**(bw1-1), dtype=np.int32)
        else:
            a = np.arange(2**bw0, dtype=np.uint32)
            b = np.arange(2**bw1, dtype=np.uint32)
        aa, bb = np.meshgrid(a, b, indexing='ij')
        input_combs = np.stack([aa.ravel(), bb.ravel()], axis=1)
    else:  # 2**20 random, non-repeating test cases.
        rng = np.random.default_rng()
        space_size = (1 << bw0) * (1 << bw1)
        num_cases = 2**20
        idx = rng.choice(space_size, size=num_cases, replace=False)
        a = idx // (1 << bw1)
        b = idx %  (1 << bw1)
        if is_signed:
            a = a.astype(np.int64)
            b = b.astype(np.int64)
            a[a >= (1 << (bw0 - 1))] -= (1 << bw0)
            b[b >= (1 << (bw1 - 1))] -= (1 << bw1)
        input_combs = np.stack([a, b], axis=1)
    np.savetxt(comb_file, input_combs, fmt="%d", delimiter=",")

    if is_signed:
        with open(f'{os.path.dirname(__file__)}/config/vtb_signed_template.sv', 'r') as f:
            template = f.read()
    else:
        with open(f'{os.path.dirname(__file__)}/config/vtb_unsigned_template.sv', 'r') as f:
            template = f.read()
    code = template.format(BW0=bw0, BW1=bw1, MUL_NAME=mul_name)
    out_path = os.path.join(work_dir, f'{mul_name}_vtb.sv')
    with open(out_path, 'w') as fout:
        fout.write(code)

    rtl_sources = (
        sorted(os.path.join(fa_ha_dir, f) for f in os.listdir(fa_ha_dir) if f.endswith('.v')) +
        sorted(os.path.join(rtl_path, f) for f in os.listdir(rtl_path) if f.endswith('.v'))
    )
    cell_path = os.path.join(work_dir, 'nangate_cells.v')
    _write_used_nangate_cells(cell_path, rtl_sources)
    sources = [cell_path] + rtl_sources + [out_path]
    simv_path = os.path.join(work_dir, 'verify.out')
    log_path = os.path.join(work_dir, 'verify.log')
    run_logged([tool_path('iverilog'), '-g2012', '-o', simv_path] + sources, cwd=work_dir, log_name=log_path)
    run_logged([tool_path('vvp'), simv_path], cwd=work_dir, log_name=log_path, mode='a')

    with open(log_path, 'r', errors='replace') as f:
        log_text = f.read()
    if '[PASS]' not in log_text or '[FAIL]' in log_text:
        raise RuntimeError(f'Multiplier verification failed. See {log_path}')
    print(f'Multiplier verification passed. Log: {log_path}')
