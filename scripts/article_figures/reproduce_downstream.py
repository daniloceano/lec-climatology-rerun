"""Gate-first reproduction of article Figures 9–16 using archived scripts.

No changes to canonical phase EOFs. Run with --legacy-only to stop at the gate.
The original tree is read-only; numerical evidence goes to a new subdirectory.
"""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import xarray as xr
from PIL import Image
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from scripts.article_figures import common as c
from scripts.article_figures.legacy_source import load_definitions
from scripts.article_figures import density_color_scale as colors
from scripts.article_figures.phase_eofs import read_phase_product, load_pinned_phase_inputs
from scripts.article_figures import generate_corrected_article as render

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT.parent / 'energetic_patterns_cyclones_south_atlantic'
TOTAL = ARCHIVE / 'csv_eofs_energetics_with_track/Total'
PCS = [f'PC{i}' for i in range(1, 9)]
GATE = ROOT / 'results/original/article/reproduction_gate'
CORRECTED = ROOT / 'results/corrected/article/validated_downstream'
PYEOF = Path('/Users/danilocoutodesouza/anaconda3/envs/data/lib/python3.12/site-packages/pyEOF/pyEOF.py')
HISTORY = PYEOF.parents[4] / 'conda-meta/history'


def normalized_columns(frame):
    return frame.rename(columns=lambda s: s + ' (finite diff.)' if s.startswith('∂') and 'finite diff' not in s else s)


def total_pyeof(cache, reference):
    """pyEOF default internal population scaling; pcs(s=2), eofs(s=2).

    common.compute_eof uses sample-standardized correlation eigenvalues mu.
    pyEOF's internal StandardScaler gives lambda = mu*N/(N-1).
    Thus PC(s=2) = unit_sample_PC * lambda; EOF(s=2) = V*sqrt(lambda).
    Reference participates ONLY in permutation/sign, never in scale fitting.
    """
    cache = cache.assign(track_id=pd.to_numeric(cache.track_id, errors='raise').astype('int64'))
    per_track = cache.groupby('track_id')[c.EOF_TERMS].mean()
    ids, loading, unit, ev = c.compute_eof(per_track, c.EOF_TERMS)
    eigenvalues = ev * len(c.EOF_TERMS) * len(ids) / (len(ids) - 1)
    raw_loading = loading * np.sqrt(len(ids) / (len(ids) - 1))
    raw_pc = unit * eigenvalues
    aligned, scores, variance, rank, corr = c.align_eofs(reference, raw_loading, raw_pc, ev)
    signs = np.sign(np.sum(aligned * raw_loading[rank - 1], axis=1)).astype(int)
    mapping = pd.DataFrame(dict(reference_eof=range(1, 9), corrected_raw_rank=rank,
                                pattern_correlation=corr, sign_alignment=signs,
                                explained_variance=variance, eigenvalue=eigenvalues[rank - 1]))
    return (pd.DataFrame(scores, columns=PCS).assign(track_id=ids.to_numpy()),
            pd.DataFrame(aligned, columns=c.EOF_TERMS), mapping)


def memberships(frame):
    return set(map(tuple, frame[['track_id', 'sign', 'dominant_eof']].to_numpy()))


def intense_ids(tracks, ids):
    maximum = tracks.groupby('track_id').vor42.max()
    threshold = float(maximum.quantile(.9))
    return sorted(set(maximum[maximum >= threshold].index) & set(ids)), threshold


def cluster(scores, ids, *, n_init='auto'):
    selected = scores[scores.track_id.isin(ids)].copy()
    scaler = StandardScaler()
    model = KMeans(n_clusters=4, random_state=42, n_init=n_init,
                   init='k-means++', algorithm='lloyd', max_iter=300, tol=1e-4)
    selected['cluster'] = model.fit_predict(scaler.fit_transform(selected[PCS])) + 1
    centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=PCS)
    centers.insert(0, 'cluster', range(1, 5))
    return selected, centers, model.cluster_centers_, scaler


def match_labels(actual, expected):
    joined = expected[['track_id', 'cluster']].merge(actual[['track_id', 'cluster']], on='track_id', suffixes=('_reference', '_raw'), validate='one_to_one')
    if len(joined) != len(expected) or len(joined) != len(actual):
        raise ValueError('cluster ID populations differ')
    table = pd.crosstab(joined.cluster_reference, joined.cluster_raw).reindex(index=range(1, 5), columns=range(1, 5), fill_value=0)
    row, col = linear_sum_assignment(-table.to_numpy())
    mapping = {int(k+1): int(v+1) for k,v in zip(col,row)}
    mismatch = int((joined.cluster_raw.map(mapping) != joined.cluster_reference).sum())
    return mapping, mismatch, table


