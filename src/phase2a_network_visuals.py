from pathlib import Path
import math
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    go = None
    PLOTLY_OK = False


def candidate_full_name(x):
    return str(x).replace('Imee R. Marcos', 'Imee Marcos').replace('Ramon, Jr. Bong Revilla', 'Bong Revilla')


def scale_series(s, min_size=10, max_size=55):
    s = pd.Series(s).fillna(0).astype(float)
    if len(s) == 0:
        return np.array([])
    if s.max() == s.min():
        return np.full(len(s), (min_size + max_size) / 2)
    ss = np.sqrt(s - s.min() + 1e-9)
    return min_size + (ss - ss.min()) / (ss.max() - ss.min() + 1e-9) * (max_size - min_size)


def hex_palette(n):
    base = ['#2563eb', '#dc2626', '#f59e0b', '#16a34a', '#9333ea', '#0891b2', '#db2777', '#65a30d', '#7c3aed', '#ea580c', '#0f766e', '#475569']
    return [base[i % len(base)] for i in range(n)]


def assign_communities(G):
    if G.number_of_nodes() == 0:
        return {}
    try:
        communities = list(nx.algorithms.community.greedy_modularity_communities(G, weight='weight'))
        comm_map = {}
        for i, comm in enumerate(communities):
            for node in comm:
                comm_map[node] = i
        return comm_map
    except Exception:
        return {n: 0 for n in G.nodes()}


def build_weighted_graph(edges, source='source', target='target', weight='weight'):
    G = nx.Graph()
    for _, r in edges.iterrows():
        s, t, w = r[source], r[target], float(r[weight])
        if pd.isna(s) or pd.isna(t) or s == t:
            continue
        G.add_edge(str(s), str(t), weight=w)
    return G


def filtered_edges_top(edges, source='source', target='target', weight='weight', top_edges=250, min_weight=None, nodes_keep=None):
    df = edges.copy()
    if min_weight is not None:
        df = df[df[weight] >= min_weight]
    if nodes_keep is not None:
        nodes_keep = set(nodes_keep)
        df = df[df[source].astype(str).isin(nodes_keep) & df[target].astype(str).isin(nodes_keep)]
    return df.sort_values(weight, ascending=False).head(top_edges).reset_index(drop=True)


