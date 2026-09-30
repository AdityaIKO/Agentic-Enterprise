"""Online Q-learning inside the *integrated* simulator (fixes the transfer gap of the abstract environment).

Each shipped order yields a trajectory  (s_0,a_0,c_0) -> (s_1,a_1,c_1) -> (s_2,a_2,c_2) -> terminal reward -late_penalty.
Q(s,a) <- Q(s,a) + alpha [ r + gamma max_a' Q(s',a') - Q(s,a) ],  r = -overtime cost, terminal r = -(late penalty).
Training seeds (>= 10_000) never overlap with evaluation seeds (0..299) or calibration seeds (1000+)."""
import numpy as np

from . import config as C
from . import rl
from .data import make_scenario
from .sim import Sim


def train_in_sim(models, n_scenarios=3000, gamma=0.97, alpha_min=0.02, eps0=0.6, eps_min=0.05, seed0=10_000, log_every=100):
    Q = np.zeros((rl.N_STATES, 2))
    N = np.zeros((rl.N_STATES, 2))
    curve, acc = [], 0.0
    for k in range(n_scenarios):
        eps = max(eps_min, eps0 * (1 - k / (0.7 * n_scenarios)))
        m = dict(models); m["Q"] = Q
        sc = make_scenario(seed0 + k)
        s = Sim(sc, "mas", m, dict(expedite="qtrain", eps=eps))
        res = s.run()
        for r in s.orders:
            tr = r.traj
            if not tr:
                continue
            pen = r.penalty
            for i in range(len(tr) - 1, -1, -1):
                st, a, c = tr[i]
                if i == len(tr) - 1:
                    target = -c - pen
                else:
                    target = -c + gamma * Q[tr[i + 1][0]].max()
                N[st, a] += 1
                alpha = max(alpha_min, 1.0 / N[st, a] ** 0.6)
                Q[st, a] += alpha * (target - Q[st, a])
        acc += -(res["penalty"] + res["overtime"])
        if (k + 1) % log_every == 0:
            curve.append((k + 1, acc / log_every)); acc = 0.0
    return Q, curve
