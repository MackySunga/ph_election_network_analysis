"""
Utility functions for the Philippine Election 2025 Network Science project.
Designed for Jupyter notebooks in ../notebooks.
"""
from __future__ import annotations

import itertools
import json
import math
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
import networkx as nx

HASHTAG_RE = re.compile(r"#([A-Za-z0-9_]+)")
MENTION_RE = re.compile(r"@([A-Za-z0-9_]+)")
URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", flags=re.IGNORECASE)


def project_root_from_notebook() -> Path:
    """Return project root when called from notebooks/ or project root."""
    cwd = Path.cwd()
    if cwd.name == "notebooks":
        return cwd.parent
    if (cwd / "data").exists() and (cwd / "src").exists():
        return cwd
    # Fallback for unusual environments
    return cwd


def ensure_dirs(root: Path) -> Dict[str, Path]:
    paths = {
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "figures": root / "outputs" / "figures",
        "interactive": root / "outputs" / "interactive",
        "tables": root / "outputs" / "tables",
        "networks": root / "outputs" / "networks",
        "report_assets": root / "outputs" / "report_assets",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    s = str(value)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"https?://\S+|www\.\S+", " ", s)
    s = re.sub(r"[^a-z0-9#@_\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_hashtags(text: Any) -> List[str]:
    return sorted(set([h.lower() for h in HASHTAG_RE.findall(str(text or ""))]))


def extract_mentions(text: Any) -> List[str]:
    return sorted(set([m.lower() for m in MENTION_RE.findall(str(text or ""))]))


def extract_urls(text: Any) -> List[str]:
    return URL_RE.findall(str(text or ""))


def domain_from_url(url: str) -> str:
    url = url.lower().strip()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.split("/")[0]


def extract_domains(text: Any) -> List[str]:
    return sorted(set(domain_from_url(u) for u in extract_urls(text)))


def is_candidate_col(col: str) -> bool:
    return bool(re.match(r"^\d+\.\s", str(col)))


def parse_candidate_column(col: str) -> Dict[str, str]:
    """Parse candidate column like '5. AQUINO, BAM (KNP)' into display fields."""
    raw = str(col).strip()
    num_match = re.match(r"^(\d+)\.\s*(.*)$", raw)
    ballot_no = num_match.group(1) if num_match else ""
    body = num_match.group(2) if num_match else raw
    party_match = re.search(r"\(([^)]+)\)\s*$", body)
    party = party_match.group(1).strip() if party_match else ""
    name_part = re.sub(r"\s*\([^)]*\)\s*$", "", body).strip()
    name_part = re.sub(r"\s+", " ", name_part)
    if "," in name_part:
        last, first = name_part.split(",", 1)
        last = re.sub(r"\s+", " ", last).strip()
        first = re.sub(r"\s+", " ", first).strip()
        # Some candidate labels already include the surname in the given-name field,
        # e.g., "GO, BONG GO". Avoid producing "Bong Go Go".
        if normalize_text(first).endswith(normalize_text(last)):
            display = first
        else:
            display = f"{first} {last}".strip()
    else:
        first = name_part
        last = ""
        display = name_part
    display = re.sub(r"\s+", " ", display).strip().title()
    # Clean common title artifacts for nicer display
    display = display.replace("AtTy", "Atty").replace("Jr.", "Jr.")
    return {"ballot_no": ballot_no, "candidate_column": raw, "candidate": display, "party": party, "last_name": last.title(), "first_name": first.title()}


def get_candidate_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if is_candidate_col(c)]


def build_candidate_reference(senate_df: pd.DataFrame) -> pd.DataFrame:
    rows = [parse_candidate_column(c) for c in get_candidate_columns(senate_df)]
    ref = pd.DataFrame(rows)
    return ref


