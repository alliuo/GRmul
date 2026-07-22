import torch
from torch_geometric.data import Data


class PPGraph():
    def __init__(self, bw0, bw1):
        self.bw0 = bw0
        self.bw1 = bw1
        self.max_weight = bw0 + bw1

        self.pp_dict = {}
        self.node_level = []
        self.node_weight = []
        self.node_DIBS = []
        self.node_type = []
        self.edge_types = []
        self.edges = []
        
        self.data = Data()
        self.data.x_raw     = torch.empty((0,1), dtype=torch.float) # level
        self.data.weight    = torch.empty((0,1), dtype=torch.float)
        self.data.DIBS      = torch.empty((0,self.max_weight), dtype=torch.float)
        self.data.node_type = torch.empty((0,), dtype=torch.long)
        self.data.in_type   = torch.empty((0,), dtype=torch.long) # in-degree
        self.data.out_type  = torch.empty((0,), dtype=torch.long) # out-degree

        self.data.is_cand    = torch.empty((0,1), dtype=torch.float)
        self.data.edge_index = torch.empty((2,0), dtype=torch.long)
        self.data.edge_type  = torch.empty((0,), dtype=torch.long)
        self.data.num_nodes  = 0


    def add_pp(self, pp, parents_idx):
        """
        Add a PP to the graph
        """
        idx = self._add_node(pp.level, pp.weight, pp.node_type, pp.DIBS)
        pp.set_graph_idx(idx)
        if parents_idx != []: # Not an initial PP.
            edge_type = pp.adder_output_role # 0: sum, 1: cout.
            for p_idx in parents_idx: 
                # Add edge.
                self.edges.append((p_idx, idx)) # Parent -> child.
                self.edge_types.append(edge_type)
        self._rebuild_edge_tensors()
        self._recompute_degrees()
        self.pp_dict[idx] = pp
        return idx


    def take_invert(self, pp_idx):
        """
        Invert a PP
        """
        self.get_pp(pp_idx).take_invert()
        self.node_type[pp_idx] = 2
        self._rebuild_node_tensors()


    def ha_to_fa(self, new_input_idx, sum_idx, cout_idx):
        """
        Modify a half adder into a full adder by connecting sum and cout to the new input.
        """
        # Sum output.
        self.edges.append((new_input_idx, sum_idx))
        self.edge_types.append(0)
        self.node_level[sum_idx] = self.pp_dict[sum_idx].level # Update level.
        self.node_DIBS[sum_idx] = [int(i or j) for i, j in \
                                    zip(self.node_DIBS[sum_idx], self.node_DIBS[new_input_idx])]
        # Cout output.
        if cout_idx is not None:
            self.edges.append((new_input_idx, cout_idx))
            self.edge_types.append(1)
            self.node_level[cout_idx] = self.pp_dict[cout_idx].level # Update level.
            self.node_DIBS[cout_idx] = [int(i or j) for i, j in \
                                         zip(self.node_DIBS[cout_idx], self.node_DIBS[new_input_idx])]
        # Rebuild tensors.
        self._rebuild_node_tensors()
        self._rebuild_edge_tensors()
        self._recompute_degrees()


    def _add_node(self, level, weight, node_type, DIBS):
        """
        Add a node to the graph
        """
        idx = len(self.node_level) # New node index.
        self.node_level.append(level)
        self.node_weight.append(weight)
        self.node_type.append(node_type)
        # Encode the DIBS.
        tmp_DIBS = [0] * self.max_weight
        for p in DIBS:
            if p.startswith('a'):
                tmp_DIBS[int(p[1:])] = 1
            elif p.startswith('b'):
                tmp_DIBS[int(p[1:]) + self.bw0] = 1
        self.node_DIBS.append(tmp_DIBS)
        self._rebuild_node_tensors()
        return idx


    def _rebuild_node_tensors(self):
        """
        Rebuild the node tensors
        """
        N = len(self.node_level)
        level_norm = torch.tensor(self.node_level, dtype=torch.float) / max(self.node_level)
        weight_norm = torch.tensor(self.node_weight, dtype=torch.float) / self.max_weight

        self.data.x_raw = level_norm.unsqueeze(-1)
        self.data.weight = weight_norm.unsqueeze(-1)
        self.data.DIBS = torch.tensor(self.node_DIBS, dtype=torch.float)
        self.data.node_type = torch.tensor(self.node_type, dtype=torch.long)
        self.data.in_type = torch.zeros((N,), dtype=torch.float)
        self.data.out_type = torch.zeros((N,), dtype=torch.float)
        self.data.num_nodes = N


    def _rebuild_edge_tensors(self):
        """
        Rebuild the edge tensors
        """
        if len(self.edges) > 0:
            src, dst = zip(*self.edges)
            self.data.edge_index = torch.tensor([src, dst], dtype=torch.long)
        else:
            self.data.edge_index = torch.empty((2,0), dtype=torch.long)
        self.data.edge_type = torch.tensor(self.edge_types, dtype=torch.long)


    def _recompute_degrees(self):
        """
        Recompute the in degree and out degree of nodes
        """
        N = len(self.node_level)
        in_deg  = torch.zeros((N,), dtype=torch.long)
        out_deg = torch.zeros((N,), dtype=torch.long)
        ei = self.data.edge_index
        if ei.numel() > 0:
            src, dst = ei
            out_deg.scatter_add_(0, src, torch.ones_like(src, dtype=torch.long))
            in_deg .scatter_add_(0, dst, torch.ones_like(dst, dtype=torch.long))

        # Map possible in-degree values [0, 2, 3] to in_type [0, 1, 2].
        in_deg[in_deg == 2] = 1   # 2 -> 1
        in_deg[in_deg == 3] = 2   # 3 -> 2
        self.data.in_type = in_deg

        # Map out-degree to out_type.
        self.data.out_type = out_deg


    def get_data(self, target_weight):
        """
        Return graph data.
        Nodes with target weight and out-degree 0 are marked as candidates.
        """
        data_clone = self.data.clone()
        data_clone.is_cand = ((data_clone.weight == (target_weight/self.max_weight)) & \
                              (data_clone.out_type.unsqueeze(-1) == 0)).float()
        return data_clone
    
    
    def get_pp(self, idx):
        return self.pp_dict[idx]
