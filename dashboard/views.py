from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.urls import reverse


SAFE_ARTIFACT_SUFFIXES = {".html", ".png", ".jpg", ".jpeg", ".svg", ".csv", ".xlsx", ".json"}


def _csv(name: str) -> pd.DataFrame:
    path = settings.PROCESSED_DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return "—"


def _fmt_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "—"


def _fmt_float(value: Any, ndigits: int = 3) -> str:
    try:
        return f"{float(value):.{ndigits}f}"
    except Exception:
        return "—"


def _records(df: pd.DataFrame, n: int | None = None) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    if n is not None:
        df = df.head(n)
    return df.fillna("").to_dict("records")


def artifact_url(path: str) -> str:
    return reverse("dashboard:artifact", kwargs={"artifact_path": path})


@lru_cache(maxsize=1)
def load_dashboard_data() -> Dict[str, Any]:
    senate = _csv("senate_national.csv")
    comparison = _csv("comparison.csv")
    correlations = _csv("correlations.csv")
    overlap = _csv("top12_overlap.csv")
    hashtag_metrics = _csv("hashtag_metrics.csv")
    candidate_metrics = _csv("candidate_comention_metrics.csv")
    bipartite_metrics = _csv("candidate_hashtag_metrics.csv")
    mentions = _csv("candidate_mention_frequency.csv")
    engagement = _csv("candidate_engagement_summary.csv")
    regional = _csv("regional_turnout.csv")
    ncr = _csv("ncr_vs_national.csv")

    top12 = senate.sort_values("vote_rank").head(12) if not senate.empty else pd.DataFrame()
    top_mentions = mentions.sort_values("count", ascending=False).head(12) if not mentions.empty else pd.DataFrame()
    top_hash = hashtag_metrics.sort_values("pagerank", ascending=False).head(12) if not hashtag_metrics.empty else pd.DataFrame()
    top_candidate_pr = candidate_metrics.sort_values("pagerank", ascending=False).head(12) if not candidate_metrics.empty else pd.DataFrame()
    top_bipartite_candidates = bipartite_metrics[bipartite_metrics.get("node_type", "") == "candidate"].copy() if not bipartite_metrics.empty else pd.DataFrame()
    if not top_bipartite_candidates.empty:
        top_bipartite_candidates = top_bipartite_candidates.sort_values("pagerank", ascending=False).head(12)

    # Over/under performance from mention rank if available.
    over_df = pd.DataFrame()
    if not comparison.empty and {"candidate", "vote_rank", "twitter_mention_count_rank", "twitter_mention_count_overperformance"}.issubset(comparison.columns):
        over_df = comparison[["candidate", "vote_rank", "twitter_mention_count_rank", "twitter_mention_count_overperformance", "winner_top12"]].copy()
        over_df = over_df.sort_values("twitter_mention_count_overperformance", ascending=False)

    best_corr = None
    if not correlations.empty and "spearman_r_vs_votes" in correlations.columns:
        row = correlations.sort_values("spearman_r_vs_votes", ascending=False).iloc[0]
        best_corr = {
            "metric": row.get("online_metric", "—"),
            "value": _fmt_float(row.get("spearman_r_vs_votes"), 3),
        }

    top_overlap = None
    if not overlap.empty and "top12_overlap_count" in overlap.columns:
        row = overlap.sort_values("top12_overlap_count", ascending=False).iloc[0]
        top_overlap = {
            "metric": row.get("online_metric", "—"),
            "count": _fmt_int(row.get("top12_overlap_count")),
            "precision": _fmt_float(row.get("precision_at_12"), 3),
        }

    cards = [
        {"label": "Tweets analyzed", "value": "217,640", "note": "Twitter/X election discourse"},
        {"label": "Unique authors", "value": "71,388", "note": "Pseudo-author accounts"},
        {"label": "Senate candidates", "value": _fmt_int(len(senate)) if not senate.empty else "66", "note": "Candidate outcome table"},
        {"label": "Actual winners", "value": "12", "note": "Final Senate Top 12"},
        {"label": "Best rank alignment", "value": best_corr["value"] if best_corr else "—", "note": best_corr["metric"] if best_corr else "Spearman correlation"},
        {"label": "Best Top-12 overlap", "value": f"{top_overlap['count']}/12" if top_overlap else "—", "note": top_overlap["metric"] if top_overlap else "Online metric"},
    ]

    artifact_map = {
        "actual_vote_ranking": "outputs/interactive/14_actual_vote_ranking_top20.html",
        "vote_rank_vs_mention_rank": "outputs/interactive/14_vote_rank_vs_mention_rank.html",
        "correlations": "outputs/interactive/14_metric_correlations_with_votes.html",
        "overperformance": "outputs/interactive/14_online_overperformance_underperformance.html",
        "top12_overlap": "outputs/interactive/14_top12_overlap_by_metric.html",
        "regional_turnout": "outputs/interactive/14_regional_turnout_undervote.html",
        "ncr_alignment": "outputs/interactive/14_ncr_vs_national_rank_alignment.html",
        "ncr_difference": "outputs/interactive/14_ncr_vs_national_rank_difference.html",
        "top_hashtags": "outputs/interactive/14_top_hashtags_pagerank.html",
        "bridge_hashtags": "outputs/interactive/14_top_bridge_hashtags.html",
        "candidate_pairs": "outputs/interactive/14_strongest_candidate_comention_pairs.html",
        "candidate_hashtag_diversity": "outputs/interactive/14_candidate_hashtag_diversity.html",
        "candidate_hashtag_nodes": "outputs/interactive/14_candidate_hashtag_top_nodes.html",
        "phase2a_candidate": "outputs/phase2a_network_visuals/interactive/phase2a_01_candidate_comention_network.html",
        "phase2a_hashtag": "outputs/phase2a_network_visuals/interactive/phase2a_02_hashtag_cooccurrence_network.html",
        "phase2a_bipartite": "outputs/phase2a_network_visuals/interactive/phase2a_03_candidate_hashtag_bipartite_network.html",
        "phase2a_bridge": "outputs/phase2a_network_visuals/interactive/phase2a_04_bridge_node_highlight_network.html",
        "phase2a_overlay": "outputs/phase2a_network_visuals/interactive/phase2a_05_online_outcome_overlay_network.html",
        "story_landing": "outputs/interactive/13_temporal_storytelling_landing.html",
        "animated_candidate_attention": "outputs/interactive/13_animated_candidate_attention_race.html",
        "animated_hashtag_growth": "outputs/interactive/13_animated_hashtag_growth.html",
        "daily_tweet_volume": "outputs/interactive/13_daily_tweet_volume_timeline.html",
        "daily_candidate_pulses": "outputs/interactive/13_animated_daily_candidate_attention_pulses.html",
        "candidate_attention_heatmap": "outputs/interactive/13_candidate_attention_heatmap.html",
    }
    artifact_map = {key: artifact_url(path) for key, path in artifact_map.items()}

    return {
        "cards": cards,
        "top12": _records(top12),
        "top_mentions": _records(top_mentions),
        "top_hash": _records(top_hash),
        "top_candidate_pr": _records(top_candidate_pr),
        "top_bipartite_candidates": _records(top_bipartite_candidates),
        "correlations": _records(correlations.sort_values("spearman_r_vs_votes", ascending=False) if not correlations.empty else correlations),
        "overlap": _records(overlap.sort_values("top12_overlap_count", ascending=False) if not overlap.empty else overlap),
        "overrepresented": _records(over_df.head(8) if not over_df.empty else over_df),
        "underrepresented": _records(over_df.tail(8).sort_values("twitter_mention_count_overperformance") if not over_df.empty else over_df),
        "regional_turnout": _records(regional.sort_values("turnout_rate", ascending=False) if not regional.empty else regional),
        "ncr_table": _records(ncr.sort_values("regional_rank").head(20) if not ncr.empty and "regional_rank" in ncr.columns else ncr.head(20)),
        "artifacts": artifact_map,
    }