def senate_national_results(senate_df: pd.DataFrame) -> pd.DataFrame:
    candidate_cols = get_candidate_columns(senate_df)
    ref = build_candidate_reference(senate_df)
    totals = senate_df[candidate_cols].apply(pd.to_numeric, errors="coerce").sum().reset_index()
    totals.columns = ["candidate_column", "total_votes"]
    out = ref.merge(totals, on="candidate_column", how="left")
    out["vote_rank"] = out["total_votes"].rank(method="min", ascending=False).astype(int)
    total_valid_votes = senate_df.get("validVotes", pd.Series(dtype=float))
    total_valid = pd.to_numeric(total_valid_votes, errors="coerce").sum() if len(total_valid_votes) else np.nan
    out["vote_share_of_valid_votes"] = out["total_votes"] / total_valid if total_valid and total_valid > 0 else np.nan
    out["winner_top12"] = out["vote_rank"] <= 12
    return out.sort_values("vote_rank")


def custom_candidate_variants(candidate: str) -> List[str]:
    """Manual variants for high-profile Philippine senatorial candidates and common nicknames."""
    c = normalize_text(candidate)
    custom = {
        "bam aquino": ["bam aquino", "bamaquino", "#bamaquino", "sen bam", "senator bam"],
        "bong go": ["bong go", "bonggo", "#bonggo", "sen bong go"],
        "bato dela rosa": ["bato dela rosa", "batodelarosa", "#batodelarosa", "bato", "ronald dela rosa"],
        "erwin tulfo": ["erwin tulfo", "erwintulfo", "#erwintulfo"],
        "kiko pangilinan": ["kiko pangilinan", "kikopangilinan", "#kikopangilinan", "francis pangilinan"],
        "rodante marcoleta": ["rodante marcoleta", "marcoleta", "#marcoleta"],
        "ping lacson": ["ping lacson", "pinglacson", "#pinglacson", "panfilo lacson"],
        "tito sotto": ["tito sotto", "titosotto", "#titosotto", "vicente sotto"],
        "pia cayetano": ["pia cayetano", "piacayetano", "#piacayetano"],
        "camille villar": ["camille villar", "camillevillar", "#camillevillar"],
        "lito lapid": ["lito lapid", "litolapid", "#litolapid"],
        "imee marcos": ["imee marcos", "imeemarcos", "#imeemarcos"],
        "benhur abalos": ["benhur abalos", "benhurabalos", "#benhurabalos"],
        "abby binay": ["abby binay", "abbybinay", "#abbybinay"],
        "manny pacman pacquiao": ["manny pacquiao", "pacquiao", "mannypacquiao", "#mannypacquiao", "pacman"],
        "manny pacquiao": ["manny pacquiao", "pacquiao", "mannypacquiao", "#mannypacquiao", "pacman"],
        "doc willie ong": ["doc willie ong", "willie ong", "willieong", "#willieong"],
        "bong revilla ramon jr.": ["bong revilla", "ramon revilla", "bongrevilla", "#bongrevilla"],
        "willie wil revillame": ["willie revillame", "revillame", "willie wil", "#willierevillame"],
        "apollo quiboloy": ["apollo quiboloy", "quiboloy", "#quiboloy"],
        "francis tol tolentino": ["francis tolentino", "tolentino", "francis tol", "#francistolentino"],
        "ben bitag tulfo": ["ben tulfo", "ben bitag tulfo", "bentulfo", "#bentulfo"],
    }
    return custom.get(c, [])


