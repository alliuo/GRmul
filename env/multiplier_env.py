import os
import shutil
import gym
import z3
import json
import numpy as np
from multiprocessing import Pool
from .partial_product import PP
from .pp_graph import PPGraph
from .full_adder import FA
from .half_adder import HA
from utils import float_to_fname
import eda_flow


CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
MULTIPLIER_ENV_CONFIG_PATH = os.path.join(CONFIG_DIR, 'multiplier_env.json')

with open(MULTIPLIER_ENV_CONFIG_PATH, 'r', encoding='utf-8') as f:
    ENV_CONFIG = json.load(f)

REFERENCE_METRIC = {
    (item['bw0'], item['bw1'], item['encoding']): (item['area'], item['delay'])
    for item in ENV_CONFIG['reference_metric']
}
SUPPORTED_REFERENCE_CONFIGS = ', '.join(
    f"{bw0}x{bw1}/{encoding}"
    for bw0, bw1, encoding in sorted(REFERENCE_METRIC)
)


class MultiplierEnv(gym.Env):
    """
    Multiplier environment
    """
    def __init__(self, 
                 bw0, 
                 bw1, 
                 work_dir,
                 encoding='no'):
        
        self.bw0 = bw0
        self.bw1 = bw1
        self.work_dir = work_dir
        self.encoding = encoding
        if ('b4' in encoding) and ((bw0%2 != 0) or (bw1%2 != 0)):
            raise ValueError(f"'{encoding}' encoding requires an even bit width, current bit width is {bw0}x{bw1}.")

        # Load parameters
        self.reward_scale = ENV_CONFIG['reward_scale']
        self.target_delays = ENV_CONFIG['target_delays']
        self.area_delay_rate = ENV_CONFIG['area_delay_rate']
        reference_key = (bw0, bw1, encoding)
        if reference_key not in REFERENCE_METRIC:
            raise ValueError(
                f"No reference area/delay is configured for {bw0}x{bw1}/{encoding}. "
                f"Supported configurations: {SUPPORTED_REFERENCE_CONFIGS}."
            )
        self.ref_area, self.ref_delay = REFERENCE_METRIC[reference_key]
        
        # Z3 solver
        self.solver = z3.SimpleSolver()
        
        # Load adder name mappings.
        with open(os.path.join(CONFIG_DIR, 'AFA_AHA_map.json'), 'r', encoding='utf-8') as f:
            serial = json.load(f)
        AFA_AHA_map = {}
        for klist, v in serial:
            key = tuple(tuple(x) for x in klist) # Restore dictionary keys.
            AFA_AHA_map[key] = v
        
        # Load adder configuration.
        adder_metric_file = os.path.join(CONFIG_DIR, 'adder_metrics_nangate45.json')
        with open(adder_metric_file, "r", encoding="utf-8") as f:
            adder_metrics = json.load(f)
        self.adder_configs = {
            'solver' : self.solver,
            'delay_dict' : adder_metrics[1],
            'AFA_AHA_map' : AFA_AHA_map
        }

        # Runtime state.
        self.pp_graph = None
        self.col_pp_num = [] # Number of PPs in each PP-array column.
        self.pp_name_idx = 0
        self.ha_name_idx = 0 # This is not always equal to the total HA count.
        self.fa_name_idx = 0
        self.fa_dict = {}
        self.ha_dict = {}
        self.delay_dict = {} # Estimated PP delays.
        self.action_seq = []
        self.current_weight = 0        
        self.state = None
        self.reset()


    @staticmethod
    def syn_mul(ys_path, rtl_path, mul_name, target_delay):
        eda_flow.build_syn_env(ys_path, rtl_path, mul_name, target_delay)
        eda_flow.run_synthesis(ys_path)
        # Extract synthesis metrics.
        area = None
        delay = None
        with open(ys_path + "/openroad.log", "r") as f:
            rpt = f.read().splitlines()
            for line in rpt:
                if len(line.rstrip()) < 2:
                    continue
                line = line.rstrip().split()
                if line[0] == "wns":
                    delay = line[-1]
                    continue
                if line[0] == "Design":
                    area = line[2]
                    break
        if area is None or delay is None:
            raise RuntimeError(f"Cannot parse synthesis metrics from {ys_path}/openroad.log")
        metric_dict = {"area": float(area), "delay": float(delay)}
        return metric_dict


    def record_rtl(self, mul_name, area, delay, reward):
        origin_rtl_path = os.path.join(self.work_dir, 'rtl')
        origin_rtl_file = os.path.join(origin_rtl_path, f'{mul_name}.v')
        # Add metrics to the RTL file.
        insert_text = f"// Area: {area}, Delay: {delay}\n"
        with open(origin_rtl_file, 'r') as f:
            lines = f.readlines()
        lines.insert(0, insert_text)
        with open(origin_rtl_file, 'w') as f:
            f.writelines(lines)
        # Save generated RTL.
        target_path = os.path.join(os.path.dirname(self.work_dir), 'out', float_to_fname(reward))
        shutil.copytree(origin_rtl_path, target_path, dirs_exist_ok=True)


    def get_reward(self):
        # Evaluate with Yosys and OpenROAD.
        # Create the work directory.
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        os.mkdir(self.work_dir)
        rtl_path = os.path.join(self.work_dir, 'rtl')
        os.mkdir(rtl_path)
        # Generate RTL.
        mul_name, adder_name_list = eda_flow.code_mul(rtl_path, self.bw0, self.bw1, self.encoding, self.pp_graph.pp_dict, self.fa_dict, self.ha_dict)
        # Synthesize unknown FA and HA cells.
        if adder_name_list != []:
            tmp_syn_dir = os.path.join(self.work_dir, 'tmp_syn')
            os.mkdir(tmp_syn_dir)
            eda_flow.syn_unknown_adder(tmp_syn_dir, rtl_path, adder_name_list)
        # Build synthesis environments and run synthesis in parallel.
        metrics_dict = {"area": [], "delay": []}
        synthesis_errors = []
        n_processing = len(self.target_delays)
        with Pool(n_processing) as pool:
            def collect_metric(metric_dict):
                for k in metric_dict.keys():
                    metrics_dict[k].append(metric_dict[k])
            def on_error(e):
                synthesis_errors.append(str(e) or repr(e))
            for i, target_delay in enumerate(self.target_delays):
                ys_path = os.path.join(self.work_dir, f"ys{i}")
                os.mkdir(ys_path)
                pool.apply_async(
                    func=self.syn_mul,
                    args=(ys_path, rtl_path, mul_name, target_delay),
                    callback=collect_metric,
                    error_callback=on_error,
                )
            pool.close()
            pool.join()
        if synthesis_errors:
            raise RuntimeError(
                f"Synthesis failed in {len(synthesis_errors)} worker(s): "
                f"{synthesis_errors[0]}"
            )
        if len(metrics_dict["area"]) != n_processing or len(metrics_dict["delay"]) != n_processing:
            raise RuntimeError(
                "Synthesis returned incomplete metric results: "
                f"area={len(metrics_dict['area'])}, delay={len(metrics_dict['delay'])}, "
                f"expected={n_processing}"
            )
        # Calculate reward
        avg_area = np.mean(metrics_dict["area"])
        avg_delay = np.mean(metrics_dict["delay"])
        # Delay reward.
        delay_reward = (self.ref_delay-avg_delay) / self.ref_delay
        # Area reward.
        area_reward = (self.ref_area-avg_area) / self.ref_area
        # Combined reward.
        reward = (self.area_delay_rate[0]*area_reward + self.area_delay_rate[1]*delay_reward) * self.reward_scale
        # Record the RTL file.
        self.record_rtl(mul_name, avg_area, avg_delay, reward)

        return reward


    def reset(self):
        self.pp_graph = PPGraph(self.bw0, self.bw1)
        if self.solver is not None:
            self.solver.reset()
        self.col_pp_num = np.zeros(self.bw0+self.bw1, dtype=int)
        self.fa_dict = {}
        self.ha_dict = {}
        self.delay_dict = {}
        self.action_seq = []

        # PP encoding.
        if self.encoding == 'b2': # Radix-2 Booth encoding of b.
            sign_bits_dec = 0 # Decimal value of the Baugh-Wooley sign-bit row.
            for i in range(self.bw1):
                parent1 = [f'b{0}', '0'] if i == 0 else [f'b{i}', f'b{i-1}']
                for j in range(self.bw0):
                    parent0 = [f'a{j}']
                    weight = i+j
                    tmp_pp = PP(f'booth{i}[{j}]', weight, parent0+parent1, 4, solver=self.solver, is_initial=True)
                    pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                    self.col_pp_num[weight] += 1
                    self.delay_dict[pp_idx] = 0
                    if j == self.bw0-1: # Baugh-Wooley
                        self.pp_graph.take_invert(pp_idx) # Baugh-Wooley
                        sign_bits_dec += 2**(i+j)
                # Negative signals.
                tmp_pp = PP(f'neg[{i}]', i, parent1, 5, solver=self.solver, is_initial=True)
                pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                self.col_pp_num[i] += 1
                self.delay_dict[pp_idx] = 0
            # Baugh-Wooley
            sign_bits_dec %= (2**(self.bw0+self.bw1))
            inv_bin = (-sign_bits_dec) & (2**(self.bw0+self.bw1)-1)
            for i in range(self.bw0+self.bw1):
                if (inv_bin >> i) & 1: # Bit i is 1.
                    self._add_constant1(f'constant1_{i}', i)

        elif self.encoding == 'b4': # Radix-4 Booth encoding of b.
            sign_bits_dec = 0 # Decimal value of the Baugh-Wooley sign-bit row.
            for i in range(0, self.bw1, 2):
                parent1 = [f'b{i+1}', f'b{i}', '0'] if i == 0 else [f'b{i+1}', f'b{i}', f'b{i-1}']
                for j in range(self.bw0 + 1): # Extend one sign bit to represent 2*a.
                    if j == 0:
                        parent0 = [f'a{0}', '0']
                    elif j == self.bw0: # Sign-bit extension.
                        parent0 = [f'a{j-1}', f'a{j-1}']
                    else:
                        parent0 = [f'a{j}', f'a{j-1}']
                    weight = i+j
                    tmp_pp = PP(f'booth{i//2}[{j}]', weight, parent0+parent1, 4, solver=self.solver, is_initial=True)
                    pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                    self.col_pp_num[weight] += 1
                    self.delay_dict[pp_idx] = 0
                    if j == self.bw0: # Baugh-Wooley
                        self.pp_graph.take_invert(pp_idx) # Baugh-Wooley
                        sign_bits_dec += 2**(i+j)
                # Negative signals.
                tmp_pp = PP(f'neg[{i//2}]', i, parent1, 5, solver=self.solver, is_initial=True)
                pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                self.col_pp_num[i] += 1
                self.delay_dict[pp_idx] = 0
            # Baugh-Wooley
            sign_bits_dec %= (2**(self.bw0+self.bw1))
            inv_bin = (-sign_bits_dec) & (2**(self.bw0+self.bw1)-1)
            for i in range(self.bw0+self.bw1):
                if (inv_bin >> i) & 1: # Bit i is 1.
                    self._add_constant1(f'constant1_{i}', i)

        elif self.encoding == 'b4u': # Unsigned Radix-4 Booth encoding of b with MSB zero padding.
            sign_bits_dec = 0 # Decimal value of the Baugh-Wooley sign-bit row.
            for i in range(0, self.bw1+2, 2):
                if i == 0:
                    parent1 = [f'b{i+1}', f'b{i}', '0']
                elif i == self.bw1: # Pad two zeros at the MSB of b.
                    parent1 = ['0', '0', f'b{i-1}']
                else:
                    parent1 = [f'b{i+1}', f'b{i}', f'b{i-1}']
                for j in range(self.bw0 + 1): # Extend one bit to represent 2*a.
                    if j == 0:
                        parent0 = [f'a{0}', '0']
                    elif j == self.bw0: # Sign-bit zero extension.
                        parent0 = ['0', f'a{j-1}']
                    else:
                        parent0 = [f'a{j}', f'a{j-1}']
                    weight = i+j
                    if weight < self.bw0+self.bw1: # Ignore overflowing PPs.
                        tmp_pp = PP(f'booth{i//2}[{j}]', weight, parent0+parent1, 4, solver=self.solver, is_initial=True)
                        pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                        self.col_pp_num[weight] += 1
                        self.delay_dict[pp_idx] = 0
                # Negative signals.
                if i < self.bw1: # the negative signal for {0, 0, b[bw1-1]} is a constant 0.
                    tmp_pp = PP(f'neg[{i//2}]', i, parent1, 5, solver=self.solver, is_initial=True)
                    pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                    self.col_pp_num[i] += 1
                    self.delay_dict[pp_idx] = 0
                # Sign extension for the PP vector, same as the negative signal.
                extend_weight = i + self.bw0 + 1
                if extend_weight < self.bw0+self.bw1: # Ignore overflowing PPs.
                    tmp_pp = PP(f'sign_ext[{i//2}]', extend_weight, parent1, 5, solver=self.solver, is_initial=True)
                    pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                    self.col_pp_num[extend_weight] += 1
                    self.delay_dict[pp_idx] = 0
                    self.pp_graph.take_invert(pp_idx) # Baugh-Wooley
                    sign_bits_dec += 2**extend_weight # Baugh-Wooley
            # Baugh-Wooley
            sign_bits_dec %= (2**(self.bw0+self.bw1))
            inv_bin = (-sign_bits_dec) & (2**(self.bw0+self.bw1)-1)
            for i in range(self.bw0+self.bw1):
                if (inv_bin >> i) & 1: # Bit i is 1.
                    self._add_constant1(f'constant1_{i}', i)

        else:
            # AND-based PP array.
            tmp_pp_array = np.zeros((self.bw0, self.bw1), dtype=int)
            for i in range(self.bw0):
                for j in range(self.bw1):
                    weight = i+j
                    tmp_pp = PP(f'a{i}*b{j}', weight, [f'a{i}', f'b{j}'], 1, solver=self.solver, is_initial=True)
                    pp_idx = self.pp_graph.add_pp(tmp_pp, [])
                    self.col_pp_num[weight] += 1
                    self.delay_dict[pp_idx] = 0
                    tmp_pp_array[i,j] = pp_idx

            # Modified Baugh-Wooley multiplication.
            if self.encoding == 'bw':
                if self.bw0 != self.bw1:
                    raise ValueError("Baugh-Wooley algorithm is currently implemented only for square bit widths.")
                # Invert the sign bit.
                for i in range(0, self.bw0-1):
                    self.pp_graph.take_invert(tmp_pp_array[self.bw0-1, i])
                    self.pp_graph.take_invert(tmp_pp_array[i, self.bw0-1])
                # Add constant 1.
                self._add_constant1(f'constant1_{self.bw0}', self.bw0)
                self._add_constant1(f'constant1_{2*self.bw0-1}', 2*self.bw0-1)

        self.pp_name_idx = 0
        self.ha_name_idx = 0
        self.fa_name_idx = 0
        self.current_weight = np.argmax(self.col_pp_num > 1)
        self.state = self.pp_graph.get_data(self.current_weight)
        return self.state


    def step(self, action):
        assert len(action)==3, "Invalid action"
        self.action_seq.append(action)
        if not action[2]: # Half adder.
            self._compress_using_ha(action[:2])
        else: # Full adder.
            self._compress_using_fa(action[0], action[1])

        if np.max(self.col_pp_num) == 1:
            done = True
            reward = self.get_reward()
        elif self.col_pp_num[self.current_weight] == 1: # Current column is compressed.
            done = False
            reward = 0
            self.current_weight += 1
        else:
            done = False
            reward = 0

        self.state = self.pp_graph.get_data(self.current_weight)
        return self.state, reward, done


    def _add_constant1(self, pp_name, weight):
        """
        Add a constant 1 to the pp array
        """
        constant1 = PP(pp_name, weight, ['1'], 3, solver=self.solver, is_initial=True)
        constant1_idx = self.pp_graph.add_pp(constant1, [])
        self.col_pp_num[weight] += 1
        self.delay_dict[constant1_idx] = 0
        return constant1_idx


    def _compress_using_ha(self, input_idxs, enable_cout=True):
        # Input PPs.
        input0 = self.pp_graph.get_pp(input_idxs[0]) # PP0.
        input1 = self.pp_graph.get_pp(input_idxs[1]) # PP1.
        assert input0.weight == input1.weight, f"PP weights are not the same and cannot be added together {input0.weight}, {input1.weight}"
        target_col = input0.weight
        self.col_pp_num[target_col] -= 1
        if (target_col == self.bw0+self.bw1-1) or not enable_cout:
            has_cout = False
        else:
            has_cout = True
            self.col_pp_num[target_col+1] += 1
        
        # Output PPs.
        sum = PP('pp_' + str(self.pp_name_idx), target_col, [input0, input1], 0, solver=self.solver)
        self.pp_name_idx += 1
        sum_idx = self.pp_graph.add_pp(sum, input_idxs)
        if has_cout:
            cout = PP('pp_' + str(self.pp_name_idx), target_col+1, [input0, input1], 1, solver=self.solver)
            self.pp_name_idx += 1
            cout_idx = self.pp_graph.add_pp(cout, input_idxs)
        
        # Half adder
        if has_cout:
            tmp_ha = HA('ha_' + str(self.ha_name_idx), input0, input1, sum, cout, self.adder_configs)
        else:
            tmp_ha = HA('ha_' + str(self.ha_name_idx), input0, input1, sum, None, self.adder_configs)
        self.ha_name_idx += 1
        self.ha_dict[sum_idx] = tmp_ha
        input0_delay = self.delay_dict[input_idxs[0]]
        input1_delay = self.delay_dict[input_idxs[1]]
        tmp_ha.update_input_order([input0_delay, input1_delay])

        # Update delay.
        self.delay_dict[sum_idx] = tmp_ha.sum_delay
        if has_cout:
            self.delay_dict[cout_idx] = tmp_ha.cout_delay
        
        return tmp_ha


    def _compress_using_fa(self, sum_idx, input2_idx):
        # Find and remove the original HA.
        orig_ha = self.ha_dict[sum_idx]
        input0 = orig_ha.input0
        input1 = orig_ha.input1
        sum = orig_ha.sum
        assert (self.pp_graph.get_pp(sum_idx) is sum), "HA lookup failed."
        cout = orig_ha.cout
        orig_type = orig_ha.type
        del self.ha_dict[sum_idx]
        del orig_ha

        # Input PP.
        input2 = self.pp_graph.get_pp(input2_idx)
        assert input0.weight == input1.weight == input2.weight, f"PP weights are not the same and cannot be added together {input0.weight}, {input1.weight}, {input2.weight}"
        target_col = input0.weight
        self.col_pp_num[target_col] -= 1

        # Update output PPs.
        if cout is not None:
            sum.add_parent(input2)
            cout.add_parent(input2)
            self.pp_graph.ha_to_fa(input2.graph_idx, sum.graph_idx, cout.graph_idx)
        else:
            sum.add_parent(input2)
            self.pp_graph.ha_to_fa(input2.graph_idx, sum.graph_idx, None)

        # Full adder
        tmp_fa = FA('fa_' + str(self.fa_name_idx), input0, input1, input2, sum, cout, self.adder_configs)
        self.fa_name_idx += 1
        self.fa_dict[sum_idx] = tmp_fa
        input0_delay = self.delay_dict[input0.graph_idx]
        input1_delay = self.delay_dict[input1.graph_idx]
        input2_delay = self.delay_dict[input2.graph_idx]
        tmp_fa.update_input_order([input0_delay, input1_delay, input2_delay])
        
        # Update delay.
        self.delay_dict[sum_idx] = tmp_fa.sum_delay
        if cout is not None:
            self.delay_dict[cout.graph_idx] = tmp_fa.cout_delay

        return tmp_fa, orig_type
