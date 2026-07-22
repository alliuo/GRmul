import argparse
import os
import traceback
import gym
import torch
from manager_server import TrainingManager
from env import ENV_ID
import policy
from utils import EpisodeData, Transition, set_seed, serialize_data


parser = argparse.ArgumentParser(description="Worker process for distributed PPO")
parser.add_argument('--work_dir', type=str, required=True)
parser.add_argument('--encoding', type=str, required=True)
parser.add_argument('--bw0', type=int, required=True)
parser.add_argument('--bw1', type=int, required=True)
parser.add_argument('--seed', type=int, required=True)
parser.add_argument('--port', type=int, required=True)
args = parser.parse_args()

# If the parent process set CUDA_VISIBLE_DEVICES, cuda:0 maps to the selected GPU.
# Rollout can also run on CPU when CUDA is unavailable.
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

# Connect to the manager.
mgr = TrainingManager(address=('127.0.0.1', args.port), authkey=b'my_ppo')
mgr.connect()
finish_queue = mgr.get_finish_queue()
transition_queue = mgr.get_transition_queue()
policy_dict = mgr.get_policy_dict()


def worker_loop():
    set_seed(args.seed)

    multiplier_env = gym.make(ENV_ID, 
                              bw0 = args.bw0, 
                              bw1 = args.bw1, 
                              work_dir = args.work_dir,
                              encoding = args.encoding).unwrapped
    multiplier_env.seed(args.seed)
    tmp_policy = policy.ActorCritic(device=device, bw0=args.bw0, bw1=args.bw1)

    local_version = None

    while True:
        if finish_queue.get():
            break

        version = policy_dict.get('version', None)
        weights = policy_dict.get('weights', None)
        if version != local_version: # Update weights.
            local_version = version
            state_dict = {k: torch.tensor(v, device=device) for k, v in weights.items()}
            tmp_policy.load_state_dict(state_dict)
            
        state = multiplier_env.reset()
        done = False
        local_episode = []
        final_reward = 0
        while not done:
            with torch.no_grad():
                action, sel_pair, logp, value_ext = tmp_policy.get_action_value(state)
            next_state, reward, done = multiplier_env.step(action)
            # Save transition.
            local_episode.append(
                Transition(
                    state=serialize_data(state),
                    action=action,
                    sel_pair=int(sel_pair),
                    reward=float(reward),
                    logp=float(logp),
                    value=float(value_ext),
                    done=done
                )
            )
            state = next_state
            final_reward += reward
        # Episode complete.
        transition_queue.put(EpisodeData(
            transitions=local_episode,
            final_reward=final_reward,
            version=local_version
        ))


def report_worker_error(exc):
    try:
        transition_queue.put({
            'type': 'worker_error',
            'pid': os.getpid(),
            'work_dir': args.work_dir,
            'seed': args.seed,
            'error': repr(exc),
            'traceback': traceback.format_exc(),
        })
    except Exception:
        pass


if __name__ == '__main__':
    try:
        worker_loop()
    except Exception as exc:
        report_worker_error(exc)
        raise
