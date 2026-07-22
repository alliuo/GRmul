import torch
import torch.nn as nn
import numpy as np
from torch_geometric.data import Batch
from torch.distributions import Categorical
from torch_geometric.nn import global_add_pool, global_max_pool, RGCNConv


class GraphEncoder(nn.Module):
    def __init__(self,
                 device,
                 bw0,
                 bw1,
                 emb_dim,
                 hidden_dim,
                 conv_layer_num):
        
        super().__init__()
        self.device = device

        # Encoder
        self.level_proj = nn.Linear(1, emb_dim)
        self.weight_proj = nn.Linear(1, emb_dim)
        self.DIBS_proj = nn.Linear(bw0+bw1, emb_dim)
        self.node_type_proj = nn.Embedding(num_embeddings=5, embedding_dim=emb_dim)
        self.in_type_proj = nn.Embedding(num_embeddings=3, embedding_dim=emb_dim)
        self.out_type_proj = nn.Embedding(num_embeddings=3, embedding_dim=emb_dim)
        
        # DAG encoder
        self.input_lin = nn.Sequential(nn.Linear(6*emb_dim, hidden_dim), nn.ReLU())
        self.convs = nn.ModuleList([RGCNConv(hidden_dim, hidden_dim, num_relations=2) for _ in range(conv_layer_num)])
        self.act = nn.ReLU()


    def forward(self, data):
        level = data.x_raw.to(self.device)
        weight = data.weight.to(self.device)
        DIBS = data.DIBS.to(self.device)
        node_type = data.node_type.to(self.device)
        in_type = data.in_type.to(self.device)
        out_type = data.out_type.to(self.device)
        edge_index = data.edge_index.to(self.device)
        edge_type = data.edge_type.to(self.device)
        
        # Encode node features.
        level_p = self.level_proj(level)
        weight_p = self.weight_proj(weight)
        node_type_p = self.node_type_proj(node_type)
        DIBS_p = self.DIBS_proj(DIBS)
        in_type_p = self.in_type_proj(in_type)
        out_type_p = self.out_type_proj(out_type)
        h_in = torch.cat([level_p, weight_p, DIBS_p, node_type_p, in_type_p, out_type_p], dim=-1)
        
        # Encode the DAG.
        h = self.input_lin(h_in)
        for conv in self.convs:
            h_next = conv(h, edge_index, edge_type)   # Message passing.
            h = self.act(h_next)
        
        return h