def make_plotly_network(G, metrics=None, title='', subtitle='', node_metric='pagerank', label_top=15, extra_lookup=None, outfile=None, height=780, seed=42, highlight_nodes=None, winner_lookup=None, overperf_lookup=None):
    if not PLOTLY_OK or G.number_of_nodes() == 0:
        return None
    pos = nx.spring_layout(G, k=1.1 / math.sqrt(max(1, G.number_of_nodes())) * 3.2, iterations=180, seed=seed, weight='weight')
    comm = assign_communities(G)
    communities = sorted(set(comm.values()))
    palette = hex_palette(max(1, len(communities)))
    color_map = {c: palette[i] for i, c in enumerate(communities)}

    weights = [d.get('weight', 1) for _, _, d in G.edges(data=True)]
    max_w = max(weights) if weights else 1
    edge_traces = []
    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        w = d.get('weight', 1)
        width = 0.4 + 5.5 * (math.sqrt(w) / math.sqrt(max_w))
        opacity = 0.10 + 0.35 * (math.sqrt(w) / math.sqrt(max_w))
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None], mode='lines',
            line=dict(width=width, color=f'rgba(100,116,139,{opacity:.3f})'),
            hoverinfo='text', text=f'{candidate_full_name(u)} ↔ {candidate_full_name(v)}<br>Weight: {w:,.0f}',
            showlegend=False
        ))

    metric_lookup = {}
    weighted_degree_lookup = dict(G.degree(weight='weight'))
    degree_lookup = dict(G.degree())
    if metrics is not None and 'node' in metrics.columns:
        metric_lookup = {str(r['node']): r.to_dict() for _, r in metrics.iterrows()}

    nodes = list(G.nodes())
    raw_metric = []
    for n in nodes:
        row = metric_lookup.get(n, {})
        val = row.get(node_metric, None)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            val = weighted_degree_lookup.get(n, 0)
        raw_metric.append(float(val))

    sizes = scale_series(raw_metric, 13, 58)
    ranked_nodes = [n for _, n in sorted(zip(raw_metric, nodes), reverse=True)]
    label_nodes = set(ranked_nodes[:label_top])
    if highlight_nodes:
        label_nodes.update(highlight_nodes)

    xs, ys, texts, hover, colors, line_colors, line_widths = [], [], [], [], [], [], []
    for i, n in enumerate(nodes):
        x, y = pos[n]
        xs.append(x)
        ys.append(y)
        display = candidate_full_name(n)
        texts.append(display if n in label_nodes else '')
        row = metric_lookup.get(n, {})
        comm_i = comm.get(n, 0)
        c = color_map.get(comm_i, '#64748b')
        if overperf_lookup and n in overperf_lookup:
            val = overperf_lookup[n]
            if val > 5:
                c = '#dc2626'
            elif val < -5:
                c = '#2563eb'
            else:
                c = '#94a3b8'
        if highlight_nodes and n in highlight_nodes:
            c = '#f97316'
        colors.append(c)
        if winner_lookup and winner_lookup.get(n, False):
            line_colors.append('#111827')
            line_widths.append(3)
        else:
            line_colors.append('#ffffff')
            line_widths.append(1)
        h = [f'<b>{display}</b>', f'Community: {comm_i}', f'Degree: {degree_lookup.get(n, 0):,.0f}', f'Weighted degree: {weighted_degree_lookup.get(n, 0):,.0f}']
        for key in ['pagerank', 'betweenness_centrality', 'degree_centrality']:
            if key in row:
                try:
                    h.append(f'{key}: {float(row[key]):.5f}')
                except Exception:
                    pass
        if extra_lookup and n in extra_lookup:
            for k, v in extra_lookup[n].items():
                h.append(f'{k}: {v}')
        hover.append('<br>'.join(h))

    node_trace = go.Scatter(
        x=xs, y=ys, mode='markers+text', text=texts, textposition='top center',
        hoverinfo='text', hovertext=hover,
        marker=dict(size=sizes, color=colors, line=dict(color=line_colors, width=line_widths), opacity=0.92),
        textfont=dict(size=11, color='#111827'), showlegend=False
    )
    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title=dict(text=f'<b>{title}</b><br><sup>{subtitle}</sup>', x=0.02, xanchor='left'),
        height=height, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=20, r=20, t=80, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode='closest'
    )
    if outfile:
        fig.write_html(outfile, include_plotlyjs=True, full_html=True)
    return fig


def make_static_network(G, metrics=None, title='', outfile=None, node_metric='pagerank', label_top=15, seed=42, highlight_nodes=None, winner_lookup=None, overperf_lookup=None, figsize=(15, 10)):
    if G.number_of_nodes() == 0:
        return None
    pos = nx.spring_layout(G, k=1.1 / math.sqrt(max(1, G.number_of_nodes())) * 3.2, iterations=180, seed=seed, weight='weight')
    comm = assign_communities(G)
    palette = hex_palette(max(1, len(set(comm.values()))))
    color_map = {c: palette[i] for i, c in enumerate(sorted(set(comm.values())))}
    metric_lookup = {}
    if metrics is not None and 'node' in metrics.columns:
        metric_lookup = {str(r['node']): r.to_dict() for _, r in metrics.iterrows()}
    wdeg = dict(G.degree(weight='weight'))
    raw = []
    for n in G.nodes():
        row = metric_lookup.get(n, {})
        val = row.get(node_metric, wdeg.get(n, 0))
        try:
            raw.append(float(val))
        except Exception:
            raw.append(float(wdeg.get(n, 0)))
    sizes = scale_series(raw, 120, 1900)
    ranked = sorted(G.nodes(), key=lambda n: wdeg.get(n, 0), reverse=True)
    label_nodes = set(ranked[:label_top])
    if highlight_nodes:
        label_nodes.update(highlight_nodes)
    colors, edgecolors, linewidths = [], [], []
    for n in G.nodes():
        c = color_map.get(comm.get(n, 0), '#64748b')
        if overperf_lookup and n in overperf_lookup:
            val = overperf_lookup[n]
            if val > 5:
                c = '#dc2626'
            elif val < -5:
                c = '#2563eb'
            else:
                c = '#94a3b8'
        if highlight_nodes and n in highlight_nodes:
            c = '#f97316'
        colors.append(c)
        if winner_lookup and winner_lookup.get(n, False):
            edgecolors.append('#111827')
            linewidths.append(2.5)
        else:
            edgecolors.append('#ffffff')
            linewidths.append(0.7)
    weights = [d.get('weight', 1) for _, _, d in G.edges(data=True)]
    maxw = max(weights) if weights else 1
    widths = [0.25 + 4.5 * math.sqrt(w) / math.sqrt(maxw) for w in weights]
    plt.figure(figsize=figsize, facecolor='white')
    nx.draw_networkx_edges(G, pos, width=widths, edge_color='#64748b', alpha=0.23)
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors, edgecolors=edgecolors, linewidths=linewidths, alpha=0.94)
    labels = {n: candidate_full_name(n) for n in label_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight='bold')
    plt.title(title, fontsize=18, fontweight='bold', loc='left')
    plt.axis('off')
    plt.tight_layout()
    if outfile:
        plt.savefig(outfile, dpi=220, bbox_inches='tight', facecolor='white')
    plt.close()


