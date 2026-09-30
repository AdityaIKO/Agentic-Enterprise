"""Tabular Q-learning for the *expedite* (overtime) decision  (lecture Ch.4 sec.9 and Ch.5 sec.5.4).

  s = (slack bucket, value bucket, stage)     a in {normal, overtime}
  Q(s,a) <- Q(s,a) + alpha [ r + gamma max_a' Q(s',a') - Q(s,a) ]
  r = -overtime_cost (per step)  and at the end  -late_penalty  (delayed reward)
Training happens in a small abstraction of the shop (queue waits + breakdowns as random delays);
evaluation happens in the full simulator (sim.py), so we test transfer, not memorisation."""
import numpy as np

from . import config as C

SLACK_EDGES = np.array([-4.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.5, 5.0])
N_SLACK = len(SLACK_EDGES) + 1
ACTIONS = ["normal", "overtime"]


def slack_bucket(slack):
    return int(np.searchsorted(SLACK_EDGES, slack, side="right"))


def value_bucket(value):
    return int(value >= 30_000)


def state_index(slack, value, stage):
    return (slack_bucket(slack) * 2 + value_bucket(value)) * 3 + stage


N_STATES = N_SLACK * 2 * 3

# closings of the three weekly carriers relative to the committed one (pattern of gaps 3,2,2)
_NEXT = np.array([0, 2, 3, 5, 7, 9, 10, 12, 14, 16, 17, 19, 21, 23, 24, 26, 28, 30])


def miss_lateness(slack):
    """Days late w.r.t. the tolerance if the order is short by -slack days at the port gate."""
    if slack >= 0:
        return 0.0
    need = -slack
    nxt = _NEXT[np.searchsorted(_NEXT, need, side="left")]
    return max(0.0, float(nxt) - C.LSD_GRACE_DAYS + 0.0)


class ExpediteEnv:
    def __init__(self, rng):
        self.rng = rng

    def reset(self):
        r = self.rng
        self.q = float(r.choice([0.6, 1.0, 1.5]))
        self.value = float(r.choice([12e3, 22e3, 38e3, 55e3, 80e3]))
        self.ops = [m * self.q * r.uniform(0.8, 1.25) for m in C.OP_MEAN_DAYS]
        rem = sum(self.ops)
        self.slack = float(r.normal(0.6, 2.6)) + 0.0 * rem     # slack before stage 0 (days)
        self.stage = 0
        return state_index(self.slack, self.value, 0)

    def step(self, a):
        r = self.rng
        d = self.ops[self.stage]
        wait = r.exponential(0.45 * d)
        if r.random() < 0.10:                        # breakdown / disruption at this stage
            wait += r.uniform(1.0, 3.5)
        speed = C.OVERTIME_SPEEDUP if a == 1 else 1.0
        elapsed = d / speed + wait
        cost = C.OVERTIME_COST_PER_DAY * d / speed if a == 1 else 0.0
        # slack is measured against the *planned* duration (1.0x): finishing faster than plan adds slack
        self.slack -= (elapsed - d * 1.0)
        reward = -cost
        self.stage += 1
        done = self.stage == 3
        if done:
            reward -= C.late_penalty(self.value, miss_lateness(self.slack))
            return None, reward, True
        return state_index(self.slack, self.value, self.stage), reward, False


def train_q(episodes=300_000, alpha_min=0.01, gamma=0.97, eps0=1.0, eps_min=0.05, seed=0):
    rng = np.random.default_rng(seed)
    env = ExpediteEnv(rng)
    Q = np.zeros((N_STATES, 2))
    N = np.zeros((N_STATES, 2))                       # visit counts -> decaying learning rate
    curve, acc = [], 0.0
    for ep in range(episodes):
        eps = max(eps_min, eps0 * (1 - ep / (0.6 * episodes)))
        s = env.reset()
        tot = 0.0
        while True:
            a = int(rng.integers(2)) if rng.random() < eps else int(np.argmax(Q[s]))
            s2, r, done = env.step(a)
            target = r if done else r + gamma * Q[s2].max()
            N[s, a] += 1
            alpha = max(alpha_min, 1.0 / N[s, a] ** 0.7)
            Q[s, a] += alpha * (target - Q[s, a])           # TD update
            tot += r
            if done:
                break
            s = s2
        acc += tot
        if (ep + 1) % 10_000 == 0:
            curve.append((ep + 1, acc / 10_000)); acc = 0.0
    return Q, curve


def evaluate_policy(policy, episodes=4000, seed=123):
    """policy(slack, value, stage) -> 0/1 ; same env, fresh randomness."""
    rng = np.random.default_rng(seed)
    env = ExpediteEnv(rng)
    tot = 0.0
    for _ in range(episodes):
        env.reset()
        ret = 0.0
        while True:
            a = policy(env.slack, env.value, env.stage)
            _, r, done = env.step(a)
            ret += r
            if done:
                break
        tot += ret
    return tot / episodes


def q_policy(Q):
    return lambda slack, value, stage: int(np.argmax(Q[state_index(slack, value, stage)]))


def td_example(q=2.0, alpha=0.2, r=5.0, gamma=0.9, maxq=4.0):
    """Worked example from lecture Ch.4/5 (target 8.6, TD error 6.6, Q_new 3.32)."""
    target = r + gamma * maxq
    return dict(target=target, td_error=target - q, q_new=q + alpha * (target - q))
