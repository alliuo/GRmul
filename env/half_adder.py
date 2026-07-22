import z3
from itertools import product, permutations
from .partial_product import PP


class HA():
    """
    Half adder
    """
    def __init__(self, name, input0, input1, sum, cout, adder_configs):
        self.name = name
        if type(input0) != PP or type(input1) != PP:
            raise TypeError("There must be two PPs as the inputs.")
        self.input0 = input0
        self.input1 = input1
        self.sum = sum
        self.cout = cout
        self.type = None
        self.path_delay = [[0, 0], [0, 0]] # [[a_to_sum, b_to_sum], [a_to_cout, b_to_cout]]
        self.candidate_input_order = [[0, 1]]
        self.input_order = []
        self.sum_delay = 0
        self.cout_delay = 0
        self.missing_input_combinations = None
        self.update_type(adder_configs)


    def __repr__(self):
        if self.cout is None:
            return f"HA(name={self.name!r}, Type={self.type}, input0={self.input0.name}, input1={self.input1.name}, sum={self.sum.name}, cout=None)"
        else:
            return f"HA(name={self.name!r}, Type={self.type}, input0={self.input0.name}, input1={self.input1.name}, sum={self.sum.name}, cout={self.cout.name})"


    def update_type(self, adder_configs):
        """
        Update adder type: exact half adder or approximable half adder (AHA).
        """
        solver = adder_configs['solver']
        delay_dict = adder_configs['delay_dict']
        AFA_AHA_map = adder_configs['AFA_AHA_map']

        # Z3-based method for generic multipliers.
        v0 = self.input0.var
        v1 = self.input1.var
        missing_value_combinations = set()
        for comb in product([0, 1], repeat=2):
            bool_comb = [True if i==1 else False for i in comb]
            result = solver.check(v0==bool_comb[0], v1==bool_comb[1])
            if result == z3.unsat:
                missing_value_combinations.add(comb)
 
        # Determine the type from missing input combinations.
        if not missing_value_combinations:
            self.type = 'half_adder'
            self.candidate_input_order = list(permutations((0, 1)))
        else:
            self.candidate_input_order = []
            for order in permutations((0, 1)):
                transformed_comb = set((comb[order[0]], comb[order[1]]) for comb in missing_value_combinations)
                if tuple(sorted(transformed_comb)) in AFA_AHA_map:
                    self.type = AFA_AHA_map[tuple(sorted(transformed_comb))]
                    self.candidate_input_order.append(order)
            if self.candidate_input_order == []:
                self.missing_input_combinations = missing_value_combinations
                self.type = 'unknown'
                self.candidate_input_order = list(permutations((0, 1)))

        # Metrics
        if self.type != 'unknown':
            self.path_delay = delay_dict[self.type]
        else:
            self.path_delay = [[1, 1], [1, 1]]


    def update_input_order(self, input_delay_list):
        """
        Update input order based on the input delay to minimize critical path delay
        """
        min_delay = 1e25
        for tmp_input_order in self.candidate_input_order:
            tmp_sum_delay = max(input_delay_list[tmp_input_order[0]] + self.path_delay[0][0], \
                                input_delay_list[tmp_input_order[1]] + self.path_delay[0][1])
            tmp_cout_delay = max(input_delay_list[tmp_input_order[0]] + self.path_delay[1][0], \
                                input_delay_list[tmp_input_order[1]] + self.path_delay[1][1])
            critical_path_delay = max(tmp_sum_delay, tmp_cout_delay)
            if critical_path_delay < min_delay:
                min_delay = critical_path_delay
                self.input_order = tmp_input_order
                self.sum_delay = tmp_sum_delay
                self.cout_delay = tmp_cout_delay
