"""Propagation regressions and explicit scientific blockers; no heavy rendering."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.article_figures import common as c

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / 'results/comparison/article'
REPRO = ROOT / 'results/corrected/article/reproduction'
AUDIT = COMP / 'total_eof_audit'
PCS = [f'PC{i}' for i in range(1, 9)]


def patterns():
    reference = pd.read_csv(COMP / 'eof_loadings_total.csv').query('version == "before"')
    reference = reference.pivot(index='eof', columns='term', values='loading').loc[range(1,9),c.EOF_TERMS].to_numpy()
    raw = pd.read_csv(REPRO / 'eof_loadings_total.csv').set_index('eof').loc[range(1,9),c.EOF_TERMS].to_numpy()
    scores = pd.read_csv(REPRO / 'eof_scores_total.csv')
    variance = pd.read_csv(REPRO / 'eof_variance_total.csv').explained_variance_pct.to_numpy()/100
    return reference, raw, scores, variance


def test_total_matching_joint_loadings_scores_variance():
    reference, raw, scores, variance = patterns()
    loading, aligned, ev, rank, correlation = c.align_eofs(reference, raw, scores[PCS].to_numpy(), variance)
    assert rank.tolist() == [1,2,3,5,4,6,7,8]
    assert sorted(rank) == list(range(1,9))
    signs = np.sign((loading*raw[rank-1]).sum(axis=1))
    np.testing.assert_array_equal(signs, [1,1,-1,1,1,1,1,1])
    np.testing.assert_array_equal(loading, raw[rank-1]*signs[:,None])
    np.testing.assert_array_equal(aligned, scores[PCS].to_numpy()[:,rank-1]*signs)
    np.testing.assert_array_equal(ev, variance[rank-1])
    saved = pd.read_csv(COMP / 'eof_scores_total.csv').query('version == "after"').set_index('track_id').loc[scores.track_id,PCS]
    np.testing.assert_allclose(aligned,saved,atol=1e-6,rtol=0)
    assert correlation.min() > .49  # numerical result only; not a scientific acceptance criterion


@pytest.mark.parametrize('flipped_mode', range(8))
def test_extremes_invariant_to_arbitrary_raw_sign_after_alignment(flipped_mode):
    reference, raw, scores, variance = patterns()
    x = scores[PCS].to_numpy()
    baseline = c.align_eofs(reference,raw,x,variance)
    flips=np.ones(8); flips[flipped_mode]=-1
    flipped=c.align_eofs(reference,raw*flips[:,None],x*flips,variance)
    for a,b in zip(baseline,flipped): np.testing.assert_allclose(a,b,atol=1e-12,rtol=0)
    def assign(result):
        return c.assign_published_eof_extremes(pd.DataFrame(result[1],columns=PCS).assign(track_id=scores.track_id))
    pd.testing.assert_frame_equal(assign(baseline),assign(flipped))


def test_figures_9_11_assignments_follow_reference_columns():
    scores=pd.read_csv(COMP/'eof_scores_total.csv')
    saved=pd.read_csv(COMP/'eof_extreme_assignments.csv')
    keys=['track_id','sign','dominant_eof']
    for version in ['before','after']:
        actual=c.assign_published_eof_extremes(scores.query('version == @version'))
        expected=saved.query('version == @version')
        pd.testing.assert_frame_equal(actual[keys].sort_values(keys).reset_index(drop=True),expected[keys].sort_values(keys).reset_index(drop=True))
    # A permutation mistake cannot pass merely because dimensions match.
    _,_,raw,_=patterns()
    wrong=c.assign_published_eof_extremes(raw)
    assert set(map(tuple,wrong[keys].to_numpy())) != set(map(tuple,saved.query('version == "after"')[keys].to_numpy()))


def test_superseded_five_cluster_fit_is_disabled():
    with pytest.raises(ValueError, match='BLOCKED superseded five-cluster'):
        c.independent_intense_pc_clusters(None, None)


def test_author_confirmed_four_archived_clusters():
    assert json.loads((REPRO/'intense_pc_cluster_metadata.json').read_text())['clusters']==4


@pytest.mark.xfail(strict=True, reason='BLOCKED: comparison selects q90 of track records, not q90 of per-cyclone maxima.')
def test_comparison_intense_criterion_matches_published_script():
    table=pd.read_csv(AUDIT/'intense_selection_audit.csv').set_index('definition')
    assert table.loc['current_comparison_track_rows','threshold']==pytest.approx(table.loc['published_script_all_track_maxima','threshold'])


@pytest.mark.xfail(strict=True, reason='BLOCKED: current legacy reference reverses published modes 2, 3, 5, 6.')
def test_current_reference_preserves_archived_published_signs():
    assert pd.read_csv(AUDIT/'total_eof_mapping.csv').current_reference_sign_vs_published.eq(1).all()


def test_superseded_five_cluster_renderers_are_disabled(tmp_path):
    from scripts.article_figures import generate_article_comparison as g
    for call in [lambda:g.fig12(None,None,None,tmp_path/'a',tmp_path/'b'),
                 lambda:g.fig13(None,None,tmp_path/'c'),
                 lambda:g.fig14(None,None,None,tmp_path/'d')]:
        with pytest.raises(ValueError, match='BLOCKED superseded five-cluster'):
            call()
    assert not list(tmp_path.iterdir())


def test_figure11_bars_equal_audit_tables(monkeypatch,tmp_path):
    from scripts.article_figures import generate_comparison as g
    assignments=pd.read_csv(COMP/'eof_extreme_assignments.csv')
    tracks_path=ROOT/'data/external/swell/paper_energy_patterns/tracks_SAt_filtered_with_energetics_processed.csv'
    if not tracks_path.exists():pytest.skip('Pinned track file not installed')
    pin=json.loads((COMP/'provenance.json').read_text())['tracks_sha256']
    assert c.sha256_file(tracks_path)==pin
    tracks=pd.read_csv(tracks_path); tracks.date=pd.to_datetime(tracks.date)
    tracks['lon vor']=np.where(tracks['lon vor']>180,tracks['lon vor']-360,tracks['lon vor'])
    first=c.first_track_rows(tracks)
    calls=[]
    monkeypatch.setattr(g,'_grouped_bars',lambda ax,values,categories,title:calls.append((values,categories)))
    monkeypatch.setattr(g,'save_pair',lambda fig,*a:g.plt.close(fig))
    g.fig11(assignments,first,tmp_path/'fig11')
    table=pd.read_csv(AUDIT/'figure11_composition.csv').query('workflow == "comparison"')
    for i,(v,sg,category) in enumerate((v,sg,cat) for v in ['before','after'] for sg in ['positive','negative'] for cat in ['region','season']):
        values,categories=calls[i]
        expected=table.query('version == @v and sign == @sg and category == @category').pivot(index='reference_eof_or_raw_rank',columns='label',values='percentage').loc[range(1,5),categories]
        np.testing.assert_allclose(values,expected,atol=1e-9,rtol=0)


def test_figure16_renderers_fail_before_side_effects(tmp_path):
    from scripts.article_figures import generate_article_comparison as article
    from scripts.article_figures import generate_corrected_article as corrected
    from scripts.article_figures import generate_comparison as paired
    for call in [lambda:article.fig16(1,None,None,None,tmp_path/'article'),lambda:corrected.render_syntheses(None,None,None,tmp_path,tmp_path),lambda:paired.fig16(1,None,tmp_path/'paired')]:
        with pytest.raises(ValueError,match='BLOCKED Figure 16 / INVALID_AS_REPLACEMENT'):call()
    assert not list(tmp_path.iterdir())


def test_figure16_full_workflows_fail_before_input_or_output_access(monkeypatch,tmp_path):
    import sys
    from scripts.article_figures import generate_article_comparison as article
    from scripts.article_figures import generate_corrected_article as corrected
    from scripts.article_figures import generate_comparison as paired
    for module in [article,corrected,paired]:
        args=['audit'] if module is corrected else ['audit','--legacy-cache','absent','--corrected-cache','absent','--tracks','absent','--output-root',str(tmp_path)]
        monkeypatch.setattr(sys,'argv',args)
        with pytest.raises(ValueError,match='BLOCKED Figure 16'):module.main()
    assert not list(tmp_path.iterdir())


def test_existing_outputs_and_phase_baseline_remain_frozen():
    snapshot=json.loads((AUDIT/'frozen_outputs.json').read_text())
    assert len(snapshot)==190
    changed=[p for p,digest in snapshot.items() if c.sha256_file(ROOT/p)!=digest]
    assert changed==[]


def test_total_eof_function_propagates_joint_alignment_on_independent_populations():
    rng=np.random.default_rng(321)
    legacy=pd.DataFrame(rng.normal(size=(80,24)),columns=c.EOF_TERMS).assign(track_id=np.arange(80))
    corrected=pd.DataFrame(rng.normal(size=(57,24)),columns=c.EOF_TERMS).assign(track_id=np.arange(57))
    b=c.compute_eof(legacy.set_index('track_id'),c.EOF_TERMS)
    a=c.compute_eof(corrected.set_index('track_id'),c.EOF_TERMS)
    expected=c.align_eofs(b[1],a[1],a[2],a[3])
    loadings,variance,scores=c.independent_total_eof(legacy,corrected)
    assert scores.groupby('version').size().to_dict()=={'after':57,'before':80}
    actual=loadings.query('version == "after"').pivot(index='eof',columns='term',values='loading')[c.EOF_TERMS]
    np.testing.assert_allclose(actual,expected[0])
    np.testing.assert_allclose(scores.query('version == "after"')[PCS],expected[1])
    np.testing.assert_allclose(variance.query('version == "after"').explained_variance_pct,100*expected[2])
