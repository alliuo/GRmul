import csv
import random
import re
import shutil
from collections import namedtuple
from pathlib import Path
import numpy as np
import torch
from torch_geometric.data import Data


Transition = namedtuple('Transition', ['state', 'action', 'sel_pair', 'reward', 'logp', 'value', 'done'])
EpisodeData = namedtuple('EpisodeData', ['transitions', 'final_reward', 'version'])
_PARETO_METRIC_RE = re.compile(
    r"Area:\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\D*"
    r"Delay:\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
    re.I,
)


def float_to_fname(f: float) -> str:
    """Convert score strings into portable folder names."""
    s = f"{f:.9g}"
    return s.replace('-', 'm')\
            .replace('.', 'p')\
            .replace('e', 'x')\
            .replace('+', 'q')


def set_seed(seed):
    """Keep Python, NumPy, and Torch random sources aligned."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if torch.backends.cudnn.enabled:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def serialize_data(data: Data):
    """Multiprocessing managers cannot share Torch tensors directly."""
    od = {}
    for key, item in data:
        if isinstance(item, torch.Tensor):
            od[key] = item.cpu().numpy()
        else:
            od[key] = item
    return od


def deserialize_data(raw: dict) -> Data:
    """Restore serialized NumPy arrays to tensors before PPO consumes them."""
    kwargs = {}
    for k, v in raw.items():
        if isinstance(v, np.ndarray):
            kwargs[k] = torch.from_numpy(v)
        else:
            kwargs[k] = v
    return Data(**kwargs)


def _read_pareto_metric(folder):
    rtl = next(Path(folder).glob("mul*.v"), None)
    if rtl is None:
        return None

    # Metrics are written by MultiplierEnv.record_rtl in the first RTL line.
    with open(rtl, "r", errors="replace") as f:
        match = _PARETO_METRIC_RE.search(f.readline())
    if not match:
        return None

    area, delay = map(float, match.groups())
    return {"name": Path(folder).name, "area": area, "delay": delay}


def collect_pareto(indir, out_dir):
    """Copy area-delay Pareto RTL candidates from indir to out_dir."""
    indir = Path(indir)
    out_dir = Path(out_dir)

    rows = [_read_pareto_metric(d) for d in sorted(indir.iterdir()) if d.is_dir()]
    rows = [row for row in rows if row is not None]
    rows.sort(key=lambda row: (row["area"], row["delay"], row["name"]))

    frontier = []
    min_delay = float("inf")
    for row in rows:
        if row["delay"] < min_delay:
            frontier.append(row)
            min_delay = row["delay"]

    for row in frontier:
        shutil.copytree(indir / row["name"], out_dir / row["name"])

    with open(out_dir / "pareto.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["mul_name", "area", "delay", "adp"])
        for row in frontier:
            writer.writerow([row["name"], row["area"], row["delay"], row["area"] * row["delay"]])

    return frontier