def build_candidate_dictionary(candidate_ref: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in candidate_ref.iterrows():
        cand = str(r["candidate"])
        norm = normalize_text(cand)
        tokens = [t for t in norm.split() if t]
        variants = set()
        variants.add(norm)
        variants.add("".join(tokens))
        variants.add("#" + "".join(tokens))
        simplified_tokens = [t for t in tokens if len(t) > 1 and t not in {"jr", "sr", "atty", "doc"}]
        if len(simplified_tokens) >= 2:
            simplified = " ".join([simplified_tokens[0], simplified_tokens[-1]])
            variants.add(simplified)
            variants.add("".join([simplified_tokens[0], simplified_tokens[-1]]))
            variants.add("#" + simplified_tokens[0] + simplified_tokens[-1])
        if len(tokens) >= 2:
            variants.add(" ".join(tokens[:2]))
            variants.add(" ".join([tokens[0], tokens[-1]]))
            variants.add("#" + tokens[0] + tokens[-1])
        # Last-name-only is risky; include only if length >= 5 and not too generic.
        if tokens:
            last = tokens[-1]
            if len(last) >= 5 and last not in {"villar", "ramos", "castro", "lapid", "sotto"}:
                variants.add(last)
        for v in custom_candidate_variants(norm):
            variants.add(normalize_text(v))
        for v in sorted(variants):
            if v:
                rows.append({
                    "candidate": cand,
                    "candidate_column": r.get("candidate_column", ""),
                    "party": r.get("party", ""),
                    "variant": v,
                    "variant_regex": r"(?<![a-z0-9_])" + re.escape(v).replace("\\#", "#") + r"(?![a-z0-9_])",
                    "variant_length": len(v),
                })
    out = pd.DataFrame(rows).drop_duplicates(["candidate", "variant"])
    return out.sort_values(["candidate", "variant_length"], ascending=[True, False]).reset_index(drop=True)


def detect_candidates(text: Any, candidate_dict: pd.DataFrame) -> List[str]:
    norm = normalize_text(text)
    found = set()
    # Match longer variants first to reduce false positives.
    for _, row in candidate_dict.sort_values("variant_length", ascending=False).iterrows():
        pattern = row["variant_regex"]
        if re.search(pattern, norm):
            found.add(row["candidate"])
    return sorted(found)


def detect_topics(text: Any, topic_dict: Optional[Dict[str, List[str]]] = None) -> List[str]:
    if topic_dict is None:
        topic_dict = default_topic_dictionary()
    norm = normalize_text(text)
    found = []
    for topic, terms in topic_dict.items():
        for term in terms:
            term_norm = normalize_text(term)
            if re.search(r"(?<![a-z0-9_])" + re.escape(term_norm) + r"(?![a-z0-9_])", norm):
                found.append(topic)
                break
    return sorted(set(found))


def default_topic_dictionary() -> Dict[str, List[str]]:
    return {
        "Election administration": ["comelec", "halalan", "eleksyon", "election", "vote", "voters", "ballot", "precinct"],
        "Senate race": ["senate", "senator", "senatorial", "senado", "senador"],
        "Governance and corruption": ["corruption", "kurakot", "corrupt", "accountability", "good governance"],
        "Political dynasty": ["dynasty", "political dynasty", "dinastiya"],
        "Economy and prices": ["inflation", "presyo", "mahal", "trabaho", "jobs", "economy", "ekonomiya", "sahod"],
        "Education": ["education", "edukasyon", "school", "teacher", "teachers", "student"],
        "Health": ["health", "kalusugan", "hospital", "doctor", "philhealth", "medical"],
        "Foreign policy and security": ["china", "west philippine sea", "wps", "security", "defense", "territory"],
        "Disinformation and media": ["fake news", "disinformation", "misinformation", "propaganda", "media", "troll"],
        "Campaign and endorsement": ["campaign", "rally", "endorse", "endorsement", "support", "iboto", "vote for"],
    }


def make_pair_edges(list_series: Iterable[List[str]], source_col="source", target_col="target") -> pd.DataFrame:
    counter = Counter()
    for items in list_series:
        if not isinstance(items, (list, tuple, set)):
            continue
        items = sorted(set([str(x).strip() for x in items if str(x).strip()]))
        if len(items) < 2:
            continue
        for a, b in itertools.combinations(items, 2):
            counter[(a, b)] += 1
    rows = [{source_col: a, target_col: b, "weight": w} for (a, b), w in counter.items()]
    return pd.DataFrame(rows).sort_values("weight", ascending=False).reset_index(drop=True) if rows else pd.DataFrame(columns=[source_col, target_col, "weight"])


def make_bipartite_edges(left_series: Iterable[List[str]], right_series: Iterable[List[str]], left_name="candidate", right_name="hashtag") -> pd.DataFrame:
    counter = Counter()
    for left_items, right_items in zip(left_series, right_series):
        if not isinstance(left_items, (list, tuple, set)) or not isinstance(right_items, (list, tuple, set)):
            continue
        left_items = sorted(set([str(x).strip() for x in left_items if str(x).strip()]))
        right_items = sorted(set([str(x).strip() for x in right_items if str(x).strip()]))
        for l in left_items:
            for r in right_items:
                counter[(l, r)] += 1
    rows = [{left_name: a, right_name: b, "weight": w} for (a, b), w in counter.items()]
    return pd.DataFrame(rows).sort_values("weight", ascending=False).reset_index(drop=True) if rows else pd.DataFrame(columns=[left_name, right_name, "weight"])


def graph_from_edges(edges: pd.DataFrame, source="source", target="target", weight="weight", directed=False) -> nx.Graph:
    G = nx.DiGraph() if directed else nx.Graph()
    for _, row in edges.iterrows():
        if pd.isna(row[source]) or pd.isna(row[target]):
            continue
        w = float(row.get(weight, 1))
        if G.has_edge(row[source], row[target]):
            G[row[source]][row[target]]["weight"] += w
        else:
            G.add_edge(row[source], row[target], weight=w)
    return G


def compute_network_metrics(G: nx.Graph) -> pd.DataFrame:
    if G.number_of_nodes() == 0:
        return pd.DataFrame()
    nodes = list(G.nodes())
    weighted_degree = dict(G.degree(weight="weight"))
    degree = dict(G.degree())
    metrics = pd.DataFrame({"node": nodes})
    metrics["degree"] = metrics["node"].map(degree).fillna(0)
    metrics["weighted_degree"] = metrics["node"].map(weighted_degree).fillna(0)
    # Centralities. Betweenness can be expensive; approximate for large graphs.
    try:
        metrics["degree_centrality"] = metrics["node"].map(nx.degree_centrality(G)).fillna(0)
    except Exception:
        metrics["degree_centrality"] = np.nan
    try:
        if G.number_of_nodes() > 1500:
            k = min(500, G.number_of_nodes())
            bc = nx.betweenness_centrality(G, k=k, weight="weight", seed=42)
        else:
            bc = nx.betweenness_centrality(G, weight="weight")
        metrics["betweenness_centrality"] = metrics["node"].map(bc).fillna(0)
    except Exception:
        metrics["betweenness_centrality"] = np.nan
    try:
        pr = nx.pagerank(G, weight="weight")
        metrics["pagerank"] = metrics["node"].map(pr).fillna(0)
    except Exception:
        metrics["pagerank"] = np.nan
    try:
        if not G.is_directed() and G.number_of_nodes() <= 5000:
            cc = nx.closeness_centrality(G)
            metrics["closeness_centrality"] = metrics["node"].map(cc).fillna(0)
        else:
            metrics["closeness_centrality"] = np.nan
    except Exception:
        metrics["closeness_centrality"] = np.nan
    try:
        if not G.is_directed() and G.number_of_nodes() <= 2000:
            ev = nx.eigenvector_centrality(G, weight="weight", max_iter=1000)
            metrics["eigenvector_centrality"] = metrics["node"].map(ev).fillna(0)
        else:
            metrics["eigenvector_centrality"] = np.nan
    except Exception:
        metrics["eigenvector_centrality"] = np.nan
    return metrics.sort_values(["pagerank", "weighted_degree"], ascending=False).reset_index(drop=True)


def detect_communities(G: nx.Graph) -> Dict[Any, int]:
    if G.number_of_nodes() == 0:
        return {}
    H = G.to_undirected() if G.is_directed() else G
    try:
        import community as community_louvain
        part = community_louvain.best_partition(H, weight="weight", random_state=42)
        return part
    except Exception:
        try:
            comms = nx.algorithms.community.greedy_modularity_communities(H, weight="weight")
            return {node: i for i, comm in enumerate(comms) for node in comm}
        except Exception:
            return {node: 0 for node in H.nodes()}


def network_summary(G: nx.Graph, name: str = "network") -> pd.DataFrame:
    if G.number_of_nodes() == 0:
        return pd.DataFrame([{"network": name, "nodes": 0, "edges": 0}])
    H = G.to_undirected() if G.is_directed() else G
    components = list(nx.connected_components(H)) if H.number_of_nodes() else []
    summary = {
        "network": name,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": nx.density(G),
        "average_degree": np.mean([d for _, d in G.degree()]) if G.number_of_nodes() else 0,
        "average_weighted_degree": np.mean([d for _, d in G.degree(weight="weight")]) if G.number_of_nodes() else 0,
        "connected_components": len(components),
        "largest_component_size": max((len(c) for c in components), default=0),
        "average_clustering": nx.average_clustering(H, weight="weight") if H.number_of_nodes() > 1 else 0,
    }
    return pd.DataFrame([summary])


def save_pyvis_network(G: nx.Graph, out_file: Path, title: str = "Network", node_metrics: Optional[pd.DataFrame] = None, max_nodes: int = 800):
    try:
        from pyvis.network import Network
    except Exception as e:
        print(f"pyvis is not installed. Skipping interactive network. Error: {e}")
        return None
    H = G.copy()
    if H.number_of_nodes() > max_nodes:
        weighted = dict(H.degree(weight="weight"))
        keep = sorted(weighted, key=weighted.get, reverse=True)[:max_nodes]
        H = H.subgraph(keep).copy()
    metric_map = {}
    if node_metrics is not None and not node_metrics.empty and "node" in node_metrics.columns:
        metric_map = node_metrics.set_index("node").to_dict(orient="index")
    net = Network(height="760px", width="100%", bgcolor="#111827", font_color="white", notebook=False, directed=G.is_directed())
    net.barnes_hut(gravity=-30000, central_gravity=0.3, spring_length=150, spring_strength=0.02, damping=0.09)
    communities = detect_communities(H)
    for n in H.nodes():
        m = metric_map.get(n, {})
        size = 8 + min(40, math.sqrt(float(m.get("weighted_degree", H.degree(n, weight="weight")) or 0)))
        title_html = f"<b>{n}</b><br>degree: {H.degree(n)}<br>weighted degree: {H.degree(n, weight='weight'):.0f}<br>community: {communities.get(n, 0)}"
        net.add_node(n, label=str(n)[:28], title=title_html, value=size, group=int(communities.get(n, 0)))
    for u, v, d in H.edges(data=True):
        w = float(d.get("weight", 1))
        net.add_edge(u, v, value=max(1, math.log1p(w)), title=f"weight: {w:.0f}")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(out_file))
    return out_file