def figure12_tables(cache, clusters, centers, loadings):
    per_track = cache.groupby('track_id')[c.EOF_TERMS].mean()
    # plot_LEC_std.py: total is the unweighted mean of phase means/phase SDs.
    # This deliberately differs from the climatological mean used for B–E.
    mean_a = cache.groupby('period')[c.EOF_TERMS].mean().mean()
    std_a = cache.groupby('period')[c.EOF_TERMS].std().mean()
    mean_cluster = centers.sort_values('cluster')[PCS].to_numpy() @ loadings[c.EOF_TERMS].to_numpy() + per_track.mean().to_numpy()
    rows = [dict(panel='A', cluster=0, term=t, mean=mean_a[t], std=std_a[t], n=per_track.shape[0]) for t in c.EOF_TERMS]
    for k in range(1, 5):
        block = per_track.loc[clusters.loc[clusters.cluster.eq(k), 'track_id']]
        for j, term in enumerate(c.EOF_TERMS):
            rows.append(dict(panel=chr(65+k), cluster=k, term=term, mean=mean_cluster[k-1,j], std=block[term].std(), n=len(block)))
    return pd.DataFrame(rows)


def original_statistics(script, tracks, clusters):
    """Execute original Figure 14 preprocessing verbatim, stopping before plots."""
    tree = ast.parse(script.read_text())
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Tuple) and any(isinstance(x, ast.Name) and x.id == 'fig' for x in t.elts) for t in node.targets):
            break
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'clusters_df', 'tracks_df'} for t in node.targets):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'read_csv':
                continue
        nodes.append(node)
    ns = dict(clusters_df=clusters.assign(cluster=clusters.cluster-1).copy(), tracks_df=tracks.copy())
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(script), 'exec'), ns)
    return ns


def phase_synthesis_inputs():
    loadings, _ = read_phase_product(ROOT)
    return loadings.query('version == "after" and reference_eof <= 4').copy()


class GateFailure(RuntimeError):
    pass


class Evidence:
    def __init__(self, output):
        self.output = output
        output.mkdir(parents=True, exist_ok=True)
        self.checks = []
        self.sources = {}

    def source(self, path):
        path = Path(path).resolve()
        self.sources[str(path)] = c.sha256_file(path)
        return path

    def table(self, name, frame):
        frame.to_csv(self.output / name, index=False, float_format='%.17g')

    def check(self, name, passed, evidence):
        self.checks.append(dict(item=name, passed=bool(passed), evidence=evidence))
        self.save()
        print(f'{name}: {"PASS" if passed else "FAIL"} {evidence}', flush=True)
        if not passed:
            raise GateFailure(f'{name}: {evidence}')

    def save(self):
        doc = dict(checks=self.checks, sources=self.sources, sklearn_version=sklearn.__version__,
                   repo_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   wrapper_sha256=c.sha256_file(Path(__file__)),
                   toolkit_commit=json.loads((ROOT/'results/comparison/article/provenance.json').read_text())['toolkit_commit'])
        (self.output/'manifest.json').write_text(json.dumps(doc, indent=2)+'\n')


