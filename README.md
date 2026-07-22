# GRmul

GRmul is a reinforcement-learning framework for optimizing multiplier
partial-product compression trees.

## Project Structure

```text
main.py            training driver
worker.py          rollout worker
manager_server.py  multiprocessing queues and shared policy state
policy.py          graph actor-critic model
ppo_trainer.py     PPO training logic
eda_flow.py        RTL generation, synthesis, timing, and verification
eda_tools.py       EDA tool command helpers
utils.py           common utilities
env/               multiplier environment and adder models
config/            EDA templates and training settings
lib/               Nangate45 Liberty/LEF files
examples/          example checkpoints and Pareto RTL results
requirements.txt   tested Python dependencies
```

## Requirements

Python dependencies are pinned in `requirements.txt`. The tested environment is:

```text
Python: 3.9.21
torch: 2.5.1
torch-geometric: 2.6.1
gym: 0.19.0
z3-solver: 4.15.4.0
numpy: 1.26.4
pandas: 2.3.1
matplotlib: 3.9.4
```

The EDA flow requires Yosys, OpenROAD, Icarus Verilog, and VVP. Tool commands
are configured in `config/eda_tools.json`.

The flow uses the Nangate45 Liberty/LEF files in `lib/` for synthesis, timing
evaluation, and simulation support.

## Installation

Install the tested Python package set:

```bash
pip install -r requirements.txt
```

Make sure `yosys`, `openroad`, `iverilog`, and `vvp` are available on `PATH`, or
edit `config/eda_tools.json` with your local tool commands.

## Configuration

`config/multiplier_env.json` stores reward scaling, synthesis target delays,
area-delay weights, and `reference_metric`. The `reference_metric` entries are
Wallace-tree multiplier metrics used as reward references.

The default `reference_metric` table covers the `no` and `b4u` encodings for
4x4, 8x8, 12x12, and 16x16 multipliers. Add matching references before training
other bit-width or encoding combinations.

Supported `--encoding` values:

- `no`: unsigned AND-based multiplier
- `bw`: signed modified Baugh-Wooley multiplier
- `b2`: signed Radix-2 Booth multiplier
- `b4`: signed Radix-4 Booth multiplier
- `b4u`: unsigned Radix-4 Booth multiplier

## Training

Pretrain a policy for the target multiplier setting:

```bash
python main.py \
  --num_workers 10 \
  --bw0 8 \
  --bw1 8 \
  --max_iter 3000 \
  --seed 10 \
  --encoding no \
  --gpu_idx 0
```

Retrain from an existing checkpoint:

```bash
python main.py \
  --num_workers 10 \
  --bw0 8 \
  --bw1 8 \
  --max_iter 3000 \
  --seed 10 \
  --encoding no \
  --init_weight examples/checkpoints/8x8_no.pth \
  --gpu_idx 0
```

The recommended workflow is to pretrain first, then retrain from the pretrained
policy. Retraining uses GAE `lambda = 0.95`, which usually improves convergence
stability and final quality. You can also retrain directly from one of the
provided checkpoints in `examples/checkpoints/`.

Key parameters:

- `--init_weight <checkpoint>` starts retraining from an existing policy.
- `--num_workers 10` is recommended because it matches the PPO buffer size.
  Larger values are usually not useful because extra workers may collect
  stale episodes that are discarded after the policy update.
- `--max_iter` must be an integer multiple of `--num_workers`.
- `--gpu_idx <idx>` restricts training to one GPU. If CUDA is unavailable, the
  code falls back to CPU.
- `--work_idx <0-9>` separates temporary files and ports. Use different values
  to run multiple `main.py` processes in parallel.
- Avoid `bw0 + bw1 > 32`; the problem can become very slow and hard to
  converge.

## Outputs

Training creates these local outputs:

- `checkpoints/policy_*.pth`: final trained policy weights
- `checkpoints/tmp_best_policy_<work_idx>.pth`: best policy during the run
- `out/training_record_*.csv`: episode score logs
- `out/rtl/`: best generated multiplier RTL
- `out/verify/`: verification testbench, input cases, and simulator log
- `out/pareto/`: collected area-delay Pareto RTL candidates
- `train0.pdf` and `train1.pdf`: score and running-score plots
- `tmp_<work_idx>/`: intermediate worker, RTL, and synthesis files

`examples/checkpoints/` contains example policy weights.
`examples/pareto_results/` contains example Pareto RTL.

## Third-Party Materials

The Nangate45 technology files in `lib/` are third-party materials governed by
their own license terms. Verify redistribution rights before publishing or
redistributing them.

Some simplified adder cells in `env/fa_ha/` were generated with Synopsys Design
Compiler in the original experimental flow. The public workflow does not
provide or require a Design Compiler interface. When a previously unknown
simplified adder is discovered, `eda_flow.py` generates its Verilog and 
`syn_unknown_adder(...)` maps it with Yosys using the configured Liberty file.

## Acknowledgements

This project is inspired by parts of
[laiyao1/ArithTreeRL](https://github.com/laiyao1/ArithTreeRL) and
[MIRALab-USTC/Arith-DAS](https://github.com/MIRALab-USTC/Arith-DAS).
