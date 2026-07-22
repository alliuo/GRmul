import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Batch
from torch.utils.data.sampler import BatchSampler, SubsetRandomSampler
import policy


class PPO():
    def __init__(self, bw0, bw1, encoding, device, is_retrain=False):
        super(PPO, self).__init__()
        self.clip_param = 0.2
        self.max_grad_norm = 0.5
        self.ppo_epoch = 8
        if encoding=='b4':
            self.buffer_capacity = int(10 * bw0 * bw1)
            self.batch_size = int(2.5 * bw0 * bw1)
        elif encoding=='b4u':
            self.buffer_capacity = int(12 * bw0 * bw1)
            self.batch_size = int(3 * bw0 * bw1)
        else:
            self.buffer_capacity = int(16 * bw0 * bw1)
            self.batch_size = int(4 * bw0 * bw1)

        if is_retrain:
            self.gamma = 1.0
            self.gae_lambda = 0.95
        else:
            self.gamma = 1.0
            self.gae_lambda = 1.0

        self.c1 = 0.5  # Value head weight.
        self.c2 = 0.01 # Entropy bonus weight.
        self.learn_rate = 1e-4

        # Model and optimizer.
        self.device = device
        self.policy = policy.ActorCritic(device=device, bw0=bw0, bw1=bw1)

        # Replay buffer.
        self.buffer = []
        self.step_counter = 0
        
        # Optimizer.
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=self.learn_rate)
 

    def store_transition(self, transition):
        self.buffer.append(transition)
        self.step_counter += 1
        return self.step_counter >= self.buffer_capacity


    def compute_gae(self, values, rewards, done_masks, gamma, gae_lambda):
        advantages = []
        gae = 0
        values = values + [0]  # Terminal bootstrap value.
        for step in reversed(range(len(rewards))):
            delta = rewards[step] + gamma * values[step + 1] * done_masks[step] - values[step]
            gae = delta + gamma * gae_lambda * done_masks[step] * gae
            advantages.insert(0, gae)
        returns = [adv + val for adv, val in zip(advantages, values[:-1])]
        return advantages, returns
    

    def update(self):
        # Prepare buffered rollout data.
        states = [t.state for t in self.buffer]
        sel_pairs = [t.sel_pair for t in self.buffer]
        logps = torch.tensor([t.logp for t in self.buffer], dtype=torch.float, device=self.device).view(-1).detach()
        values_ext = [t.value for t in self.buffer]
        rewards = [t.reward for t in self.buffer]
        done_masks = [0.0 if t.done else 1.0 for t in self.buffer]

        # Compute advantages and returns.
        advs, returns_ext = self.compute_gae(values_ext, rewards, done_masks, self.gamma, self.gae_lambda)
        advs = torch.tensor(advs, dtype=torch.float, device=self.device)
        advs = (advs - advs.mean()) / (advs.std() + 1e-9)
        returns_ext = torch.tensor(returns_ext, dtype=torch.float, device=self.device)

        # Train the policy.
        buf_len = len(self.buffer)
        for epoch in range(self.ppo_epoch):
            batch_sampler = BatchSampler(SubsetRandomSampler(range(buf_len)), self.batch_size, drop_last=False)
            print(f'================ Epoch {epoch} ================')
            for batch_idx in batch_sampler:
                # Collect a minibatch.
                states_batch = [states[i] for i in batch_idx]
                sel_pair_batch = [sel_pairs[i] for i in batch_idx]

                # Evaluate under the current policy.
                data_batch = Batch.from_data_list(states_batch).to(self.device)
                logp_new, values_ext_new, entropy = self.policy.evaluate_actions(data_batch, sel_pair_batch) # [batch_size]

                # Gather old log probabilities, advantages, and returns.
                logp_old = logps[batch_idx].view(-1).to(self.device) # [batch_size]
                adv_batch = advs[batch_idx].view(-1).to(self.device).detach() # [batch_size]
                returns_ext_batch = returns_ext[batch_idx].view(-1).to(self.device) # [batch_size]

                # Policy loss
                ratio = torch.exp(logp_new.view(-1) - logp_old)
                surr1 = ratio * adv_batch
                surr2 = torch.clamp(ratio, 1-self.clip_param, 1+self.clip_param) * adv_batch
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                value_ext_loss = F.mse_loss(values_ext_new.view(-1), returns_ext_batch)

                # Entropy bonus
                entropy_loss = -entropy.mean()

                # Loss
                loss = policy_loss + self.c1*value_ext_loss + self.c2*entropy_loss

                # Update the policy.
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.optimizer.step()
                print('Actor loss = {:.2f}, critic loss = {:.2f}'.format(policy_loss.item(), value_ext_loss.item()))
        
        print(f'================================================')
        self.buffer.clear()
        self.step_counter = 0