def validate_legacy(legacy, tracks, root, evidence):
    ref = normalized_columns(pd.read_csv(evidence.source(TOTAL/'eofs.csv')))[c.EOF_TERMS]
    archived_pc = pd.read_csv(evidence.source(TOTAL/'pcs.csv'))
    scores, loadings, mapping = total_pyeof(legacy, ref.to_numpy())
    # Preserve archived input order: KMeans RNG samples rows, not track IDs.
    scores = scores.set_index('track_id').loc[archived_pc.track_id].reset_index()
    error = float(np.max(np.abs(scores[PCS].to_numpy()-archived_pc[PCS].to_numpy())))
    evidence.table('pc_standard_deviations.csv', pd.DataFrame(dict(pc=PCS, reproduced=scores[PCS].std(), archived=archived_pc[PCS].std())).reset_index(drop=True))
    evidence.table('eof_scores_total.csv', scores)
    evidence.check('PCs legacy', error < 1e-9, dict(max_absolute_error=error, convention='pcs(s=2), lambda=24*EV*N/(N-1)', n=len(scores)))
    evidence.check('EOF loadings legacy', np.allclose(loadings, ref, atol=1e-11, rtol=0), dict(max_absolute_error=float(np.max(np.abs(loadings.to_numpy()-ref.to_numpy())))))
    assignments = c.assign_published_eof_extremes(scores)
    expected = pd.concat([pd.read_csv(evidence.source(TOTAL/f'pcs_with_dominant_eof_{suffix}.csv')).assign(sign=sign) for sign,suffix in [('positive','q90'),('negative','q10')]])
    evidence.table('eof_extreme_assignments.csv', assignments)
    evidence.check('EOF +/- assignments', memberships(assignments)==memberships(expected), dict(symmetric_difference=len(memberships(assignments)^memberships(expected)), rows=len(assignments)))
    archived_clusters = pd.read_csv(evidence.source(root/'figures/eof_clusters_intense/pcs_with_clusters.csv'))
    archived_clusters['cluster'] += 1
    ids, threshold = intense_ids(tracks, scores.track_id)
    evidence.table('intense_ids.csv', pd.DataFrame(dict(track_id=ids)))
    evidence.check('intense selection', set(ids)==set(archived_clusters.track_id) and len(ids)==679, dict(threshold=threshold, n=len(ids), threshold_population=tracks.track_id.nunique()))
    ten, _, _, _ = cluster(scores, ids, n_init=10)
    _, ten_diff, ten_table = match_labels(ten, archived_clusters)
    evidence.table('n_init_10_contingency.csv', ten_table.reset_index())
    clustered, centers, standardized, scaler = cluster(scores, ids)
    label_map, mismatch, contingency = match_labels(clustered, archived_clusters)
    evidence.table('cluster_contingency.csv', contingency.reset_index())
    evidence.check('4-cluster assignments', mismatch==0, dict(mismatches=mismatch, n_init_10_mismatches=ten_diff, n_init='auto', effective_n_init=1, environment_evidence=str(HISTORY), label_map=label_map))
    order = [next(k for k,v in label_map.items() if v==i)-1 for i in range(1,5)]
    clustered['cluster'] = clustered.cluster.map(label_map)
    centers = centers.iloc[order].copy(); centers['cluster'] = range(1,5)
    standardized = standardized[order]
    archived_centers = pd.read_csv(evidence.source(root/'figures/eof_clusters_intense/cluster_centroids.csv'))
    center_error = float(np.max(np.abs(centers[PCS].to_numpy()-archived_centers[PCS].to_numpy())))
    evidence.check('cluster centroids', center_error < 1e-9, dict(max_absolute_error=center_error))
    evidence.table('cluster_assignments.csv', clustered)
    evidence.table('cluster_centers.csv', centers)
    f12 = figure12_tables(legacy, clustered, centers, loadings)
    evidence.table('figure12_values.csv', f12)
    # Published annotations read directly from the frozen Figure 12 PNG, at 0.01 precision.
    annotations = pd.read_csv(evidence.source(ROOT/'tests/fixtures/figure12_published_annotations.csv'))
    joined = annotations.merge(f12, on=['panel','term'], suffixes=('_published','_reproduced'), validate='one_to_one')
    delta = np.abs(joined[['mean_published','std_published']].to_numpy()-joined[['mean_reproduced','std_reproduced']].to_numpy())
    evidence.check('Figure 12 logic', len(joined)==len(annotations) and np.max(delta)<.00500001, dict(annotation_pairs=len(joined), max_rounding_error=float(np.max(delta)), panel_A='all systems, equal phase means and mean phase SD', panels_BE='centroid @ EOF(s=2) + per-cyclone climatology; member SD'))
    density_script = evidence.source(root/'eof_export_density_clusters.py')
    density_fn = load_definitions(density_script).compute_density
    selected_tracks = tracks[tracks.track_id.isin(ids)]
    months = selected_tracks.date.dt.to_period('M').nunique()
    density_rows=[]
    for k in range(1,5):
        subset=tracks[tracks.track_id.isin(clustered.loc[clustered.cluster.eq(k),'track_id'])]
        values,lon,lat=density_fn(subset,months)
        with xr.open_dataarray(evidence.source(root/f'track_density_clusters/track_density_cluster_{k}.nc')) as saved:
            err=float(np.max(np.abs(values-saved.values)))
            ok=np.array_equal(lon,saved.lon) and np.array_equal(lat,saved.lat) and np.allclose(values,saved.values,atol=1e-10,rtol=0)
        density_rows.append(dict(cluster=k, months=months, track_rows=len(subset), max_absolute_error=err))
        evidence.check(f'Figure 13 density cluster {k}',ok,density_rows[-1])
    evidence.table('figure13_density_validation.csv',pd.DataFrame(density_rows))
    evidence.check('Figure 13 logic',True,dict(months=months,bandwidth=.05,metric='haversine',unit='track positions / 10^6 km^2 / month'))
    first=tracks.groupby('track_id').first().reset_index()
    first['season']=first.date.dt.month.map(c.season_of_month)
    ns=original_statistics(evidence.source(root/'eof_cluster_statistics.py'), tracks, clustered)
    stats=render.cluster_statistics(clustered,tracks,first)
    evidence.table('figure14_statistics.csv',stats)
    for name, prefix in [('seasonal_counts','season'),('genesis_counts','region')]:
        expected_stats=ns[name]
        for category in expected_stats.columns:
            np.testing.assert_allclose(stats.set_index('cluster')[f'{prefix}_{category}_pct'],expected_stats[category],atol=1e-12)
    np.testing.assert_array_equal(stats.n,ns['cluster_counts'])
    expected_intensity=ns['intensity_df'].groupby('cluster').vor42.mean()
    np.testing.assert_allclose(stats.set_index('cluster').max_vor42_mean,expected_intensity)
    evidence.check('Figure 14 logic',True,dict(counts=stats.n.tolist(),comparison='verbatim original preprocessing, same archived IDs; genesis and season percentages'))
    draw=load_definitions(evidence.source(root/'tests_draw_lec/draw_lec_eofs.py'),skip_imports={'draw_lec_v6'})
    original_phases={phase:normalized_columns(pd.read_csv(evidence.source(ARCHIVE/f'csv_eofs_energetics_with_track/{phase}/eofs.csv'))).set_axis(range(1,9)) for phase in c.PHASES}
    original_phases['total']=ref.set_axis(range(1,9))
    assembled=draw.create_individual_eof_dataframes(original_phases)
    for mode in range(1,5):
        for phase in c.PHASES:
            np.testing.assert_array_equal(assembled[mode].loc[phase],original_phases[phase].loc[mode])
    evidence.check('Figure 16 logic',True,dict(source='draw_lec_eofs.py: create_individual_eof_dataframes; draw_lec_v6 selects four primary phases', object='phase EOF loadings'))
    # Legacy maps 9–10 must also reproduce the archived numerical grids.
    density_fn=load_definitions(evidence.source(ARCHIVE/'src_energetic_eof/export_density_eof.py')).compute_density
    months=tracks.date.dt.to_period('M').nunique()
    for sign,suffix in [('positive','q90'),('negative','q10')]:
        for k in range(1,5):
            group=assignments.query('sign == @sign and dominant_eof == @k')
            values,lon,lat=density_fn(tracks[tracks.track_id.isin(group.track_id)],months)
            with xr.open_dataarray(evidence.source(TOTAL/f'track_density_{suffix}/SAt_track_density_eof_{k}.0.nc')) as saved:
                err=float(np.max(np.abs(values-saved.values)))
                ok=np.array_equal(lon,saved.lon) and np.array_equal(lat,saved.lat) and np.allclose(values,saved.values,atol=1e-10,rtol=0)
            evidence.check(f'Figures 9–10 {suffix} EOF{k}',ok,dict(max_absolute_error=err, months=months))
    validate_figure11(root,tracks,assignments,first,evidence)
    evidence.save()
    return ref, scores, mapping, clustered, centers, standardized, first


