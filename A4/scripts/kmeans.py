"""Lloyd's K-Means with the D² seeding of Arthur & Vassilvitskii (2007).

Reference: https://research.google/pubs/k-means-the-advantages-of-careful-seeding/
Only NumPy is used here; sklearn is used for comparison in the notebook.
"""

import numpy as np


def squared_distances(X, centers):
    distances = np.empty((len(X), len(centers)))
    for j, center in enumerate(centers):
        distances[:, j] = ((X - center) ** 2).sum(axis=1)
    return distances


def kmeans_plus_plus(X, k, rng):
    """Return k initial centers, shape (k, X.shape[1])."""
    centers = [X[rng.integers(len(X))].copy()]
    nearest = ((X - centers[0]) ** 2).sum(axis=1)
    for _ in range(1, k):
        if nearest.sum() == 0:
            raise ValueError("k exceeds the number of distinct points.")
        index = rng.choice(len(X), p=nearest / nearest.sum())
        centers.append(X[index].copy())
        nearest = np.minimum(nearest, ((X - X[index]) ** 2).sum(axis=1))
    return np.asarray(centers)


def kmeans_once(X, centers, max_iter=300, tol=1e-4):
    """Return centers, labels, inertia, n_iter for one initialization."""
    X = np.asarray(X, dtype=float)
    centers = np.array(centers, dtype=float, copy=True)
    if (X.ndim != 2 or centers.ndim != 2 or X.shape[1] != centers.shape[1]
            or not 1 <= len(centers) <= len(X) or max_iter < 1 or tol < 0
            or not np.isfinite(X).all() or not np.isfinite(centers).all()):
        raise ValueError("Check data, centers, max_iter and tolerance.")
    k = len(centers)
    previous = np.full(len(X), -1)

    for iteration in range(1, max_iter + 1):
        distances = squared_distances(X, centers)
        labels = distances.argmin(axis=1)
        counts = np.bincount(labels, minlength=k)

        # Move farthest points into empty clusters without emptying their donors.
        errors = distances[np.arange(len(X)), labels]
        for empty in np.flatnonzero(counts == 0):
            candidates = np.flatnonzero(counts[labels] > 1)
            index = candidates[np.argmax(errors[candidates])]
            counts[labels[index]] -= 1
            labels[index] = empty
            counts[empty] = 1

        updated = np.array([X[labels == j].mean(axis=0) for j in range(k)])
        converged = (np.array_equal(labels, previous)
                     or np.linalg.norm(updated - centers) <= tol)
        centers = updated
        if converged:
            break
        previous = labels.copy()

    # Keep returned labels/inertia consistent even when max_iter stopped the run.
    distances = squared_distances(X, centers)
    labels = distances.argmin(axis=1)
    inertia = distances[np.arange(len(X)), labels].sum()
    return centers, labels, float(inertia), iteration


def kmeans(X, k, n_init=10, max_iter=300, tol=1e-4, seed=42):
    """Run several initializations and return the result with lowest inertia."""
    X = np.asarray(X, dtype=float)
    if (X.ndim != 2 or not np.isfinite(X).all() or n_init < 1
            or not 1 <= k <= len(np.unique(X, axis=0))):
        raise ValueError("Use finite 2D data, positive n_init and k <= distinct rows.")
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_init):
        initial = kmeans_plus_plus(X, k, rng)
        result = kmeans_once(X, initial, max_iter, tol)
        if best is None or result[2] < best[2]:
            best = result
    return best
