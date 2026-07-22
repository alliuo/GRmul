import os
import sys
import argparse
import time
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from subprocess import Popen
from ppo_trainer import PPO
from manager_server import TrainingManager
from utils import Transition, collect_pareto, float_to_fname, set_seed, deserialize_data
from eda_flow import verify_multiplier


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--init_weight', type = str, default = '')
    parser.add_argument('--encoding', choices=['no', 'bw', 'b2', 'b4', 'b4u'], default = 'no', help = """
    no : Unsigned AND-based multiplier.
    bw : Signed multiplier based on modified Baugh-Wooley algorithm.
    b2 : Signed multiplier based on Radix-2 Booth encoding.
    b4 : Signed multiplier based on Radix-4 Booth encoding.
    b4u : Unsigned multiplier based on Radix-4 Booth encoding.
    """)
    parser.add_argument('--work_idx', type = int, choices=list(range(10)), default=0, 
        help='worker group index; use different values to run multiple main processes in parallel')
    parser.add_argument('--seed', type = int, default=10, metavar='N', help='random seed (default: 10)')
    parser.add_argument('--bw0', type = int, default=4, help='bit-width of input0 (multiplicand) (default: 4)')
    parser.add_argument('--bw1', type = int, default=4, help='bit-width of input1 (multiplier) (default: 4)')
    parser.add_argument('--max_iter', type = int, default = 3000)
    parser.add_argument('--num_workers', type = int, default = 10)
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--gpu_idx', type=str, default=None, help='optional GPU index assigned to CUDA_VISIBLE_DEVICES')
    return parser.parse_args()


def create_work_dirs(work_idx=0):
    base_work_path = os.path.abspath(f'./tmp_{work_idx}')
    # Create the local work directory.
    if os.path.exists(base_work_path):
        shutil.rmtree(base_work_path)
    os.mkdir(base_work_path)
    os.mkdir(os.path.join(base_work_path, 'out'))
    return base_work_path


def create_output_dirs():
    os.makedirs('./checkpoints', exist_ok=True)
    os.makedirs('./out', exist_ok=True)


def format_worker_error(error):
    trace = error.get('traceback', '').rstrip()
    header = (
        f"Worker failed: pid={error.get('pid')}, seed={error.get('seed')}, "
        f"work_dir={error.get('work_dir')}, error={error.get('error')}"
    )
    return f"{header}\n{trace}" if trace else header