def composition(assignments, first):
    merged=assignments.merge(first[['track_id','region','season']],on='track_id',validate='many_to_one')
    rows=[]
    for (sign,mode),block in merged.groupby(['sign','dominant_eof']):
        for category,labels in [('region',['ARG','LA-PLATA','SE-BR']),('season',['DJF','MAM','JJA','SON'])]:
            for label in labels:
                n=int(block[category].eq(label).sum())
                rows.append(dict(sign=sign,reference_eof=mode,category=category,label=label,n=n,denominator=len(block),percentage=100*n/len(block)))
    return pd.DataFrame(rows)


def validate_figure11(root, tracks, assignments, first, evidence):
    """Reuse only the original numerical statements that feed the main panel."""
    script=evidence.source(root/'eof_cyclone_statistics_q10_q90.py')
    tree=ast.parse(script.read_text())
    loop=next(n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='suffix')
    nodes=[]
    for node in loop.body:
        if isinstance(node,ast.Assign):
            names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            if 'cyclone_stats' in names: break
            if set(names)&{'track_path','pcs_path','tracks','pcs'}: continue
        nodes.append(node)
    actual=composition(assignments,first)
    for sign in ['positive','negative']:
        ns=dict(pd=pd,np=np,tracks=tracks.copy(),pcs=assignments[assignments.sign.eq(sign)].copy())
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(script),'exec'),ns)
        for name,category,value in [('region_counts','region','proportion'),('seasonal_counts','season','frequency')]:
            expected=ns[name]
            part=actual.query('sign == @sign and category == @category')
            joined=part.merge(expected,left_on=['reference_eof','label'],right_on=['dominant_eof',category],validate='one_to_one')
            np.testing.assert_allclose(joined.percentage,joined[value],atol=1e-12)
            assert len(joined)==len(expected)
    evidence.table('figure11_composition.csv',actual)
    evidence.check('Figure 11 logic',True,dict(comparison='verbatim original preprocessing',metadata='region from original tracks, season of first stored occurrence',rows=len(actual)))


