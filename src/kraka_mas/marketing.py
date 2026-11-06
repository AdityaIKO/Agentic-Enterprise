"""Digital Marketing & Ads Agent (exploratory).  Question: how should a small weekly ad budget be split across channels
when the best channel is unknown and differs per market?  Compared: fixed equal split (what a manual marketer often does)
vs the agent (Thompson sampling: shifts budget towards channels that produce qualified RFQs, keeps exploring).

EVERYTHING HERE IS AN ASSUMPTION: channel names are real options for a B2B exporter, but the base rates (qualified RFQ per USD)
are NOT measured KrakaCoal data.  True rates are redrawn per run (lognormal), so the best channel is unknown in advance.
Result = value of the *method* under these assumptions, not a forecast of real leads."""
import numpy as np

CHANNELS = ["Google Ads (search)", "LinkedIn Ads", "B2B marketplace listing", "Email / WhatsApp outreach", "SEO content"]
BASE_RATE = np.array([0.0040, 0.0025, 0.0050, 0.0060, 0.0020])      # ASSUMPTION: qualified RFQs per USD spent
UNIT = 25.0                                                          # USD per allocation step
WEEKLY = 500.0                                                       # USD per week (ASSUMPTION)
WEEKS = 12


def run_once(rng, strategy, sigma=0.6):
    true = BASE_RATE * rng.lognormal(0.0, sigma, len(BASE_RATE)) if sigma > 0 else BASE_RATE.copy()
    a = np.ones(len(true)); b = np.ones(len(true)) * 200.0          # Beta-like prior on rate per unit (mean ~ base scale)
    spend = np.zeros(len(true)); leads = np.zeros(len(true))
    for w in range(WEEKS):
        for _ in range(int(WEEKLY / UNIT)):
            if strategy == "fixed":
                k = int((_ + w) % len(true))
            else:
                k = int(np.argmax(rng.gamma(a, 1.0 / b)))            # Thompson sampling on Gamma(a, b) posterior of leads per USD
            got = rng.poisson(true[k] * UNIT)
            spend[k] += UNIT; leads[k] += got
            a[k] += got; b[k] += UNIT
    return leads.sum(), spend, leads


def run(n=400, seed=0, sigma=0.6):
    rng = np.random.default_rng(seed)
    out = {}
    for strat in ("fixed", "agent"):
        L = []; share = np.zeros(len(CHANNELS))
        for _ in range(n):
            l, sp, _ = run_once(rng, strat, sigma); L.append(l); share += sp / sp.sum()
        L = np.array(L)
        out[strat] = dict(leads_mean=float(L.mean()), leads_ci=[float(np.percentile(L, 2.5)), float(np.percentile(L, 97.5))],
                          cost_per_rfq=float(WEEKLY * WEEKS / L.mean()), share=(share / n).tolist())
    out["channels"] = CHANNELS; out["budget_total"] = WEEKLY * WEEKS; out["n_runs"] = n
    out["uplift_pct"] = 100 * (out["agent"]["leads_mean"] / out["fixed"]["leads_mean"] - 1)
    return out


def run_all():
    r = run(); r["uplift_fixed_ranking_pct"] = run(sigma=0.0)["uplift_pct"]
    return r


if __name__ == "__main__":
    import json, pathlib
    r = run_all(); pathlib.Path(__file__).resolve().parents[2].joinpath("outputs/marketing.json").write_text(json.dumps(r, indent=1))
    print(json.dumps({k: r[k] for k in ("uplift_pct", "uplift_fixed_ranking_pct")}, indent=1))