def base_context(active: str) -> Dict[str, Any]:
    data = load_dashboard_data()
    return {
        "active": active,
        "cards": data["cards"],
        "artifacts": data["artifacts"],
    }


def overview(request):
    data = load_dashboard_data()
    context = base_context("overview") | {
        "top12": data["top12"][:6],
        "correlations": data["correlations"][:5],
    }
    return render(request, "dashboard/overview.html", context)


def election_outcome(request):
    data = load_dashboard_data()
    context = base_context("election_outcome") | {"top12": data["top12"]}
    return render(request, "dashboard/election_outcome.html", context)


def twitter_analytics(request):
    data = load_dashboard_data()
    context = base_context("twitter_analytics") | {
        "top_mentions": data["top_mentions"],
        "top_hash": data["top_hash"],
    }
    return render(request, "dashboard/twitter_analytics.html", context)


def network_science(request):
    data = load_dashboard_data()
    context = base_context("network_science") | {
        "top_candidate_pr": data["top_candidate_pr"],
        "top_bipartite_candidates": data["top_bipartite_candidates"],
    }
    return render(request, "dashboard/network_science.html", context)


def online_vs_votes(request):
    data = load_dashboard_data()
    context = base_context("online_vs_votes") | {
        "correlations": data["correlations"],
        "overlap": data["overlap"],
        "overrepresented": data["overrepresented"],
        "underrepresented": data["underrepresented"],
    }
    return render(request, "dashboard/online_vs_votes.html", context)


def geography(request):
    data = load_dashboard_data()
    context = base_context("geography") | {
        "regional_turnout": data["regional_turnout"],
        "ncr_table": data["ncr_table"],
    }
    return render(request, "dashboard/geography.html", context)


def storytelling(request):
    context = base_context("storytelling")
    return render(request, "dashboard/storytelling.html", context)


def interpretation(request):
    context = base_context("interpretation")
    return render(request, "dashboard/interpretation.html", context)


def artifact(request, artifact_path: str):
    # Serve only known local output artifacts inside the project folder.
    requested = (settings.BASE_DIR / artifact_path).resolve()
    base = settings.BASE_DIR.resolve()
    try:
        requested.relative_to(base)
    except ValueError as exc:
        raise Http404("Invalid artifact path") from exc
    if not requested.exists() or requested.suffix.lower() not in SAFE_ARTIFACT_SUFFIXES:
        raise Http404("Artifact not found")
    return FileResponse(open(requested, "rb"))
