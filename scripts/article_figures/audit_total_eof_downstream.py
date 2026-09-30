"""Numerical audit only: reuse assignments; never render or refit clustering.

Run from the repository root with ``python -m scripts.article_figures.audit_total_eof_downstream``.
External inputs are explicit, hash-checked where a pre-existing pin exists.
Archived manuscript artifacts are evidence, not an automatically trusted baseline.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from scripts.article_figures import common as c

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/comparison/article/total_eof_audit'
COMP = ROOT / 'results/comparison/article'
REPRO = ROOT / 'results/corrected/article/reproduction'
PCS = [f'PC{i}' for i in range(1, 9)]


def ids_hash(ids):
    return hashlib.sha256(('\n'.join(map(str, sorted(set(map(int, ids))))) + '\n').encode()).hexdigest()


def memberships(frame):
    return set(map(tuple, frame[['track_id', 'sign', 'dominant_eof']].to_numpy()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((COMP / 'provenance.json').read_text())
    config = tomllib.loads((ROOT / 'config/data_sources.toml').read_text())
    manuscript = Path(config['article']['legacy_source_root'])
    archive = ROOT.parent / 'energetic_patterns_cyclones_south_atlantic'
    total_archive = archive / 'csv_eofs_energetics_with_track/Total'
    sources = {}
    checks = []

    def source(path, expected=None):
        if not path.is_file():
            raise FileNotFoundError(f'Expected audit source: {path}; no alternate search permitted')
        digest = c.sha256_file(path)
        if expected is not None and digest != expected:
            raise ValueError(f'Hash mismatch: {path}: expected {expected}, observed {digest}')
        sources[str(path)] = {'sha256': digest, 'preexisting_pin': expected is not None}
        return path

    def csv(name, rows):
        frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
        frame.to_csv(OUT / name, index=False, float_format='%.12g')
        return frame

    def check(name, passed, evidence):
        checks.append({'check': name, 'status': 'PASS' if passed else 'FAIL', 'evidence': str(evidence)})

    legacy_path = source(Path(provenance['legacy_cache']), provenance['legacy_cache_sha256'])
    corrected_path = source(ROOT / config['inputs']['corrected_cache']['local'], provenance['corrected_cache_sha256'])
    tracks_path = source(ROOT / config['inputs']['tracks']['local'], provenance['tracks_sha256'])
    legacy, corrected, tracks = c.load_article_comparison_inputs(legacy_path, corrected_path, tracks_path)
    frames = {'before': legacy, 'after': corrected}
    for v, f in frames.items():
        check(f'{v}_unique_period_keys', not f.duplicated(['track_id', 'period']).any(), len(f))
    csv('population_periods.csv', [{'version': v, 'period': p, 'rows': len(g), 'cyclones': g.track_id.nunique()}
                                  for v, f in frames.items() for p, g in f.groupby('period')])
    common_ids = set(legacy.track_id) & set(corrected.track_id)
    before_raw = c.compute_eof(legacy.groupby('track_id')[c.EOF_TERMS].mean(), c.EOF_TERMS)
    after_raw = c.compute_eof(corrected.groupby('track_id')[c.EOF_TERMS].mean(), c.EOF_TERMS)
    loadings, variance, scores = c.independent_total_eof(legacy, corrected)
    aligned = c.align_eofs(before_raw[1], after_raw[1], after_raw[2], after_raw[3])
    ranks = aligned[3]
    signs = np.sign(np.sum(aligned[0] * after_raw[1][ranks - 1], axis=1)).astype(int)
    original_loadings = pd.read_csv(source(total_archive / 'eofs.csv'))
    original_loadings.columns = [x + ' (finite diff.)' if x.startswith('∂') and 'finite diff' not in x else x for x in original_loadings.columns]
    original_loadings = original_loadings[c.EOF_TERMS].to_numpy()
    original_scores = pd.read_csv(source(total_archive / 'pcs.csv')).set_index('track_id').sort_index()
    assert original_scores.index.equals(before_raw[0])
    pub_corr = np.diag(np.corrcoef(original_loadings, before_raw[1])[:8, 8:])
    published_sign = np.sign(pub_corr).astype(int)
    published_aligned = c.align_eofs(original_loadings, after_raw[1], after_raw[2], after_raw[3])
    pub_sign = np.sign(np.sum(published_aligned[0] * after_raw[1][published_aligned[3] - 1], axis=1)).astype(int)
    check('no_total_complete_case_loss',len(before_raw[0])==6789 and len(after_raw[0])==3820, [len(before_raw[0]),len(after_raw[0])])
    rows = []
    for k in range(8):
        rows.append(dict(reference_eof=k+1, corrected_raw_rank=int(ranks[k]), rank_swap=bool(ranks[k] != k+1),
            pattern_correlation=aligned[4][k], sign_alignment_to_current_reference=signs[k], sign_alignment_to_published=pub_sign[k],
            current_reference_sign_vs_published=published_sign[k], ev_published=100*before_raw[3][k], ev_corrected=100*aligned[2][k],
            max_absolute_loading_difference_current=np.max(np.abs(before_raw[1][k]-aligned[0][k])),
            max_absolute_loading_difference_published=np.max(np.abs(original_loadings[k]-published_aligned[0][k])),
            archived_pc_std=original_scores[PCS[k]].std(ddof=1), current_pc_std=before_raw[2][:,k].std(ddof=1),
            archived_loading_abs_correlation=abs(pub_corr[k])))
    mapping = csv('total_eof_mapping.csv', rows)
    check('one_to_one_total_matching', sorted(ranks.tolist()) == list(range(1,9)), ranks.tolist())
    check('published_reference_orientation', np.all(published_sign == 1), published_sign.tolist())
    for name, calculated in [('loadings', loadings), ('variance', variance), ('scores', scores)]:
        saved = pd.read_csv(source(COMP / f'eof_{name}_total.csv'))
        keys = ['version','eof','term'] if name == 'loadings' else ['version','eof'] if name == 'variance' else ['version','track_id']
        a, b = calculated.sort_values(keys).reset_index(drop=True), saved.sort_values(keys).reset_index(drop=True)
        numeric = a.select_dtypes(include='number').columns
        delta = np.max(np.abs(a[numeric].to_numpy()-b[numeric].to_numpy()))
        check(f'current_saved_total_{name}', delta < 5e-6, f'max absolute CSV rounding error {delta}')
    for k, raw_rank in enumerate(ranks):
        check(f'PC{k+1}_joint_permutation_sign_EV',
              np.allclose(aligned[1][:,k], after_raw[2][:,raw_rank-1]*signs[k]) and
              np.allclose(aligned[0][k], after_raw[1][raw_rank-1]*signs[k]) and aligned[2][k] == after_raw[3][raw_rank-1],
              f'raw {raw_rank}, sign {signs[k]}, EV {100*aligned[2][k]}')
    assignments = pd.read_csv(source(COMP / 'eof_extreme_assignments.csv'))
    repro_assignments = pd.read_csv(source(REPRO / 'eof_extreme_assignments.csv'))
    published_parts = []
    for sign, suffix in [('positive','q90'),('negative','q10')]:
        archived = pd.read_csv(source(total_archive / f'pcs_with_dominant_eof_{suffix}.csv'))
        published_parts.append(archived.assign(sign=sign))
    published = pd.concat(published_parts, ignore_index=True)
    expected_published = c.assign_published_eof_extremes(original_scores.reset_index())
    check('archived_extremes_reproduced_from_archived_PCs', memberships(expected_published) == memberships(published),
          len(memberships(expected_published) ^ memberships(published)))
    # Isolate orientation and PC scale effects on the same legacy population, no scientific replacement.
    orient = pd.DataFrame(before_raw[2]*published_sign, columns=PCS).assign(track_id=before_raw[0].to_numpy())
    orientation_only = c.assign_published_eof_extremes(orient)
    scaled = orient.copy()
    scaled[PCS] *= original_scores[PCS].std().to_numpy()
    scale_plus_sign = c.assign_published_eof_extremes(scaled)
    check('archived_PC_scaling_and_sign_relation', np.allclose(scaled.set_index('track_id')[PCS],original_scores[PCS],atol=1e-9),
          'archived PCs = unit PCs * published sign * archived sample std')
    check('sign_and_scale_restore_archived_assignments', memberships(scale_plus_sign)==memberships(published),
          len(memberships(scale_plus_sign)^memberships(published)))
    counts, overlaps, thresholds = [], [], []
    for v in ['before','after']:
        s = scores[scores.version.eq(v)]
        expected = c.assign_published_eof_extremes(s)
        check(f'{v}_extremes_from_aligned_PCs', memberships(expected)==memberships(assignments[assignments.version.eq(v)]),len(expected))
        for pc in PCS:
            thresholds.append({'version':v,'pc':pc,'q90':s[pc].quantile(.9),'q10':s[pc].quantile(.1)})
    for k in range(1,9):
        row = {'reference_eof':k,'corrected_raw_rank':int(ranks[k-1]),'current_sign_alignment':int(signs[k-1])}
        for sign, suffix in [('positive','q90'),('negative','q10')]:
            b=set(assignments.loc[assignments.version.eq('before')&assignments.sign.eq(sign)&assignments.dominant_eof.eq(k),'track_id'])
            a=set(assignments.loc[assignments.version.eq('after')&assignments.sign.eq(sign)&assignments.dominant_eof.eq(k),'track_id'])
            p=set(published.loc[published.sign.eq(sign)&published.dominant_eof.eq(k),'track_id'])
            r=set(repro_assignments.loc[repro_assignments.sign.eq(sign)&repro_assignments.dominant_eof.eq(k),'track_id'])
            row.update({f'before_{suffix}_n':len(b),f'after_{suffix}_n':len(a),f'archived_published_{suffix}_n':len(p),f'corrected_only_raw_{suffix}_n':len(r)})
            bc=b&common_ids
            overlaps.append(dict(reference_eof=k,sign=sign,retained=k<=4,n_before=len(b),n_after=len(a),intersection=len(a&b),
                jaccard_independent=len(a&b)/len(a|b) if a|b else np.nan,
                jaccard_common_ID_restriction=len(a&bc)/len(a|bc) if a|bc else np.nan,
                published_vs_before_symmetric_difference=len(p^b), corrected_only_vs_after_symmetric_difference=len(r^a)))
        counts.append(row)
    csv('pc_extreme_counts.csv',counts); csv('pc_extreme_overlap.csv',overlaps); csv('pc_thresholds.csv', thresholds)
    changes=[]
    for sign in ['positive','negative']:
        b=assignments.query('version == "before" and sign == @sign').set_index('track_id')
        a=assignments.query('version == "after" and sign == @sign').set_index('track_id')
        shared=b.index.intersection(a.index)
        changes.append({'metric':f'{sign}_retained_in_both','n':len(shared)})
        changes.append({'metric':f'{sign}_dominant_eof_changed_among_retained_in_both','n':int((b.loc[shared,'dominant_eof']!=a.loc[shared,'dominant_eof']).sum())})
    def sign_sets(v):
        f=assignments[assignments.version.eq(v)]
        return {i:set(g.sign) for i,g in f.groupby('track_id')}
    bs,as_=sign_sets('before'),sign_sets('after')
    for old,new in [('positive','negative'),('negative','positive')]:
        changes.append({'metric':f'exclusive_{old}_to_exclusive_{new}_common_IDs','n':sum(bs.get(i)=={old} and as_.get(i)=={new} for i in common_ids)})
    for v in ['before','after']:
        ss=sign_sets(v)
        changes.append({'metric':f'{v}_systems_in_both_signs','n':sum(len(s)==2 for s in ss.values())})
    csv('pc_membership_changes.csv',changes)
    csv('legacy_assignment_sensitivity.csv',[
        {'variant':label,'symmetric_difference_vs_archive':len(memberships(f)^memberships(published)),'assignment_rows':len(f)}
        for label,f in [('current',assignments.query('version == "before"')),('published_sign_unit_variance',orientation_only),('published_sign_and_scale',scale_plus_sign)]])
    first=c.first_track_rows(tracks)
    # This exact original input is named by the manuscript scripts, not discovered by fallback.
    original_tracks_path=source(archive/'tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv')
    original_tracks=pd.read_csv(original_tracks_path,usecols=['track_id','date','lon vor','lat vor','vor42','region'])
    original_tracks.date=pd.to_datetime(original_tracks.date)
    original_tracks['lon vor']=np.where(original_tracks['lon vor']>180,original_tracks['lon vor']-360,original_tracks['lon vor'])
    fields=['track_id','date','lon vor','lat vor','vor42']
    x=original_tracks[fields].sort_values(fields[:2]).reset_index(drop=True)
    y=tracks[fields].sort_values(fields[:2]).reset_index(drop=True)
    check('original_vs_processed_track_keys',x[fields[:2]].equals(y[fields[:2]]),len(x))
    check('original_vs_processed_physical_track_values',np.allclose(x[fields[2:]],y[fields[2:]],atol=1e-12,rtol=0),np.max(np.abs(x[fields[2:]].to_numpy()-y[fields[2:]].to_numpy())))
    old_first=original_tracks.sort_values(fields[:2]).groupby('track_id').first()
    difference=(first.set_index('track_id').region!=old_first.region).sum()
    check('genesis_boxes_vs_original_region_metadata',difference==0,f'{difference} of {len(first)} differ')
    check('published_vs_current_extreme_memberships',memberships(published)==memberships(assignments.query('version == "before"')),len(memberships(published)^memberships(assignments.query('version == "before"'))))
    check('corrected_only_vs_reference_extreme_memberships',memberships(repro_assignments)==memberships(assignments.query('version == "after"')),len(memberships(repro_assignments)^memberships(assignments.query('version == "after"'))))
    check('published_PC_scaling',np.allclose(original_scores[PCS].std(),1),original_scores[PCS].std().tolist())
    if 'region' in tracks:
        archived_first=tracks.sort_values(['track_id','date']).groupby('track_id').first()
        mismatch=(first.set_index('track_id').region != archived_first.region)
        check('genesis_reclassification_preserves_stored_metadata', not mismatch.any(), f'{mismatch.sum()} differing regions')
    statistics=[]
    for workflow, f in [('comparison',assignments),('corrected_only',repro_assignments.assign(version='after'))]:
        merged=f.merge(first[['track_id','season','region']],on='track_id',validate='many_to_one')
        check(f'{workflow}_extreme_track_coverage',len(merged)==len(f),len(merged))
        for (v,sg,k),g in merged.groupby(['version','sign','dominant_eof']):
            for category,categories in [('season',['DJF','MAM','JJA','SON']),('region',['ARG','LA-PLATA','SE-BR','OTHER'])]:
                for label in categories:
                    n=int(g[category].eq(label).sum())
                    statistics.append({'workflow':workflow,'version':v,'sign':sg,'reference_eof_or_raw_rank':k,'category':category,'label':label,'n':n,'denominator':len(g),'percentage':100*n/len(g)})
    stat=csv('figure11_composition.csv',statistics)
    delta=stat[stat.workflow.eq('comparison')].pivot(index=['sign','reference_eof_or_raw_rank','category','label'],columns='version',values='percentage').reset_index()
    delta['delta_percentage_points']=delta.after-delta.before
    csv('figure11_changes.csv',delta)
    maximum=tracks.groupby('track_id').vor42.max()
    qrows=tracks.vor42.quantile(.9); qmax=maximum.quantile(.9)
    selections=[]
    for definition,pop,t,op in [('current_comparison_track_rows',tracks.vor42,qrows,'>'),('published_script_all_track_maxima',maximum,qmax,'>='),('TeX_strict_all_track_maxima',maximum,qmax,'>'),('sensitivity_legacy_EOF_maxima',maximum.loc[sorted(set(legacy.track_id))],maximum.loc[sorted(set(legacy.track_id))].quantile(.9),'>'),('sensitivity_corrected_EOF_maxima',maximum.loc[sorted(set(corrected.track_id))],maximum.loc[sorted(set(corrected.track_id))].quantile(.9),'>')]:
        selected=set(maximum[maximum>=t if op=='>=' else maximum>t].index)
        selections.append(dict(definition=definition,variable='vor42',threshold=t,operator=op,quantile=.9,threshold_population_n=len(pop),n_before=len(set(legacy.track_id)&selected),n_after=len(set(corrected.track_id)&selected),threshold_equal_cyclones=int(maximum.eq(t).sum())))
    csv('intense_selection_audit.csv',selections)
    clusters=pd.read_csv(source(COMP/'intense_pc_cluster_assignments.csv'))
    centers=pd.read_csv(source(COMP/'intense_pc_cluster_centers.csv'))
    meta=json.loads(source(COMP/'intense_pc_cluster_metadata.json').read_text())
    repro_clusters=pd.read_csv(source(REPRO/'intense_pc_cluster_assignments.csv'))
    repro_meta=json.loads(source(REPRO/'intense_pc_cluster_metadata.json').read_text())
    archived_clusters=pd.read_csv(source(manuscript/'figures/eof_clusters_intense/pcs_with_clusters.csv'))
    check('comparison_intense_matches_published_maximum_criterion',all(set(clusters.query('version == @v').track_id)==(set(f.track_id)&set(maximum[maximum>=qmax].index)) for v,f in frames.items()),f'row q90 {qrows} versus max q90 {qmax}')
    check('corrected_only_five_clusters',repro_meta['clusters']==5,repro_meta['clusters'])
    check('archived_intense_IDs_equal_maximum_criterion',set(archived_clusters.track_id)==set(maximum[maximum>=qmax].index),len(archived_clusters))
    check('five_group_tex_vs_archived_cluster_count',archived_clusters.cluster.nunique()==5,archived_clusters.cluster.nunique())
    csv('archived_cluster_counts.csv',archived_clusters.groupby('cluster').size().rename('n').reset_index().assign(identity='archived zero-based; 4-group artifact, not five-group proof'))
    bc=centers.query('version == "before"').sort_values('cluster')[PCS].to_numpy()
    ac=centers.query('version == "after"').sort_values('cluster')[PCS].to_numpy()
    order=np.array(meta['corrected_original_rank_by_matched_cluster'])-1
    raw_centers=np.empty_like(ac); raw_centers[order]=ac
    cost=np.linalg.norm(bc[:,None,:]-raw_centers[None,:,:],axis=2)
    rr,cc=linear_sum_assignment(cost)
    best=cost[rr,cc].sum()
    alternatives=[]
    for i,j in zip(rr,cc):
        other=cost.copy(); other[i,j]=1e9
        ii,jj=linear_sum_assignment(other)
        alternatives.append(cost[ii,jj].sum()-best)
    check('cluster_matching_one_to_one',sorted(order.tolist())==list(range(5)) and np.array_equal(cc,order),order.tolist())
    csv('cluster_distance_matrix.csv',[{'reference_cluster':i+1,'corrected_raw_cluster':j+1,'distance':cost[i,j]} for i in range(5) for j in range(5)])
    csv('cluster_mapping.csv',[dict(reference_cluster=i+1,corrected_raw_cluster=int(order[i]+1),matched_label=i+1,distance=cost[i,order[i]],
        n_before=int(((clusters.version=='before')&(clusters.cluster==i+1)).sum()),n_after=int(((clusters.version=='after')&(clusters.cluster==i+1)).sum()),
        nearest_raw_cluster=int(cost[i].argmin()+1), row_alternative_margin=float(np.min(np.delete(cost[i],order[i]))-cost[i,order[i]]),
        global_assignment_gap_if_pair_forbidden=alternatives[i],identity='current recomputed legacy cluster; not verified published cluster') for i in range(5)])
    csv('cluster_centroid_differences.csv',[{'reference_cluster':i+1,'pc':pc,'before':bc[i,j],'after':ac[i,j],'difference':ac[i,j]-bc[i,j]} for i in range(5) for j,pc in enumerate(PCS)])
    group_rows=[]; lec_rows=[]; density_rows=[]; stats_rows=[]; feature_rows=[]
    for workflow, f in [('comparison',clusters),('corrected_only',repro_clusters.assign(version='after'))]:
        for v,vf in f.groupby('version'):
            cache=frames[v]; means=cache.groupby('track_id')[c.EOF_TERMS].mean()
            groups=[('all_intense',vf.track_id),*[(str(k),g.track_id) for k,g in vf.groupby('cluster')]]
            if workflow=='corrected_only': groups.append(('figure12a_all_systems',means.index))
            for label,ids in groups:
                subset=tracks[tracks.track_id.isin(ids)]
                realized=set(subset.track_id)
                group_rows.append(dict(workflow=workflow,version=v,group=label,n=len(ids),assignment_ids_sha256=ids_hash(ids),track_ids_sha256=ids_hash(realized),missing_track_ids=len(set(ids)-realized),figure12a_uses_this=label==('all_intense' if workflow=='comparison' else 'figure12a_all_systems')))
                values=means.loc[list(ids)]
                for term in c.EOF_TERMS:
                    lec_rows.append(dict(workflow=workflow,version=v,group=label,term=term,n=len(values),mean=values[term].mean(),std=values[term].std()))
                density_rows.append(dict(workflow=workflow,version=v,group=label,track_points=len(subset),observed_group_months=subset.date.dt.to_period('M').nunique(),normalization_months=subset.date.dt.to_period('M').nunique() if workflow=='comparison' else tracks[tracks.track_id.isin(vf.track_id)].date.dt.to_period('M').nunique(),id_sha256=ids_hash(ids)))
            for k,g in vf.groupby('cluster'):
                joined=g.merge(first[['track_id','season','region']],on='track_id',validate='many_to_one').merge(maximum.rename('max_vor42'),on='track_id',validate='many_to_one')
                row={'workflow':workflow,'version':v,'cluster':k,'n':len(joined),'max_vor42_mean':joined.max_vor42.mean(),'max_vor42_median':joined.max_vor42.median()}
                for field in ['season','region']:
                    for category in (['DJF','MAM','JJA','SON'] if field=='season' else ['ARG','LA-PLATA','SE-BR','OTHER']):
                        row[f'{field}_{category}_pct']=100*joined[field].eq(category).mean()
                for q in [0,.25,.75,1]: row[f'max_vor42_q{int(100*q)}']=joined.max_vor42.quantile(q)
                stats_rows.append(row)
            if workflow=='comparison':
                s=scores.query('version == @v').set_index('track_id').loc[vf.track_id,PCS]
                for pc in PCS: feature_rows.append({'version':v,'pc':pc,'intense_std':s[pc].std(),'full_population_std':scores.query('version == @v')[pc].std()})
                actual=s.assign(cluster=vf.cluster.to_numpy()).groupby('cluster')[PCS].mean().to_numpy()
                check(f'{v}_centers_from_assignments',np.allclose(actual,bc if v=='before' else ac,atol=5e-7),np.max(np.abs(actual-(bc if v=='before' else ac))))
    pc_density=[]
    for workflow,f in [('comparison',assignments),('corrected_only',repro_assignments.assign(version='after'))]:
        for (v,sg,k),g in f.groupby(['version','sign','dominant_eof']):
            block=tracks[tracks.track_id.isin(g.track_id)]
            months=block.date.dt.to_period('M').nunique()
            pc_density.append({'workflow':workflow,'version':v,'sign':sg,'reference_eof_or_raw_rank':k,'n':len(g),'track_points':len(block),'group_months':months,'normalization_months':months if workflow=='comparison' else tracks.date.dt.to_period('M').nunique(),'id_sha256':ids_hash(g.track_id)})
    csv('pc_density_membership.csv',pc_density)
    csv('figure12_14_membership_checks.csv',group_rows); csv('figure12_lec_statistics.csv',lec_rows); csv('figure13_density_membership.csv',density_rows); csv('cluster_feature_scales.csv',feature_rows)
    all_stats=csv('cluster_statistics_audit.csv',stats_rows)
    for workflow,path in [('comparison',COMP),('corrected_only',REPRO)]:
        old=pd.read_csv(source(path/'intense_pc_cluster_statistics.csv'))
        new=all_stats[all_stats.workflow.eq(workflow)].copy()
        if 'version' not in old: old['version']='after'
        keys=['version','cluster']; cols=list(old.select_dtypes('number').columns.drop('cluster'))
        if set(cols)<=set(new):
            error=np.max(np.abs(new.set_index(keys).sort_index()[cols].to_numpy()-old.set_index(keys).sort_index()[cols].to_numpy()))
            check(f'{workflow}_figure14_saved_statistics',error<5e-6,error)
        else: check(f'{workflow}_figure14_saved_statistics',False,'schema differs: '+str(set(cols)-set(new)))
    # Paired control is a separate primary-phase experiment, not the common-ID overlap above.
    lp,cp,tp=c.load_comparison_inputs(legacy_path,corrected_path,tracks_path)
    pl,pv,ps=c.paired_total_eof(lp,cp)
    paired=[]
    for v in ['before','after']:
        e=c.assign_eof_extremes(ps[ps.version.eq(v)])
        for (sg,k),g in e.groupby(['sign','dominant_eof']):paired.append({'version':v,'sign':sg,'paired_reference_eof':k,'n':len(g)})
    csv('paired_control_extreme_counts.csv',paired); csv('paired_control_total_variance.csv',pv)
    # Audit existing manifests, including frozen phase baseline, without rewriting them.
    for path in [COMP/'figure_manifest.csv',REPRO/'figure_manifest.csv']:
        manifest=pd.read_csv(source(path))
        for row in manifest.to_dict('records'):
            for suffix in ['png','pdf']:
                if suffix in row and f'{suffix}_sha256' in row:
                    p=ROOT/row[suffix]
                    check(f'manifest:{p.relative_to(ROOT)}',c.sha256_file(p)==row[f'{suffix}_sha256'],row[f'{suffix}_sha256'])
    for snapshot in [COMP/'phase_eof_matched/frozen_outputs.json',OUT/'frozen_outputs.json']:
        frozen=json.loads(snapshot.read_text())
        changed=[p for p,h in frozen.items() if c.sha256_file(ROOT/p)!=h]
        check(f'frozen:{snapshot.relative_to(ROOT)}',not changed,f'{len(frozen)} files; changed={changed}')
    for relative in ['eofs_kmeans_pcs.py','eof_plot_lec_centroids.py','plot_LEC_panel_clusters.py','eof_cyclone_statistics_q10_q90.py','tests_draw_lec/draw_lec_eofs.py',config['article']['published_article_tex']]:source(manuscript/relative)
    source(ROOT/'figures/original/article/fig_16_eof_synthesis.png')
    submission=manuscript/Path(config['article']['published_article_tex']).parent
    for name,local in [('EOFs_panel.png','fig_16_eof_synthesis.png'),('panel_LEC_clusters.png','fig_12_intense_clusters_lec.png')]:
        src=source(submission/name)
        check(f'published_image_identity:{name}',c.sha256_file(src)==c.sha256_file(ROOT/'figures/original/article'/local),c.sha256_file(src))
    # Definition conflicts are independent of numerical propagation checks.
    checks.extend([
        {'check':'Figure16_definition','status':'BLOCKED','evidence':'Final TeX 467-473: positive-group phase-resolved mean LEC; original draw_lec_eofs.py: phase loading tables. Author review required.'},
        {'check':'Figure12a_definition','status':'BLOCKED','evidence':'Published caption and original panel: all systems; comparison: all intense. Corrected-only: all 3820 systems.'},
        {'check':'Figure12b_definition','status':'BLOCKED','evidence':'Original eof_plot_lec_centroids.py: centroids @ EOF + full mean; current generators: direct group means.'},
        {'check':'clustering_scaling','status':'BLOCKED','evidence':'Original: StandardScaler fitted on intense subset; comparison: unscaled PCs standardized on full independent populations.'},
        {'check':'comparison_density_definition','status':'BLOCKED','evidence':'Comparison: Gaussian-smoothed histogram / occupied months per group; published: haversine KDE per 1e6 km2 per common months.'},
    ])
    frozen_commit=provenance['legacy_source_commit_audited']
    for name in ['eof_analysis_with_track_id.py','attribute_track_ids_to_eof_extremes.py']:
        blob=subprocess.check_output(['git','-C',str(archive),'show',f'{frozen_commit}:src_energetic_eof/{name}'])
        sources[f'{archive}@{frozen_commit}:src_energetic_eof/{name}']={'sha256':hashlib.sha256(blob).hexdigest(),'preexisting_pin':True}
    csv('consistency_checks.csv',checks)
    outputs={str(p.relative_to(ROOT)):c.sha256_file(p) for p in OUT.glob('*.csv')}
    summary={'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'inputs':sources,'outputs':outputs,'method':'No maps, figures or clustering refitted. Small EOF eigendecompositions independently recomputed; stored assignments and centers audited.',
        'article_comparison':{'before_cyclones':6789,'before_rows':25000,'after_cyclones':3820,'after_rows':15829,'common_IDs':len(common_ids),'periods':'all archived, equal period weighting within cyclone'},
        'paired_control':{'cyclones_per_version':len(lp.track_id.unique()),'rows_per_version':len(lp),'periods':'four primary phases only','extremes':'screen four PCs, separate recomputed reference; not literal article'},
        'tracks':{'rows':len(tracks),'cyclones':tracks.track_id.nunique(),'months':tracks.date.dt.to_period('M').nunique(),'earliest':str(tracks.date.min()),'latest':str(tracks.date.max())},
        'current_vs_published_reference_sign':published_sign.tolist(),'corrected_only_metadata':repro_meta,'archived_cluster_count':archived_clusters.cluster.nunique(),
        'checks_passed':sum(x['status']=='PASS' for x in checks),'checks_failed':sum(x['status']=='FAIL' for x in checks),'checks_blocked':sum(x['status']=='BLOCKED' for x in checks),
        'source_code_sha256':{str(p.relative_to(ROOT)):c.sha256_file(p) for p in [Path(__file__),ROOT/'scripts/article_figures/common.py',ROOT/'scripts/article_figures/generate_article_comparison.py',ROOT/'scripts/article_figures/generate_corrected_article.py',ROOT/'scripts/article_figures/generate_comparison.py',ROOT/'scripts/article_figures/downstream_guards.py']},
        'warning':'Reference in current outputs means recomputed legacy, not verified published identity/orientation; no scientific corrections or artifact replacement authorized by this audit.'}
    c.write_json(OUT/'provenance.json',summary)
    print(mapping.to_string(index=False))
    print(pd.DataFrame(counts).to_string(index=False))
    print(pd.DataFrame(selections).to_string(index=False))
    print(pd.DataFrame(checks).query('status == "FAIL"').to_string(index=False))


if __name__ == '__main__':
    main()