def build_phase2a(root=None, verbose=True):
    ROOT = Path(root) if root else Path.cwd()
    if ROOT.name == 'notebooks':
        ROOT = ROOT.parent
    DATA = ROOT / 'data' / 'processed'
    OUT = ROOT / 'outputs' / 'phase2a_network_visuals'
    FIG = OUT / 'figures'
    INT = OUT / 'interactive'
    TAB = OUT / 'tables'
    for p in [OUT, FIG, INT, TAB]:
        p.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if verbose:
            print(msg)

    log('[01/09] Loading Phase 1 tables...')
    candidate_edges = pd.read_csv(DATA / 'candidate_comention_edges.csv')
    candidate_metrics = pd.read_csv(DATA / 'candidate_comention_metrics.csv')
    hashtag_edges = pd.read_csv(DATA / 'hashtag_edges_filtered.csv')
    hashtag_metrics = pd.read_csv(DATA / 'hashtag_metrics.csv')
    ch_edges = pd.read_csv(DATA / 'candidate_hashtag_edges.csv')
    ch_metrics = pd.read_csv(DATA / 'candidate_hashtag_metrics.csv')
    comparison = pd.read_csv(DATA / 'comparison.csv')
    senate = pd.read_csv(DATA / 'senate_national.csv')

    log('[02/09] Building candidate co-mention graph...')
    candidate_edges_top = filtered_edges_top(candidate_edges, top_edges=220, min_weight=10)
    G_cand = build_weighted_graph(candidate_edges_top)
    extra_comp = comparison.set_index('candidate')[['vote_rank', 'total_votes', 'winner_top12', 'twitter_mention_count']].to_dict('index')
    make_plotly_network(G_cand, candidate_metrics, 'Candidate co-mention network', 'Candidates are connected when they appeared in the same tweet. Size = PageRank; color = discourse community.', 'pagerank', 18, extra_lookup=extra_comp, outfile=INT / 'phase2a_01_candidate_comention_network.html', height=820)
    make_static_network(G_cand, candidate_metrics, 'Candidate Co-Mention Network', FIG / 'phase2a_01_candidate_comention_network.png', 'pagerank', 18)
    candidate_edges_top.to_csv(TAB / 'phase2a_candidate_edges_used.csv', index=False)

    log('[03/09] Building hashtag co-occurrence graph...')
    top_hashtags = hashtag_metrics.sort_values('pagerank', ascending=False).head(150)['node'].astype(str).tolist()
    hashtag_edges_top = filtered_edges_top(hashtag_edges, top_edges=650, min_weight=3, nodes_keep=top_hashtags)
    G_hash = build_weighted_graph(hashtag_edges_top)
    make_plotly_network(G_hash, hashtag_metrics, 'Hashtag co-occurrence network', 'Hashtags are connected when they appeared together. Size = PageRank; color = hashtag community.', 'pagerank', 22, outfile=INT / 'phase2a_02_hashtag_cooccurrence_network.html', height=820, seed=17)
    make_static_network(G_hash, hashtag_metrics, 'Hashtag Co-Occurrence Network', FIG / 'phase2a_02_hashtag_cooccurrence_network.png', 'pagerank', 22, seed=17, figsize=(16, 11))
    hashtag_edges_top.to_csv(TAB / 'phase2a_hashtag_edges_used.csv', index=False)

    log('[04/09] Building candidate-hashtag bipartite graph...')
    candidate_rank = ch_metrics[ch_metrics['node_type'] == 'candidate'].sort_values('weighted_degree', ascending=False)
    top_candidates = candidate_rank.head(22)['node'].astype(str).tolist()
    for c in senate.sort_values('vote_rank').head(12)['candidate'].astype(str).tolist():
        if c not in top_candidates:
            top_candidates.append(c)
    ch_sub = ch_edges[ch_edges['candidate'].astype(str).isin(top_candidates)].copy()
    top_h = ch_sub.groupby('hashtag')['weight'].sum().sort_values(ascending=False).head(70).index.astype(str).tolist()
    ch_sub = ch_sub[ch_sub['hashtag'].astype(str).isin(top_h)].sort_values('weight', ascending=False).head(600)
    G_bip = nx.Graph()
    for _, r in ch_sub.iterrows():
        c, h, w = str(r['candidate']), str(r['hashtag']), float(r['weight'])
        G_bip.add_node(c, node_type='candidate')
        G_bip.add_node(h, node_type='hashtag')
        G_bip.add_edge(c, h, weight=w)
    cand_nodes = [n for n, d in G_bip.nodes(data=True) if d.get('node_type') == 'candidate']
    hash_nodes = [n for n, d in G_bip.nodes(data=True) if d.get('node_type') == 'hashtag']
    wdeg_bip = dict(G_bip.degree(weight='weight'))
    cand_nodes = sorted(cand_nodes, key=lambda n: wdeg_bip.get(n, 0), reverse=True)
    hash_nodes = sorted(hash_nodes, key=lambda n: wdeg_bip.get(n, 0), reverse=True)
    pos = {}
    for i, n in enumerate(cand_nodes):
        pos[n] = (0, -i)
    for j, n in enumerate(hash_nodes):
        pos[n] = (1, -j * len(cand_nodes) / max(1, len(hash_nodes)))
    if PLOTLY_OK:
        edge_traces = []
        weights = [d.get('weight', 1) for _, _, d in G_bip.edges(data=True)]
        maxw = max(weights) if weights else 1
        for u, v, d in G_bip.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            w = d.get('weight', 1)
            edge_traces.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None], mode='lines', line=dict(width=0.25 + 4.5 * math.sqrt(w) / math.sqrt(maxw), color='rgba(100,116,139,0.22)'), hoverinfo='text', text=f'{candidate_full_name(u)} — {candidate_full_name(v)}<br>Weight: {w:,.0f}', showlegend=False))
        xs, ys, texts, hovers, sizes, colors, symbols = [], [], [], [], [], [], []
        for n in cand_nodes + hash_nodes:
            x, y = pos[n]
            xs.append(x); ys.append(y)
            sizes.append(12 + 45 * math.sqrt(wdeg_bip.get(n, 1)) / math.sqrt(max(wdeg_bip.values())))
            if n in cand_nodes:
                colors.append('#2563eb'); symbols.append('circle'); texts.append(candidate_full_name(n))
                h = f'<b>{candidate_full_name(n)}</b><br>Type: Candidate<br>Weighted degree: {wdeg_bip.get(n,0):,.0f}<br>Connected hashtags: {G_bip.degree(n):,}'
            else:
                colors.append('#f59e0b'); symbols.append('diamond'); texts.append(n if n in top_h[:18] else '')
                h = f'<b>#{n}</b><br>Type: Hashtag<br>Weighted degree: {wdeg_bip.get(n,0):,.0f}<br>Connected candidates: {G_bip.degree(n):,}'
            hovers.append(h)
        node_trace = go.Scatter(x=xs, y=ys, mode='markers+text', text=texts, textposition='middle right', hoverinfo='text', hovertext=hovers, marker=dict(size=sizes, color=colors, symbol=symbols, line=dict(width=1.3, color='white'), opacity=0.93), textfont=dict(size=10, color='#111827'), showlegend=False)
        fig = go.Figure(data=edge_traces + [node_trace])
        fig.update_layout(title=dict(text='<b>Candidate–hashtag bipartite network</b><br><sup>Blue circles are candidates; orange diamonds are hashtags.</sup>', x=0.02, xanchor='left'), height=1000, plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=20, r=20, t=80, b=20), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), hovermode='closest')
        fig.write_html(INT / 'phase2a_03_candidate_hashtag_bipartite_network.html', include_plotlyjs=True, full_html=True)
    # static bipartite
    weights = [d.get('weight', 1) for _, _, d in G_bip.edges(data=True)]
    maxw = max(weights) if weights else 1
    plt.figure(figsize=(16, 18), facecolor='white')
    for u, v, d in G_bip.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        w = d.get('weight', 1)
        plt.plot([x0, x1], [y0, y1], color='#64748b', alpha=0.20, linewidth=0.2 + 3.5 * math.sqrt(w) / math.sqrt(maxw))
    for n in cand_nodes:
        x, y = pos[n]
        plt.scatter(x, y, s=80 + 1000 * math.sqrt(wdeg_bip.get(n, 1)) / math.sqrt(max(wdeg_bip.values())), c='#2563eb', edgecolor='white', linewidth=1.5, zorder=3)
        plt.text(x - 0.03, y, candidate_full_name(n), ha='right', va='center', fontsize=9, fontweight='bold')
    for n in hash_nodes:
        x, y = pos[n]
        plt.scatter(x, y, s=40 + 700 * math.sqrt(wdeg_bip.get(n, 1)) / math.sqrt(max(wdeg_bip.values())), c='#f59e0b', edgecolor='white', linewidth=1, zorder=3, marker='D')
        if n in top_h[:22]:
            plt.text(x + 0.03, y, n, ha='left', va='center', fontsize=8, fontweight='bold')
    plt.title('Candidate–Hashtag Bipartite Network', fontsize=18, fontweight='bold', loc='left')
    plt.axis('off'); plt.tight_layout(); plt.savefig(FIG / 'phase2a_03_candidate_hashtag_bipartite_network.png', dpi=220, bbox_inches='tight', facecolor='white'); plt.close()
    ch_sub.to_csv(TAB / 'phase2a_candidate_hashtag_edges_used.csv', index=False)

    log('[05/09] Building bridge-node highlight network...')
    bridge_hashes = hashtag_metrics.sort_values('betweenness_centrality', ascending=False).head(15)['node'].astype(str).tolist()
    make_plotly_network(G_hash, hashtag_metrics, 'Bridge hashtag network', 'Highlighted orange nodes have high betweenness centrality: they connect separate hashtag communities.', 'betweenness_centrality', 20, highlight_nodes=bridge_hashes, outfile=INT / 'phase2a_04_bridge_node_highlight_network.html', height=820, seed=17)
    make_static_network(G_hash, hashtag_metrics, 'Bridge Hashtags in the Election Network', FIG / 'phase2a_04_bridge_node_highlight_network.png', 'betweenness_centrality', 20, seed=17, highlight_nodes=bridge_hashes, figsize=(16, 11))
    hashtag_metrics.sort_values('betweenness_centrality', ascending=False).head(25).to_csv(TAB / 'phase2a_top_bridge_hashtags.csv', index=False)

    log('[06/09] Building online-outcome overlay graph...')
    winner_lookup = comparison.set_index('candidate')['winner_top12'].astype(bool).to_dict()
    if 'twitter_mention_count_overperformance' not in comparison.columns and 'twitter_mention_count_rank' in comparison.columns:
        comparison['twitter_mention_count_overperformance'] = comparison['vote_rank'] - comparison['twitter_mention_count_rank']
    over_lookup = comparison.set_index('candidate')['twitter_mention_count_overperformance'].dropna().to_dict() if 'twitter_mention_count_overperformance' in comparison.columns else {}
    make_plotly_network(G_cand, candidate_metrics, 'Online network prominence vs actual Senate outcome', 'Node size = PageRank. Dark border = actual Top 12 winner. Red = online-overrepresented; blue = electorally stronger than online.', 'pagerank', 18, extra_lookup=extra_comp, outfile=INT / 'phase2a_05_online_outcome_overlay_network.html', height=820, winner_lookup=winner_lookup, overperf_lookup=over_lookup)
    make_static_network(G_cand, candidate_metrics, 'Online Network Prominence vs Senate Outcome', FIG / 'phase2a_05_online_outcome_overlay_network.png', 'pagerank', 18, winner_lookup=winner_lookup, overperf_lookup=over_lookup, figsize=(15, 10))

    log('[07/09] Exporting visual support tables...')
    candidate_metrics.sort_values('pagerank', ascending=False).head(25).to_csv(TAB / 'phase2a_top_candidate_pagerank.csv', index=False)

    log('[08/09] Creating master visual explorer page...')
    index_cards = [
        ('Candidate Co-Mention Network', 'phase2a_01_candidate_comention_network.html', 'Shows which candidates were repeatedly discussed together. Node size reflects PageRank; edge thickness reflects co-mention strength.'),
        ('Hashtag Co-Occurrence Network', 'phase2a_02_hashtag_cooccurrence_network.html', 'Shows how hashtags formed a connected election discourse structure. #halalan2025 appears as the key hub.'),
        ('Candidate–Hashtag Bipartite Network', 'phase2a_03_candidate_hashtag_bipartite_network.html', 'Shows how candidates connect to hashtags and issue/campaign labels.'),
        ('Bridge Node Highlight Network', 'phase2a_04_bridge_node_highlight_network.html', 'Highlights high-betweenness hashtags that connect separate discourse communities.'),
        ('Online Prominence vs Senate Outcome', 'phase2a_05_online_outcome_overlay_network.html', 'Compares online network prominence against actual Top 12 Senate outcome.'),
    ]
    html = """<!doctype html><html><head><meta charset='utf-8'><title>Phase 2A Network Science Visual Explorer</title>
<style>
body{font-family:Inter,Segoe UI,Arial,sans-serif;margin:0;background:#0f172a;color:#e5e7eb;} header{padding:36px 44px;background:linear-gradient(135deg,#111827,#1e3a8a);} h1{margin:0;font-size:38px;} p{line-height:1.55;color:#cbd5e1;} .wrap{padding:28px 44px;} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px;} .card{background:#111827;border:1px solid #334155;border-radius:18px;padding:22px;box-shadow:0 16px 40px rgba(0,0,0,.28);} .card h2{margin:0 0 8px;font-size:22px;color:white}.btn{display:inline-block;margin-top:12px;padding:10px 14px;border-radius:999px;background:#f59e0b;color:#111827;text-decoration:none;font-weight:700}.note{background:#020617;border-left:5px solid #f59e0b;padding:16px 20px;border-radius:12px;margin:20px 0 28px;} .footer{padding:24px 44px;color:#94a3b8;font-size:13px;}
</style></head><body><header><h1>Phase 2A: Network Science Visual Explorer</h1><p>Interactive node-link visualizations for the Philippine Election 2025 Twitter/X network study.</p></header><main class='wrap'><div class='note'><b>How to read these graphs:</b> nodes are candidates, hashtags, or users; lines are relationships; larger nodes are more central; thicker lines are stronger relationships; colors indicate communities or analytic categories.</div><div class='grid'>"""
    for title, file, desc in index_cards:
        html += f"<div class='card'><h2>{title}</h2><p>{desc}</p><a class='btn' href='{file}'>Open interactive graph</a></div>"
    html += "</div></main><div class='footer'>Generated by Phase 2A Network Science Visual Explorer.</div></body></html>"
    (INT / 'phase2a_network_visual_explorer.html').write_text(html, encoding='utf-8')
    pd.DataFrame([{'visual': t, 'interactive_file': file, 'description': d} for t, file, d in index_cards]).to_csv(TAB / 'phase2a_visual_index.csv', index=False)

    log('[09/09] Phase 2A complete.')
    return {
        'explorer': str(INT / 'phase2a_network_visual_explorer.html'),
        'interactive_dir': str(INT),
        'figures_dir': str(FIG),
        'tables_dir': str(TAB),
    }


if __name__ == '__main__':
    print(build_phase2a(Path(__file__).resolve().parents[1]))
