"""Regression tests for the author's script-first downstream workflow."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from scripts.article_figures import reproduce_downstream as r
from scripts.article_figures import common as c

ROOT=Path(__file__).resolve().parents[1]


def test_pyeof_s2_scaling_from_eigenvalues_and_joint_matching():
    rng=np.random.default_rng(723)
    x=pd.DataFrame(rng.normal(size=(90,24)),columns=c.EOF_TERMS)
    x['Ca']+=x.Ce*2
    pca=PCA(svd_solver='full').fit(StandardScaler().fit_transform((x-x.mean())/x.std()))
    reference=pca.components_[:8]*np.sqrt(pca.explained_variance_[:8,None])
    order=np.array([0,1,2,4,3,7,6,5]); signs=np.array([-1,1,-1,1,-1,1,1,-1])
    scores,loadings,mapping=r.total_pyeof(x.assign(track_id=np.arange(len(x))),reference[order]*signs[:,None])
    expected=pca.transform(StandardScaler().fit_transform((x-x.mean())/x.std()))[:,:8]*np.sqrt(pca.explained_variance_[:8])
    np.testing.assert_allclose(scores[r.PCS],expected[:,order]*signs,atol=1e-11)
    np.testing.assert_allclose(loadings,reference[order]*signs[:,None],atol=1e-11)
    assert sorted(mapping.corrected_raw_rank)==list(range(1,9))
    np.testing.assert_allclose(scores[r.PCS].std(),mapping.eigenvalue,atol=1e-11)


def test_figure12_panel_A_phase_aggregation_and_centroid_reconstruction():
    rng=np.random.default_rng(43)
    x=pd.DataFrame(rng.normal(size=(100,24)),columns=c.EOF_TERMS)
    x=x.assign(track_id=np.repeat(np.arange(50),2),period=['mature','decay']*50)
    x.loc[x.track_id<10,'period']='incipient'
    groups=pd.DataFrame({'track_id':range(24),'cluster':np.repeat([1,2,3,4],6)})
    centers=pd.DataFrame(rng.normal(size=(4,8)),columns=r.PCS).assign(cluster=range(1,5))
    load=pd.DataFrame(rng.normal(size=(8,24)),columns=c.EOF_TERMS)
    out=r.figure12_tables(x,groups,centers,load)
    a=out.query('panel == "A"').set_index('term').loc[c.EOF_TERMS]
    assert set(a.n)=={50}
    np.testing.assert_allclose(a['mean'],x.groupby('period')[c.EOF_TERMS].mean().mean())
    np.testing.assert_allclose(a['std'],x.groupby('period')[c.EOF_TERMS].std().mean())
    actual=out.query('cluster > 0').pivot(index='cluster',columns='term',values='mean')[c.EOF_TERMS]
    expected=centers[r.PCS].to_numpy()@load.to_numpy()+x.groupby('track_id')[c.EOF_TERMS].mean().mean().to_numpy()
    np.testing.assert_allclose(actual,expected)
    direct=x.merge(groups,on='track_id').groupby('cluster')[c.EOF_TERMS].mean()
    assert not np.allclose(actual,direct)


def test_intense_threshold_is_common_per_track_maximum():
    tracks=pd.DataFrame({'track_id':np.repeat(np.arange(100),2),'vor42':np.column_stack([np.arange(100),np.zeros(100)]).ravel()})
    ids,t=r.intense_ids(tracks,range(95))
    assert t==pytest.approx(89.1)
    assert ids==list(range(90,95))


def test_figure16_inputs_identical_to_frozen_5_8():
    actual=r.phase_synthesis_inputs()
    canonical,_=r.read_phase_product(ROOT)
    expected=canonical.query('version == "after" and reference_eof <= 4')
    pd.testing.assert_frame_equal(actual,expected)
    assert len(actual)==4*4*24
    for (_,mode),block in actual.groupby(['scope','reference_eof']):
        assert block.sign_alignment.nunique()==1
        assert block.raw_rank.nunique()==1


def test_legacy_gate_evidence_is_complete_and_passed():
    manifest=json.loads((r.GATE/'manifest.json').read_text())
    checks={x['item']:x for x in manifest['checks']}
    required=['PCs legacy','EOF +/- assignments','intense selection','4-cluster assignments','Figure 12 logic','Figure 13 logic','Figure 14 logic','Figure 16 logic']
    assert set(required)<=set(checks)
    assert all(x['passed'] for x in checks.values())
    assert checks['PCs legacy']['evidence']['max_absolute_error']<1e-9
    assert checks['EOF +/- assignments']['evidence']['symmetric_difference']==0
    assert checks['intense selection']['evidence']['n']==679
    assert checks['4-cluster assignments']['evidence']['mismatches']==0


def read_product(name):
    return pd.read_csv(r.CORRECTED/name,float_precision='round_trip')


def test_validated_figures_are_canonical_and_comparisons_match_sources():
    from scripts.article_figures import build_validated_comparison as comparison

    corrected=pd.read_csv(r.CORRECTED/'figure_manifest_09_16.csv').set_index('figure')
    panels=pd.read_csv(comparison.RESULTS/'figure_manifest.csv').set_index('figure_label').loc[range(9,17)]
    assert sorted(corrected.index)==list(range(9,17))
    assert sorted(panels.index)==list(range(9,17))
    for number in range(9,17):
        row=corrected.loc[number]
        panel=panels.loc[number]
        assert row.png.startswith('figures/corrected/article/fig_')
        assert c.sha256_file(ROOT/row.png)==row.png_sha256
        assert c.sha256_file(ROOT/row.pdf)==row.pdf_sha256
        assert panel.corrected_png==row.png
        assert panel.corrected_png_sha256==row.png_sha256
        for path_col,hash_col in [('png','png_sha256'),('pdf','pdf_sha256'),('published_png','published_png_sha256')]:
            assert c.sha256_file(ROOT/panel[path_col])==panel[hash_col]
    assert not (ROOT/'figures/corrected/article/validated_downstream').exists()
    obsolete=('fig_12a_','fig_12b_','fig_13_five_','fig_14_five_','fig_16a_','fig_16b_','fig_16c_','fig_16d_')
    assert not any(path.name.startswith(obsolete) for path in comparison.COMPARISON.glob('fig_*'))


def test_archived_assignments_and_intense_IDs_are_reproduced():
    config=json.loads((r.GATE/'manifest.json').read_text())
    archive=ROOT.parent/'energetic_patterns_cyclones_south_atlantic/csv_eofs_energetics_with_track/Total'
    if not archive.exists(): pytest.skip('archived external inputs not installed')
    scores=pd.read_csv(r.GATE/'eof_scores_total.csv')
    archived=pd.read_csv(archive/'pcs.csv')
    np.testing.assert_allclose(scores[r.PCS],archived[r.PCS],atol=1e-9,rtol=0)
    actual=c.assign_published_eof_extremes(scores)
    expected=pd.concat([pd.read_csv(archive/f'pcs_with_dominant_eof_{suffix}.csv').assign(sign=sign) for sign,suffix in [('positive','q90'),('negative','q10')]])
    assert r.memberships(actual)==r.memberships(expected)
    archived_cluster_path=next(Path(p) for p in config['sources'] if p.endswith('/pcs_with_clusters.csv'))
    clusters=pd.read_csv(archived_cluster_path)
    assert set(pd.read_csv(r.GATE/'intense_ids.csv').track_id)==set(clusters.track_id)
    clusters['cluster']+=1
    recreated,_,_,_=r.cluster(scores,clusters.track_id)
    assert r.match_labels(recreated,clusters)[1]==0


def test_corrected_selection_clusters_and_shared_memberships():
    ids=read_product('intense_ids.csv').track_id
    assert ids.nunique()==len(ids)==603
    scores=read_product('eof_scores_total.csv')
    assert len(scores)==3820
    clusters=read_product('cluster_assignments.csv')
    assert set(clusters.track_id)==set(ids)
    assert set(clusters.cluster)=={1,2,3,4}
    recreated,_,_,_=r.cluster(scores,ids)
    assert r.match_labels(recreated,clusters)[1]==0
    table=read_product('figure_cluster_memberships.csv')
    for k,group in clusters.groupby('cluster'):
        records=table.query('cluster == @k')
        assert set(records.figure)=={12,13,14}
        assert set(records.ids_sha256)=={r.ids_digest(group.track_id)}
        assert set(records.n)=={len(group)}
    assert set(read_product('figure12_values.csv').query('panel == "A"').n)=={3820}
    stats=read_product('figure14_statistics.csv').set_index('cluster')
    assert stats.n.to_dict()==clusters.groupby('cluster').size().to_dict()
    intensity=read_product('figure14_intensity.csv')
    np.testing.assert_allclose(stats.max_vor42_mean,intensity.groupby('cluster').vor42.mean())
    for prefix in ['season','region']:
        np.testing.assert_allclose(stats.filter(like=prefix+'_').sum(axis=1),100)


def test_corrected_PC_scale_and_mapping_are_recorded():
    mapping=read_product('total_eof_mapping.csv')
    assert sorted(mapping.corrected_raw_rank)==list(range(1,9))
    assert mapping.corrected_raw_rank.tolist()==[1,2,3,5,4,6,7,8]
    assert mapping.sign_alignment.tolist()==[1,-1,1,1,-1,-1,1,1]
    scores=read_product('eof_scores_total.csv')
    np.testing.assert_allclose(scores[r.PCS].std(),mapping.eigenvalue,rtol=1e-12)
    np.testing.assert_allclose(mapping.eigenvalue,mapping.explained_variance*24*3820/3819,rtol=1e-12)
    assert r.memberships(c.assign_published_eof_extremes(scores))==r.memberships(read_product('eof_extreme_assignments.csv'))


def test_saved_figure16_values_are_exactly_canonical():
    actual=read_product('figure16_loadings.csv')
    expected=r.phase_synthesis_inputs().reset_index(drop=True)
    pd.testing.assert_frame_equal(actual,expected,check_exact=True)


def test_density_preserves_original_temporal_policy_and_unclipped_values():
    from scripts.article_figures import density_color_scale as color

    metadata=read_product('density_metadata.csv')
    assert set(metadata.query('figure in [9,10]').months)=={505}
    assert metadata.query('figure == 13').months.nunique()==1
    for suffix,number in [('q90',9),('q10',10),('clusters',13)]:
        for k in range(1,5):
            field=read_product(f'density_{suffix}_{k}.csv.gz')
            assert len(field)==64*128
            assert field.lon.nunique()==128 and field.lat.nunique()==64
            assert field.density.ge(0).all()
            expected=metadata.query('figure == @number and group == @k').maximum.item()
            assert field.density.max()==pytest.approx(expected,abs=1e-12)
            row=metadata.query('figure == @number and group == @k').iloc[0]
            levels=np.array(json.loads(row.levels))
            assert row.interval_count==color.interval_count(number,k)==len(levels)-1
            assert np.all(np.diff(levels)>0)
            assert levels[-1]==round(expected,2)
            assert row.vmax==pytest.approx(levels[-1])


def test_density_level_spacing_prefers_half_unit_when_interval_count_allows():
    from scripts.article_figures.density_color_scale import density_levels

    preferred=density_levels(13.188339,13)
    assert len(preferred)==14 and preferred[-1]==13.19
    assert set(np.diff(preferred)[1:-1])=={1.0}
    compact=density_levels(3.4127068,10)
    assert len(compact)==11 and compact[-1]==3.41
    assert np.all(np.diff(compact)>0)


def test_phase_products_and_figures_have_valid_hashes():
    baseline=json.loads((ROOT/'results/comparison/article/phase_eof_matched/provenance.json').read_text())['outputs']
    assert any('fig_08' in path for path in baseline)
    for path,digest in baseline.items():
        assert c.sha256_file(ROOT/path)==digest,path


def test_final_provenance_hashes_and_figure_coverage():
    manifest=json.loads((r.CORRECTED/'provenance.json').read_text())
    assert manifest['status']=='VALIDATED_CORRECTED_CANDIDATES'
    assert {f['figure'] for f in manifest['figures']}==set(range(9,17))
    for figure in manifest['figures']:
        assert figure['legacy_input'] and figure['corrected_input'] and figure['tracks_input']
        assert figure['cluster_parameters']['K']==4
        assert figure['cluster_parameters']['effective_n_init']==1
        assert figure['intensity_threshold']==pytest.approx(10.353024)
    for name,digest in manifest['outputs'].items():
        assert c.sha256_file(ROOT/name)==digest,name
    for name,digest in manifest['sources'].items():
        if Path(name).exists(): assert c.sha256_file(Path(name))==digest,name