if __name__ == '__main__':
    args = parse_args()
    if args.gpu_idx is not None:
        os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu_idx

    import torch

    if args.port is None:
        args.port = 50000 + (args.work_idx * 10)
    is_retrain = args.init_weight != ''
    
    # If --gpu_idx is set, cuda:0 means the first visible device after CUDA_VISIBLE_DEVICES filtering.
    # Without CUDA, the same model code runs on CPU.
    main_device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    
    if (args.max_iter % args.num_workers) != 0:
        raise ValueError("'max_iter' must be an integer multiple of 'num_workers'")
    set_seed(args.seed)
    create_output_dirs()

    print('-----------------------------------------------------------')
    print(f'{args.bw0}x{args.bw1}, Encoding: {args.encoding}')
    print(f'Device: {main_device}')
    if args.gpu_idx is not None:
        print(f'CUDA_VISIBLE_DEVICES: {args.gpu_idx}')
    print('-----------------------------------------------------------')
    
    # Start the manager.
    mgr = TrainingManager(address=('127.0.0.1', args.port), authkey=b'my_ppo')
    mgr.start()
    finish_queue = mgr.get_finish_queue()
    transition_queue = mgr.get_transition_queue()
    policy_dict = mgr.get_policy_dict()

    # Initialize the agent.
    agent = PPO(bw0=args.bw0, bw1=args.bw1, encoding=args.encoding, device=main_device, is_retrain=is_retrain)
    if is_retrain:
        agent.policy.load_state_dict(torch.load(args.init_weight, weights_only=True, map_location=main_device))
    
    new_state = {'weights':{k: v.cpu().numpy() for k, v in agent.policy.state_dict().items()}, 'version':0}
    policy_dict.clear()
    policy_dict.update(new_state)

    # Launch workers.
    base_work_path = create_work_dirs(args.work_idx)
    for i in range(args.num_workers):
        work_dir = os.path.join(base_work_path, str(i))
        cmd = [sys.executable, 'worker.py',
           '--work_dir', work_dir,
           '--encoding', args.encoding,
           '--bw0', str(args.bw0),
           '--bw1', str(args.bw1),
           '--seed', str(args.seed + i),
           '--port', str(args.port)]
        Popen(cmd)
        time.sleep(1)
    
    # Training
    try:
        T1 = time.perf_counter()
        training_record = pd.DataFrame(columns = (['episode', 'score', 'running_score']))
        best_score = -float('inf')
        running_score = None
        episode_idx = 0
        while episode_idx < args.max_iter:
            for _ in range(args.num_workers):
                finish_queue.put(False)
            for _ in range(args.num_workers):
                ep_data = transition_queue.get()
                if isinstance(ep_data, dict) and ep_data.get('type') == 'worker_error':
                    raise RuntimeError(format_worker_error(ep_data))
                current_version = policy_dict.get('version', None) # Current policy version.
                if ep_data.version != current_version:
                    print(f"Discarding episode from version {ep_data.version} (current {current_version})")
                    continue
                
                # Record scores.
                score = ep_data.final_reward
                if running_score is None:
                    running_score = score
                else:
                    running_score = running_score * 0.9 + score * 0.1
                training_record.loc[training_record.shape[0]] = [int(episode_idx), score, running_score]

                # Store episode transitions in the PPO buffer.
                cnt = 0
                buffer_full = False
                for state_bytes, action, sel_pair, reward, logp, value, done in ep_data.transitions:
                    state = deserialize_data(state_bytes).to(main_device)
                    trans = Transition(state, action, sel_pair, reward, logp, value, done)
                    buffer_full = agent.store_transition(trans)
                    cnt += 1
                
                # Report the episode and update the best score.
                print("Episode {}, length: {}, moving average score: {:.2f}, score: {:.2f}"
                    .format(episode_idx, cnt, running_score, score))
                if score > best_score:
                    best_score = score
                    print(f"[New best] Episode {episode_idx}, score={score:.2f}")
                    save_path = f'./checkpoints/tmp_best_policy_{args.work_idx}.pth'
                    torch.save(agent.policy.state_dict(), save_path)

                # Update the agent.
                if buffer_full:
                    agent.update()
                    new_state = {'weights':{k: v.cpu().numpy() for k, v in agent.policy.state_dict().items()}, 'version':current_version+1}
                    policy_dict.clear()
                    policy_dict.update(new_state)
                
                episode_idx += 1
                if episode_idx >= args.max_iter:
                    break
    except Exception:
        for _ in range(args.num_workers):
            finish_queue.put(True)
        raise
    else:
        for _ in range(args.num_workers):
            finish_queue.put(True)
    T2 = time.perf_counter()
    run_time = T2-T1
    print('----------------- Finish -----------------')
    print(f'Best score: {best_score}')
    print(f"Total time: {run_time:.4f} seconds")

    # Save training records and policy weights.
    retrain_flag = '_retrain' if is_retrain else ''
    file_label = f'{args.bw0}x{args.bw1}_seed{args.seed}_{args.encoding}{retrain_flag}_{args.work_idx}'
    training_record.to_csv(f'./out/training_record_{file_label}.csv', index=False)
    save_path = f'./checkpoints/policy_{file_label}.pth'
    torch.save(agent.policy.state_dict(), save_path)
    print(f'Agent model saved to -> {save_path}')

    # Save the best multiplier.
    out_rtl_path = './out/rtl'
    best_rtl = os.path.join(base_work_path, 'out', f'{float_to_fname(best_score)}')
    if os.path.exists(out_rtl_path):
        shutil.rmtree(out_rtl_path)
    shutil.copytree(best_rtl, out_rtl_path)
    print(f"Copied best RTL from {best_rtl} to './out/rtl' (overwritten if it already exists)")

    # Verify the multiplier.
    verify_path = './out/verify'
    if os.path.exists(verify_path):
        shutil.rmtree(verify_path)
    os.mkdir(verify_path)
    is_signed = not (args.encoding=='no' or args.encoding=='b4u')
    verify_multiplier(verify_path, args.bw0, args.bw1, is_signed)

    # Collect area-delay Pareto frontier from all saved RTL candidates.
    pareto_path = './out/pareto'
    if os.path.exists(pareto_path):
        shutil.rmtree(pareto_path)
    os.mkdir(pareto_path)
    pareto_frontier = collect_pareto(os.path.join(base_work_path, 'out'), pareto_path)
    print(f"Collected {len(pareto_frontier)} Pareto RTL candidates to '{pareto_path}'")

    # Plot training progress.
    fig_idx = 0
    for score_type in ['score', 'running_score']:
        episodes = training_record['episode']
        scores  = training_record[score_type]
        plt.figure()
        plt.plot(episodes, scores, '-o', label='Running Score')
        plt.xlabel('Episode')
        plt.ylabel('Score')
        plt.title('Training Progress')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        fig = plt.gcf()
        fig.savefig(f'./train{fig_idx}.pdf', bbox_inches='tight')
        fig_idx += 1