def render_validated_densities(root, tracks, assignments, clusters, figures, scratch, evidence):
    eof_fn=load_definitions(evidence.source(ARCHIVE/'src_energetic_eof/export_density_eof.py')).compute_density
    cluster_fn=load_definitions(evidence.source(root/'eof_export_density_clusters.py')).compute_density
    eof_renderer=load_definitions(evidence.source(root/'map_density_eof.py'))
    cluster_renderer=load_definitions(evidence.source(root/'map_density_intense.py'))
    summary=[]
    for suffix,sign,number in [('q90','positive',9),('q10','negative',10),('clusters',None,13)]:
        directory=scratch/f'density_{suffix}'; directory.mkdir(parents=True,exist_ok=True)
        subset=tracks if sign else tracks[tracks.track_id.isin(clusters.track_id)]
        months=int(subset.date.dt.to_period('M').nunique())
        maxima={}
        for k in range(1,5):
            ids=(assignments.loc[assignments.sign.eq(sign)&assignments.dominant_eof.eq(k),'track_id'] if sign else clusters.loc[clusters.cluster.eq(k),'track_id'])
            values,lon,lat=(eof_fn if sign else cluster_fn)(tracks[tracks.track_id.isin(ids)],months)
            name=f'EOF_{float(k)}' if sign else f'Cluster {k}'
            filename=f'SAt_track_density_eof_{k}.0.nc' if sign else f'track_density_cluster_{k}.nc'
            xr.DataArray(values,coords={'lon':lon,'lat':lat},dims=['lat','lon'],name=name).to_netcdf(directory/filename)
            xx,yy=np.meshgrid(lon,lat)
            pd.DataFrame(dict(lon=xx.ravel(),lat=yy.ravel(),density=values.ravel())).to_csv(evidence.output/f'density_{suffix}_{k}.csv.gz',index=False,float_format='%.17g',compression={'method':'gzip','mtime':0})
            maximum=float(values.max())
            maxima[k]=maximum
            levels=colors.density_levels(maximum,colors.interval_count(number,k))
            summary.append(dict(figure=number,group=k,months=months,n=len(ids),maximum=maximum,
                                vmax=f'{levels[-1]:.2f}',interval_count=len(levels)-1,
                                levels=json.dumps(levels.tolist()),assignment_ids_sha256=ids_digest(ids)))
        panel=scratch/f'panel_{suffix}'
        if sign:
            colors.render_eof_panel(directory,panel,suffix,maxima,eof_renderer)
            source=panel/f'density_panel_{suffix}.png'
        else:
            colors.render_cluster_panel(directory,panel,maxima,cluster_renderer)
            source=panel/'density_panel.png'
        shutil.copy2(source,figures/render.FIGURE_NAMES[number])
    evidence.table('density_metadata.csv',pd.DataFrame(summary))


def ids_digest(ids):
    import hashlib
    return hashlib.sha256(('\n'.join(map(str,sorted(set(map(int,ids)))))+'\n').encode()).hexdigest()


def render_12(root, tables, output, scratch):
    lec=load_definitions(root/'plot_LEC_std.py',skip_imports={'pdfs'})
    images=[]
    for panels,labels,subdir in [('A',['total'],'all'),('BCDE',[f'Cluster {k}' for k in range(1,5)],'clusters')]:
        part=tables[tables.panel.isin(list(panels))]
        mean=part.pivot(index='panel',columns='term',values='mean').loc[list(panels),c.EOF_TERMS].set_axis(labels)
        std=part.pivot(index='panel',columns='term',values='std').loc[list(panels),c.EOF_TERMS].set_axis(labels)
        dest=scratch/f'lec12_{subdir}'
        lec.plot_lorenzcycletoolkit_with_std(mean,std,str(dest))
        images.extend(dest/'LEC_std'/f'LEC_{label}.png' for label in labels)
    render.assemble_panel(images,output,figsize=(15,10),grid=(2,3),label_y=.55,cluster_panel=True)


