"""Cross-validation designs for the audit (numpy and scikit-learn only).

Every function returns a list of REPEATS; each repeat is a list of (train_idx, test_idx)
folds. A single-pass design (leave-one-run-out, chronological) has one repeat; random
designs have several. Metrics are computed per repeat and then averaged, so repeats
reduce seed noise but never count as independent subjects.

Designs (names follow the requirements document):
  D1/D2  random k-fold (shuffled / stratified)        - trials from the same run mix across folds
  D1m    random k-fold with k = number of runs         - same number of folds as leave-one-run-out
  D1s    size-matched random split                     - same train and test SIZES as each leave-one-run-out fold
  D3     leave-one-run-out
  D4     chronological hold-out, D4b forward chaining
  D5     chronological hold-out with a gap of g trials
  D6     leave-one-session-out (needs 2+ sessions)

Why D1s exists: 5-fold trains on 80 percent of trials but leave-one-run-out on 3 runs trains
on about 67 percent. Less training data lowers accuracy by itself, so D1 minus D3 mixes
"leakage" with "training size". D1s removes that confound.
"""
import numpy as np
from sklearn.model_selection import KFold, StratifiedKFold


def loro_splits(groups):
    """Leave-one-group-out (runs or sessions). One repeat."""
    groups = np.asarray(groups)
    folds = []
    for g in np.unique(groups):
        folds.append((np.where(groups != g)[0], np.where(groups == g)[0]))
    return [folds]


def kfold_repeats(y, k=5, stratified=True, repeats=10, seed=0):
    """Random k-fold repeated `repeats` times with different seeds."""
    y = np.asarray(y)
    out = []
    for r in range(repeats):
        cv = (StratifiedKFold if stratified else KFold)(k, shuffle=True, random_state=seed + r)
        out.append([(tr, te) for tr, te in cv.split(np.zeros(len(y)), y)])
    return out


def size_matched_random_repeats(y, groups, repeats=20, seed=0):
    """Random trial-level PARTITION that mimics leave-one-group-out.

    In every repeat the trials are shuffled within each class and dealt out to one test set per
    group, so each test set has the same size and the same class counts as the real group and
    every trial is tested exactly once (the test sets are disjoint and cover all trials).
    Training set = the rest, so training sizes match leave-one-group-out exactly.

    (v0.2 drew each test set independently, so test sets overlapped inside a repeat and some
    trials were never tested; fixed in v0.3.)
    """
    y = np.asarray(y)
    groups = np.asarray(groups)
    rng = np.random.default_rng(seed)
    all_idx = np.arange(len(y))
    glist = np.unique(groups)
    out = []
    for _ in range(repeats):
        tests = {g: [] for g in glist}
        for c in np.unique(y):
            pool = rng.permutation(np.where(y == c)[0])
            start = 0
            for g in glist:
                n_c = int(((groups == g) & (y == c)).sum())
                tests[g].extend(pool[start:start + n_c])
                start += n_c
        folds = []
        for g in glist:
            test = np.sort(np.array(tests[g], dtype=int))
            folds.append((np.setdiff1d(all_idx, test), test))
        out.append(folds)
    return out


def _order_index(n, order):
    return np.argsort(order, kind="stable") if order is not None else np.arange(n)


def chrono_holdout(n, test_frac=1 / 3, gap=0, order=None):
    """Train on the first (1 - test_frac) of trials in time order, test on the rest.

    `gap` trials right after the training block are dropped, so training and test
    trials are never neighbours. The training block is the same for every gap.
    """
    idx = _order_index(n, order)
    n_train = n - int(round(n * test_frac))
    train, test = idx[:n_train], idx[n_train + gap:]
    if len(train) == 0 or len(test) == 0:
        raise ValueError("Chronological split leaves an empty train or test set.")
    return [[(np.sort(train), np.sort(test))]]


def forward_chain(n, n_splits=3, gap=0, order=None):
    """Expanding window: split time into n_splits+1 blocks; train on blocks 0..i-1, test on block i."""
    idx = _order_index(n, order)
    blocks = np.array_split(idx, n_splits + 1)
    folds = []
    for i in range(1, n_splits + 1):
        train = np.concatenate(blocks[:i])
        test = blocks[i][gap:]
        if len(test) == 0:
            raise ValueError("Gap removes the whole test block.")
        folds.append((np.sort(train), np.sort(test)))
    return [folds]


def session_splits(sessions):
    """Leave-one-session-out. Needs at least two sessions."""
    if len(np.unique(sessions)) < 2:
        raise ValueError("Leave-one-session-out needs at least 2 sessions.")
    return loro_splits(sessions)


def validate_splits(repeats, y, groups=None, order=None, min_gap=None, min_test=1):
    """Raise ValueError if any fold breaks a rule. Used by the tests and by the audit."""
    y = np.asarray(y)
    for folds in repeats:
        for tr, te in folds:
            if len(np.intersect1d(tr, te)) > 0:
                raise ValueError("Train and test overlap.")
            if len(te) < min_test:
                raise ValueError("Test fold too small.")
            if len(np.unique(y[tr])) < 2:
                raise ValueError("A training fold contains only one class.")
            if groups is not None:
                g = np.asarray(groups)
                if len(np.intersect1d(g[tr], g[te])) > 0:
                    raise ValueError("A group appears in both train and test.")
            if min_gap is not None and order is not None:
                o = np.asarray(order)
                dist = np.abs(o[te][:, None] - o[tr][None, :]).min()
                if dist < min_gap + 1:
                    raise ValueError(f"Gap violated: nearest train-test distance is {dist}.")
    return True


# ---- thin scikit-learn style wrappers so other people can reuse the designs ----
class GappedChronologicalSplit:
    """scikit-learn style splitter: first part train, last part test, `gap` trials removed between."""

    def __init__(self, test_frac=1 / 3, gap=0):
        self.test_frac, self.gap = test_frac, gap

    def split(self, X, y=None, groups=None):
        n = len(X)
        for tr, te in chrono_holdout(n, self.test_frac, self.gap)[0]:
            yield tr, te

    def get_n_splits(self, X=None, y=None, groups=None):
        return 1


class SizeMatchedRandomSplit:
    """scikit-learn style splitter: random splits with the same sizes as leave-one-group-out."""

    def __init__(self, n_repeats=20, seed=0):
        self.n_repeats, self.seed = n_repeats, seed

    def split(self, X, y, groups):
        for folds in size_matched_random_repeats(y, groups, self.n_repeats, self.seed):
            for tr, te in folds:
                yield tr, te

    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_repeats * len(np.unique(groups))