def safe_to_excel(dfs: Dict[str, pd.DataFrame], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in dfs.items():
            safe_sheet = re.sub(r"[^A-Za-z0-9_ ]", "", sheet)[:31]
            df.to_excel(writer, sheet_name=safe_sheet, index=False)
    return path


def save_plotly(fig, html_path: Path, png_path: Optional[Path] = None):
    html_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(html_path))
    if png_path is not None:
        try:
            png_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_image(str(png_path), scale=2)
        except Exception as e:
            print(f"PNG export skipped. Install kaleido to enable PNG export. Details: {e}")
    return html_path


def add_rank_columns(df: pd.DataFrame, columns: List[str], higher_is_better=True, suffix="rank") -> pd.DataFrame:
    out = df.copy()
    for c in columns:
        if c in out.columns:
            out[f"{c}_{suffix}"] = out[c].rank(method="min", ascending=not higher_is_better)
    return out

import ast

def parse_list_value(x: Any) -> List[str]:
    if isinstance(x, list):
        return x
    if pd.isna(x):
        return []
    s = str(x)
    try:
        val = ast.literal_eval(s)
        if isinstance(val, list):
            return val
    except Exception:
        pass
    if s.strip() == "":
        return []
    return [i.strip() for i in s.split("|") if i.strip()]


def parse_list_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].apply(parse_list_value)
    return out