def match_published_dimensions(png: Path, original: Path) -> None:
    """Center-crop or white-pad small tight-bbox changes around the same map."""
    with Image.open(original) as published, Image.open(png) as candidate:
        dx = candidate.width - published.width
        dy = candidate.height - published.height
        if dx == dy == 0:
            return
        if abs(dx) > 20 or abs(dy) > 20 or abs(dx)/published.width > .02 or abs(dy)/published.height > .02:
            raise GateFailure(f'layout differs for {png}: {candidate.size} != {published.size}')
        left, top = max(dx, 0)//2, max(dy, 0)//2
        cropped = candidate.convert('RGB').crop((left, top, left + min(candidate.width,published.width),
                                                 top + min(candidate.height,published.height)))
        canvas = Image.new('RGB', published.size, 'white')
        canvas.paste(cropped, (max(-dx, 0)//2, max(-dy, 0)//2))
        canvas.save(png)


def corrected_stage(legacy,corrected,tracks,root,bundle):
    ref,old_scores,old_mapping,old_clusters,old_centers,old_standardized,first=bundle
    evidence=Evidence(CORRECTED)
    gate=json.loads((GATE/'manifest.json').read_text())
    if not gate['checks'] or not all(x['passed'] for x in gate['checks']):
        raise GateFailure('legacy gate is not complete')
    evidence.source(GATE/'manifest.json')
    scores,loadings,mapping=total_pyeof(corrected,ref.to_numpy())
    # Original os.listdir-derived PC order retained on the common corrected IDs.
    order=old_scores.loc[old_scores.track_id.isin(scores.track_id),'track_id']
    scores=scores.set_index('track_id').loc[order].reset_index()
    mapping['ev_legacy']=old_mapping.explained_variance.to_numpy()
    evidence.table('total_eof_mapping.csv',mapping)
    evidence.table('eof_scores_total.csv',scores)
    evidence.table('eof_loadings_total.csv',loadings.assign(reference_eof=range(1,9)))
    evidence.table('pc_standard_deviations.csv',pd.DataFrame(dict(pc=PCS,std=scores[PCS].std())).reset_index(drop=True))
    assignments=c.assign_published_eof_extremes(scores)
    evidence.table('eof_extreme_assignments.csv',assignments)
    evidence.table('extreme_counts.csv',assignments.groupby(['sign','dominant_eof']).size().rename('n').reset_index())
    evidence.table('pc_quantiles.csv',pd.DataFrame(dict(pc=PCS,q10=scores[PCS].quantile(.1),q90=scores[PCS].quantile(.9))).reset_index(drop=True))
    ids,threshold=intense_ids(tracks,scores.track_id)
    evidence.check('corrected intense selection',len(ids)==603,dict(n=len(ids),threshold=threshold,population=6789,ids_sha256=ids_digest(ids)))
    evidence.table('intense_ids.csv',pd.DataFrame(dict(track_id=ids)))
    clusters,centers,standardized,scaler=cluster(scores,ids)
    cost=np.linalg.norm(old_standardized[:,None,:]-standardized[None,:,:],axis=2)
    rr,cc=linear_sum_assignment(cost)
    label_map={int(j+1):int(i+1) for i,j in zip(rr,cc)}
    clusters['corrected_raw_cluster']=clusters.cluster
    clusters['cluster']=clusters.cluster.map(label_map)
    centers=centers.iloc[cc].copy(); centers['corrected_raw_cluster']=centers.cluster; centers['cluster']=range(1,5)
    distances=[]
    for i,j in zip(rr,cc):
        other=cost.copy();other[i,j]=np.inf
        ar,ac=linear_sum_assignment(other)
        distances.append(dict(legacy_cluster=i+1,corrected_raw_cluster=j+1,n_legacy=int(old_clusters.cluster.eq(i+1).sum()),n_corrected=int(clusters.cluster.eq(i+1).sum()),centroid_distance=cost[i,j],assignment_margin=other[ar,ac].sum()-cost[rr,cc].sum()))
    evidence.table('cluster_mapping.csv',pd.DataFrame(distances))
    evidence.table('cluster_distance_matrix.csv',pd.DataFrame(cost,columns=[f'raw_{k}' for k in range(1,5)]).assign(legacy_cluster=range(1,5)))
    evidence.table('cluster_assignments.csv',clusters)
    evidence.table('cluster_centers.csv',centers)
    f12=figure12_tables(corrected,clusters,centers,loadings)
    evidence.table('figure12_values.csv',f12)
    evidence.table('figure11_composition.csv',composition(assignments,first))
    stats=render.cluster_statistics(clusters,tracks,first)
    evidence.table('figure14_statistics.csv',stats)
    intensity=clusters[['track_id','cluster']].merge(tracks.groupby('track_id').vor42.max(),on='track_id')
    evidence.table('figure14_intensity.csv',intensity)
    phase=phase_synthesis_inputs()
    evidence.source(ROOT/'results/comparison/article/phase_eof_matched/loadings.csv')
    evidence.table('figure16_loadings.csv',phase)
    membership_rows=[]
    for number in [12,13,14]:
        for k in range(1,5):
            group=clusters.loc[clusters.cluster.eq(k),'track_id']
            membership_rows.append(dict(figure=number,cluster=k,n=len(group),ids_sha256=ids_digest(group)))
    evidence.table('figure_cluster_memberships.csv',pd.DataFrame(membership_rows))
    figures=ROOT/'figures/corrected/article'
    figures.mkdir(parents=True,exist_ok=True)
    scratch=ROOT/'tmp/validated_downstream';scratch.mkdir(parents=True,exist_ok=True)
    render_validated_densities(root,tracks,assignments,clusters,figures,scratch,evidence)
    render.render_eof_statistics(assignments,first,figures/render.FIGURE_NAMES[11])
    render_12(root,f12,figures/render.FIGURE_NAMES[12],scratch)
    render.render_cluster_statistics(clusters,tracks,first,figures/render.FIGURE_NAMES[14])
    draw=load_definitions(root/'tests_draw_lec/draw_lec_v6.py')
    phase_means=corrected.groupby('period')[c.EOF_TERMS].mean()
    evidence.table('figure15_phase_means.csv',phase_means.rename_axis('period').reset_index())
    draw.plot_lorenzcycletoolkit(phase_means,str(scratch/'synthesis'),normalization_type='log')
    shutil.copy2(scratch/'synthesis/draw_LEC/LEC_total_v6.png',figures/render.FIGURE_NAMES[15])
    eof_draw=load_definitions(root/'tests_draw_lec/draw_lec_eofs.py',skip_imports={'draw_lec_v6'})
    eof_draw.plot_lorenzcycletoolkit.__globals__['plot_period_means']=draw.plot_period_means
    images=[]
    for mode in range(1,5):
        table=phase.query('reference_eof == @mode').pivot(index='scope',columns='term',values='loading').loc[c.PHASES,c.EOF_TERMS]
        eof_draw.plot_lorenzcycletoolkit(table,str(scratch/'synthesis_eofs'),mode)
        images.append(scratch/f'synthesis_eofs/draw_LEC/LEC_eof_{mode}.png')
    render.assemble_panel(images,figures/render.FIGURE_NAMES[16],figsize=(9.5,9.5),grid=(2,2),label_y=.5,show_labels=False)
    manifest=[]
    references={9:'map_density_eof.py',10:'map_density_eof.py',11:'eof_cyclone_statistics_q10_q90.py',12:'eof_plot_lec_centroids.py',13:'eof_export_density_clusters.py',14:'eof_cluster_statistics.py',15:'tests_draw_lec/draw_lec_v6.py',16:'tests_draw_lec/draw_lec_eofs.py'}
    for number in range(9,17):
        png=figures/render.FIGURE_NAMES[number]
        match_published_dimensions(png, ROOT/'figures/original/article'/render.FIGURE_NAMES[number])
        pdf=render.save_raster_pdf(png)
        manifest.append(dict(figure=number,script_original=str(evidence.source(root/references[number])),wrapper=str(Path(__file__).resolve()),png=str(png.relative_to(ROOT)),pdf=str(pdf.relative_to(ROOT)),png_sha256=c.sha256_file(png),pdf_sha256=c.sha256_file(pdf)))
    evidence.table('figure_manifest.csv',pd.DataFrame(manifest))
    evidence.save()
    metadata=dict(K=4,PCs=PCS,scaler='StandardScaler fit separately on intense subset',random_state=42,n_init='auto',effective_n_init=1,algorithm='lloyd',init='k-means++',max_iter=300,tol=1e-4,sklearn_version=sklearn.__version__,threshold=threshold,threshold_population=6789,row_order='archived legacy PC row order restricted to corrected IDs',cluster_matching='Hungarian Euclidean distance between centers in each intense-subset standardized matched-PC coordinate system; no claim of physical equivalence',legacy_manifest_sha256=c.sha256_file(GATE/'manifest.json'))
    (CORRECTED/'workflow.json').write_text(json.dumps(metadata,indent=2)+'\n')
    finalize_provenance()
    return 0


def finalize_provenance():
    """Hash the complete corrected run and its source inputs."""
    gate=json.loads((GATE/'manifest.json').read_text())
    workflow=json.loads((CORRECTED/'workflow.json').read_text())
    figure_manifest=pd.read_csv(CORRECTED/'figure_manifest.csv')
    if set(figure_manifest.figure)!=set(range(9,17)) or not all(x['passed'] for x in gate['checks']):
        raise GateFailure('cannot finalize incomplete downstream products')
    sources=dict(gate['sources'])
    sources.update(json.loads((CORRECTED/'manifest.json').read_text())['sources'])
    for name in ['reproduce_downstream.py','density_color_scale.py','common.py','legacy_source.py','generate_corrected_article.py','phase_eofs.py']:
        path=ROOT/'scripts/article_figures'/name
        sources[str(path)]=c.sha256_file(path)
    outputs={str(p.relative_to(ROOT)):c.sha256_file(p) for directory in [GATE,CORRECTED] for p in directory.iterdir() if p.is_file() and p.name!='provenance.json'}
    figures=[]
    for row in figure_manifest.to_dict('records'):
        for kind in ['png','pdf']:
            path=ROOT/row[kind]
            if c.sha256_file(path)!=row[f'{kind}_sha256']: raise GateFailure(f'figure hash mismatch: {path}')
            outputs[row[kind]]=row[f'{kind}_sha256']
        row.update(legacy_gate=str(GATE.relative_to(ROOT)/'manifest.json'),
                   legacy_input=[p for p in sources if p.endswith('/energy_cache.parquet')],
                   corrected_input=[p for p in sources if p.endswith('/energy_cache_corrected.parquet')],
                   tracks_input=[p for p in sources if p.endswith('/tracks_SAt_filtered_with_periods.csv')],
                   eof_mapping=str(CORRECTED.relative_to(ROOT)/'total_eof_mapping.csv') if row['figure'] in range(9,15) else ('results/comparison/article/phase_eof_matched/loadings.csv' if row['figure']==16 else None),
                   PC_convention='pyEOF.pcs(s=2): unit sample PC * corrected lambda; lambda=24*EV*N/(N-1)',
                   intensity_threshold=workflow['threshold'],cluster_parameters=workflow,
                   repo_commit=gate['repo_commit'],toolkit_commit=gate['toolkit_commit'])
        figures.append(row)
    document=dict(status='VALIDATED_CORRECTED_CANDIDATES',figures=figures,sources=sources,outputs=outputs,
                  software=dict(numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,matplotlib=matplotlib.__version__,xarray=xr.__version__),
                  numerical_legacy_gate='passed; see checks in reproduction_gate/manifest.json',
                  historical_environment='data: sklearn 1.4.2, pyEOF 0.0.0; package source and conda history hashed',
                  compatibility='sklearn 1.7.1 reproduces all 679 archived cluster labels modulo label permutation',
                  PDF_format='one-page raster PDF exported from publication-style PNG; not vector',
                  limitations=['Density color limits are rounded to two decimals from each panel maximum; visual values above the rounded limit are capped only for plotting, while saved density fields remain unmodified',
                               'Cluster matching margins are recorded; Hungarian assignment does not establish physical equivalence',
                               'Canonical phase products and Figures 5–8 remain frozen'])
    (CORRECTED/'provenance.json').write_text(json.dumps(document,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-only',action='store_true')
    args=parser.parse_args()
    config=tomllib.loads((ROOT/'config/data_sources.toml').read_text())
    root=Path(config['article']['legacy_source_root'])
    evidence=Evidence(GATE)
    legacy,corrected,sources=load_pinned_phase_inputs(ROOT,ROOT/config['inputs']['corrected_cache']['local'])
    for frame in (legacy,corrected):
        frame['track_id']=pd.to_numeric(frame.track_id,errors='raise').astype('int64')
    for s in sources.values(): evidence.source(s['path'])
    evidence.source(PYEOF); evidence.source(HISTORY)
    evidence.source(PYEOF.parents[1]/'sklearn/cluster/_kmeans.py')
    for filename in ['src_energetic_eof/eof_analysis_with_track_id.py','src_energetic_eof/attribute_track_ids_to_eof_extremes.py']:
        evidence.source(ARCHIVE/filename)
    for filename in ['eofs_kmeans_pcs.py','plot_LEC_std.py','eof_plot_lec_centroids.py','plot_LEC_panel_clusters.py','eof_cyclone_statistics_q10_q90.py','map_density_eof.py','map_density_intense.py','tests_draw_lec/draw_lec_v6.py']:
        evidence.source(root/filename)
    tracks=pd.read_csv(evidence.source(ARCHIVE/'tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv'))
    tracks.date=pd.to_datetime(tracks.date)
    try:
        bundle=validate_legacy(legacy,tracks,root,evidence)
    except GateFailure as exc:
        print(f'BLOCKED: {exc}. No corrected output generated.',flush=True)
        return 1
    if args.legacy_only:
        return 0
    return corrected_stage(legacy,corrected,tracks,root,bundle)


if __name__=='__main__':
    raise SystemExit(main())