class ActorCritic(nn.Module):
    def __init__(self,
                 device,
                 bw0,
                 bw1,
                 emb_dim = 8,
                 hidden_dim = 64,
                 conv_layer_num = 3):

        super().__init__()
        self.device = device
        
        self.encoder = GraphEncoder(
            device = self.device,
            bw0 = bw0,
            bw1 = bw1,
            emb_dim = emb_dim,
            hidden_dim = hidden_dim,
            conv_layer_num = conv_layer_num
        )

        # Pair policy MLP: maps concat(h_i, h_j) to action logits.
        self.pair_mlp = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 2)
        )

        # Critic value head.
        self.value_ext_head = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

        self._init_weights()
        self.to(device)


    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        

    def forward(self, data):
        batch = data.batch.to(self.device)
        node_type = data.node_type.to(self.device)
        in_type = data.in_type.to(self.device)
        is_cand = data.is_cand.to(self.device)
        
        # Encode graph states.
        h = self.encoder(data)

        # Graph-level value
        h_add_pool = global_add_pool(h, batch)
        h_max_pool = global_max_pool(h, batch)
        h_pool = torch.cat([h_add_pool, h_max_pool], dim=-1)
        value_ext = self.value_ext_head(h_pool)  # [batch_num, 1]

        # Candidate selection: compute policy logits only for candidate nodes.
        cand_mask = (is_cand.view(-1) == 1)
        candidate_global_idx = torch.nonzero(cand_mask, as_tuple=False).view(-1)  # [M_total]
        h_cands = h[candidate_global_idx]       # [M_total, hidden_dim]
        candidate_batch = batch[candidate_global_idx]  # [M_total]
        is_valid_ha_sum = (node_type[candidate_global_idx] == 0) & (in_type[candidate_global_idx] == 1) 
        # Build flattened pair logits for each graph.
        batch_num = int(value_ext.shape[0])
        pair_flats = []
        pair_rows = []
        pair_cols = []
        for i in range(batch_num):
            mask_i = (candidate_batch == i)
            h_i = h_cands[mask_i]  # [M_i, hidden]
            is_valid_ha_sum_i = is_valid_ha_sum[mask_i]
            M_i = h_i.size(0)
            if M_i < 2:
                raise RuntimeError("Need >=2 candidate nodes to sample a pair.")
            
            # Node pairs.
            upper = torch.triu_indices(M_i, M_i, offset=1, device=self.device)
            lower = torch.vstack([upper[1], upper[0]])
            rows, cols = torch.cat([upper, lower], dim=1)
            h_i_rows = h_i[rows]  # [num_pairs, hidden_dim]
            h_i_cols = h_i[cols]  # [num_pairs, hidden_dim]
            pair_inp = torch.cat([h_i_rows, h_i_cols], dim=-1)  # [num_pairs, 2*hidden_dim]

            # Pair action logits.
            joint_logits = self.pair_mlp(pair_inp) # [num_pairs, 2]
            can_merge = is_valid_ha_sum_i[rows]
            joint_logits[:, 1] = torch.where(can_merge,
                                            joint_logits[:, 1],
                                            torch.tensor(-1e9, device=self.device, dtype=joint_logits.dtype))
            pair_flats.append(joint_logits.view(-1))
            pair_rows.append(rows)
            pair_cols.append(cols)

        return value_ext, candidate_global_idx, pair_flats, pair_rows, pair_cols
    

    def get_action_value(self, data):
        """
        Sample pair for a **single** graph (data is single graph).
        Returns:
          action: [node0, node1, merge]  (node0 and node1 are indices in the input graph; merge is 0 or 1)
          logp_pair - log probability under the current policy
          value_ext - graph value
        """
        # Forward
        data = Batch.from_data_list([data]).to(self.device)
        value_ext, candidate_global_idx, pair_flats, pair_rows, pair_cols = self.forward(data)
        value_ext = float(value_ext.item())
        pair_flat = pair_flats[0]
        rows = pair_rows[0]
        cols = pair_cols[0]
        
        # Sample pair
        dist = Categorical(logits=pair_flat)
        sel_pair = dist.sample()
        logp = float(dist.log_prob(sel_pair).item())

        # Map flat index back to [node0, node1, merge]
        pair_idx = sel_pair//2
        merge_flag = sel_pair % 2
        sel_row = int(rows[pair_idx].item())
        sel_col = int(cols[pair_idx].item())
        node0 = int(candidate_global_idx[sel_row].item())
        node1 = int(candidate_global_idx[sel_col].item())
        merge = bool(merge_flag)
        action = [node0, node1, merge]
        
        return action, int(sel_pair.item()), logp, value_ext


    def evaluate_actions(self, data_batch, sel_pair_batch):
        """
        data_batch - batch of graphs.
        sel_pair_batch - iterable/list of length batch_size
        Returns:
          logp_tensor: Tensor [batch]
          value_ext: Tensor [batch]
          entropy_tensor: Tensor [batch]
        """
        # Forward
        value_ext, _, pair_flats, _, _ = self.forward(data_batch)
        batch_num = int(value_ext.shape[0])

        if isinstance(sel_pair_batch, torch.Tensor):
            sel_pair_batch = sel_pair_batch.tolist()

        log_probs_new = []
        entropies = []

        # Evaluate each graph separately.
        for i in range(batch_num):
            # Select candidates for graph i
            pair_flat = pair_flats[i]   # tensor [num_pairs_i]
            dist = Categorical(logits=pair_flat)

            # Action
            sel_pair = sel_pair_batch[i]
 
            # Obtain log probability and entropy.
            sel_pair_tensor = torch.tensor(sel_pair, dtype=torch.long, device=pair_flat.device)
            logp = dist.log_prob(sel_pair_tensor)
            entropy = dist.entropy()
            log_probs_new.append(logp)
            entropies.append(entropy)

        logp_tensor = torch.stack(log_probs_new).to(self.device)  # (batch,)
        entropy_tensor = torch.stack(entropies).to(self.device)   # (batch,)
        return logp_tensor, value_ext.view(-1), entropy_tensor
