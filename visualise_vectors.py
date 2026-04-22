#!/usr/bin/env python3
"""
Visualize stored embedding vectors from DocumentChunk in 2D and 3D.

Usage:
  python visualise_vectors.py
  python visualise_vectors.py --source my_file.pdf --limit 300 --show
  python visualise_vectors.py --user-message "What is bank" --show
"""

import argparse
import os
import sys
from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot DocumentChunk embeddings in 2D and 3D using PCA."
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional source filter (exact match of DocumentChunk.source).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of vectors to load (default: 500).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save output images (default: current directory).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="embeddings",
        help="Output filename prefix (default: embeddings).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Open plot windows interactively in addition to saving images.",
    )
    parser.add_argument(
        "--user-message",
        action="append",
        default=[],
        help=(
            "User query sentence to embed and plot alongside stored vectors. "
            "Can be provided multiple times."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-k nearest chunks to print per user message (default: 5).",
    )
    parser.add_argument(
        "--snippet-chars",
        type=int,
        default=180,
        help="Max characters of chunk content to show in results (default: 180).",
    )
    return parser.parse_args()


def require_dependencies():
    try:
        import numpy as np
        import matplotlib.pyplot as plt
    except ImportError as exc:
        print(
            "Missing dependency. Install with:\n"
            "  pip install numpy matplotlib\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    return np, plt


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_agent.settings")
    try:
        import django

        django.setup()
    except Exception as exc:
        print(
            "Could not initialize Django. Run this script from the project root and "
            "ensure DB settings are valid.\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


def load_chunks(source_filter=None, limit=500):
    from chat.models import DocumentChunk

    queryset = DocumentChunk.objects.all().order_by("id")
    if source_filter:
        queryset = queryset.filter(source=source_filter)
    queryset = queryset[:limit]

    chunks = []
    for chunk in queryset:
        emb = chunk.embedding
        if emb is None:
            continue
        try:
            if len(emb) == 0:
                continue
        except TypeError:
            # Non-sized embedding object; continue and let conversion below validate.
            pass

        chunks.append(
            {
                "id": chunk.id,
                "source": chunk.source or "unknown",
                "content": chunk.content or "",
                "embedding": list(emb),
            }
        )

    return chunks


def pca_fit(np, data_matrix, n_components):
    if data_matrix.shape[0] == 0:
        return None, None

    mean = data_matrix.mean(axis=0)
    if data_matrix.shape[0] == 1:
        # One point cannot produce variance; fixed basis at zeros.
        basis = np.zeros((data_matrix.shape[1], n_components))
        return mean, basis

    centered = data_matrix - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    basis = vt[:n_components].T
    return mean, basis


def pca_transform(np, matrix, mean, basis):
    if matrix.shape[0] == 0:
        return matrix
    if mean is None or basis is None:
        raise ValueError("PCA model is not fitted.")
    return (matrix - mean) @ basis


def embed_user_messages(user_messages):
    if not user_messages:
        return [], []

    try:
        from chat.services.gemini_service import GeminiService

        gemini = GeminiService()
    except Exception as exc:
        print(
            "Could not initialize GeminiService to embed `--user-message` values. "
            "Continuing without plotting user messages.\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        return [], []

    vectors = []
    labels = []
    for msg in user_messages:
        try:
            vectors.append(gemini.get_embedding(msg))
            labels.append(msg)
        except Exception as exc:
            print(
                f"Failed to embed user message: {msg!r}. Skipping.\nDetails: {exc}",
                file=sys.stderr,
            )

    return vectors, labels


def cosine_distances(np, matrix, vector):
    # Returns cosine distance = 1 - cosine_similarity
    # Shapes: matrix [n, d], vector [d]
    denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(vector)
    denom = np.where(denom == 0, 1.0, denom)
    sims = (matrix @ vector) / denom
    return 1.0 - sims


def print_topk_results(np, chunks, matrix, query_vector, query_label, top_k, snippet_chars):
    dists = cosine_distances(np, matrix, query_vector)
    order = np.argsort(dists)[: max(0, top_k)]

    label = (query_label or "").strip().replace("\n", " ")
    label = (label[:200] + "...") if len(label) > 203 else label
    print("\nQuery:", repr(label))
    if len(order) == 0:
        print("No results (top_k=0).")
        return

    print(f"Top {len(order)} nearest chunks (cosine distance):")
    for rank, idx in enumerate(order, start=1):
        c = chunks[int(idx)]
        snippet = (c.get("content") or "").strip().replace("\n", " ")
        if snippet_chars is not None and snippet_chars >= 0 and len(snippet) > snippet_chars:
            snippet = snippet[:snippet_chars] + "..."
        print(
            f"{rank}. id={c.get('id')} source={c.get('source')!r} "
            f"distance={float(dists[int(idx)]):.6f} snippet={snippet!r}"
        )


def plot_2d(plt, points_2d, sources, output_path, query_points=None, query_labels=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    grouped = defaultdict(lambda: ([], []))
    for (x, y), source in zip(points_2d, sources):
        grouped[source][0].append(x)
        grouped[source][1].append(y)

    for source, (xs, ys) in grouped.items():
        ax.scatter(xs, ys, s=28, alpha=0.8, label=source)

    ax.set_title("Embedding Vectors (PCA 2D)")
    ax.set_xlabel("Principal Component 1")
    ax.set_ylabel("Principal Component 2")
    if len(grouped) <= 15:
        ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.25)

    if query_points is not None and len(query_points) > 0:
        for idx, (x, y) in enumerate(query_points):
            label = "query"
            if query_labels and idx < len(query_labels):
                short = query_labels[idx].strip().replace("\n", " ")
                short = (short[:40] + "...") if len(short) > 43 else short
                label = f"query: {short}"
            ax.scatter([x], [y], s=220, marker="*", c="black", label=label, zorder=5)
        ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    return fig


def plot_3d(plt, points_3d, sources, output_path, query_points=None, query_labels=None):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    grouped = defaultdict(lambda: ([], [], []))
    for (x, y, z), source in zip(points_3d, sources):
        grouped[source][0].append(x)
        grouped[source][1].append(y)
        grouped[source][2].append(z)

    for source, (xs, ys, zs) in grouped.items():
        ax.scatter(xs, ys, zs, s=25, alpha=0.8, label=source)

    ax.set_title("Embedding Vectors (PCA 3D)")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("PC3")
    if len(grouped) <= 10:
        ax.legend(loc="best", fontsize=8)

    if query_points is not None and len(query_points) > 0:
        for idx, (x, y, z) in enumerate(query_points):
            label = "query"
            if query_labels and idx < len(query_labels):
                short = query_labels[idx].strip().replace("\n", " ")
                short = (short[:40] + "...") if len(short) > 43 else short
                label = f"query: {short}"
            ax.scatter([x], [y], [z], s=180, marker="*", c="black", label=label)
        ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    return fig


def main():
    args = parse_args()
    np, plt = require_dependencies()
    setup_django()

    chunks = load_chunks(source_filter=args.source, limit=args.limit)
    if not chunks:
        print("No embeddings found for the selected filters.")
        sys.exit(0)

    data = np.array([c["embedding"] for c in chunks], dtype=float)
    sources = [c["source"] for c in chunks]
    n_samples, n_dims = data.shape
    print(f"Loaded {n_samples} vectors with dimension {n_dims}.")

    mean, basis3 = pca_fit(np, data, n_components=3)
    if mean is None or basis3 is None:
        print("Not enough data to fit PCA.")
        sys.exit(0)

    points_3d = pca_transform(np, data, mean, basis3)
    points_2d = pca_transform(np, data, mean, basis3[:, :2])

    query_vectors, query_labels = embed_user_messages(args.user_message)
    query_points_2d = None
    query_points_3d = None
    if query_vectors:
        q = np.array(query_vectors, dtype=float)
        if q.shape[1] != n_dims:
            print(
                f"User message embedding dim mismatch: expected {n_dims}, got {q.shape[1]}. "
                "Skipping user message plotting.",
                file=sys.stderr,
            )
        else:
            query_points_3d = pca_transform(np, q, mean, basis3)
            query_points_2d = pca_transform(np, q, mean, basis3[:, :2])
            for qvec, qlabel in zip(q, query_labels):
                print_topk_results(
                    np,
                    chunks,
                    data,
                    qvec,
                    qlabel,
                    top_k=max(0, int(args.top_k)),
                    snippet_chars=int(args.snippet_chars),
                )

    os.makedirs(args.output_dir, exist_ok=True)
    out_2d = os.path.join(args.output_dir, f"{args.prefix}_2d.png")
    out_3d = os.path.join(args.output_dir, f"{args.prefix}_3d.png")

    fig2d = plot_2d(
        plt,
        points_2d,
        sources,
        out_2d,
        query_points=query_points_2d,
        query_labels=query_labels,
    )
    fig3d = plot_3d(
        plt,
        points_3d,
        sources,
        out_3d,
        query_points=query_points_3d,
        query_labels=query_labels,
    )

    print(f"Saved 2D plot: {out_2d}")
    print(f"Saved 3D plot: {out_3d}")

    if args.show:
        plt.show()
    else:
        plt.close(fig2d)
        plt.close(fig3d)


if __name__ == "__main__":
    main()
