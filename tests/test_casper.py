"""Tests exercise the supplied survey and graph invariants, not UI dummy records."""
from pathlib import Path
import sys
import io
import os
import unittest
from dataclasses import replace
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'NITW_Roommate_Optimizer'))
from src.data.data_cleaner import load_data, PUBLIC_PATH, NUMERIC, HOBBIES, public_measurements
from src.data.feature_engine import compute_cs, compute_cf, score_matrices
from src.graph.graph_builder import Settings, build_graph
from src.graph.matcher import casper_matching, max_weight_matching
from src.pipeline import run_pipeline, export_results, lambda_analysis
from src.realtime.api import app

class CasperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df,cls.audit=load_data(PUBLIC_PATH)
        cls.result=run_pipeline(cls.df)

    def test_real_data_integrity_and_privacy(self):
        raw=pd.read_csv(PUBLIC_PATH)
        self.assertEqual(len(raw),98)
        self.assertFalse(set(raw.columns)&{'name','email','Email','Full Name','branch','respondent_id','submission_id'})
        self.assertEqual(raw.participant_id.nunique(),98)
        self.assertFalse(raw[NUMERIC].isna().any().any())
        self.assertEqual(self.audit.numeric_features,11)

    def test_original_scaling_is_preserved(self):
        for feature in NUMERIC:
            np.testing.assert_allclose(self.df[feature+'_norm'],self.df[feature]/10)

    def test_matrix_matches_original_scalar_compatibility(self):
        cs,cf=score_matrices(self.df)
        for i,j in [(0,1),(14,70),(31,52),(8,9)]:
            self.assertAlmostEqual(cs[i,j],compute_cs(self.df.iloc[i],self.df.iloc[j]),12)
            self.assertAlmostEqual(cf[i,j],compute_cf(self.df.iloc[i],self.df.iloc[j]),12)
        np.testing.assert_allclose(cs,cs.T)
        np.testing.assert_allclose(cf,cf.T)

    def test_constraints_hold_after_cpp_refinement(self):
        r=self.result;used=[]
        for a,b in r['pairs']:
            self.assertTrue(r['graph']['allowed'][a,b])
            self.assertEqual(self.df.iloc[a].gender,self.df.iloc[b].gender)
            self.assertLessEqual(r['graph']['cf'][a,b],r['settings']['threshold'])
            used.extend([a,b])
        self.assertEqual(len(used),len(set(used)))
        self.assertEqual(set(used)|set(r['unmatched']),set(range(98)))

    def test_fairness_is_pareto_safe_on_real_data(self):
        for lam in [0,.5,1,2]:
            r=run_pipeline(self.df,Settings(lambda_=lam),compare=False)
            greedy=r['comparison'].iloc[0];final=r['comparison'].iloc[1]
            self.assertGreaterEqual(final['total']+1e-8,greedy['total'])
            self.assertGreaterEqual(final['minimum']+1e-8,greedy['minimum'])
            self.assertLessEqual(final['variance']-1e-8,greedy['variance'])

    def test_cpp_checks_both_swap_alternatives(self):
        # A graph fixture tests a solver invariant; it is never shipped as survey data.
        edges=[(0,1,10),(2,3,1),(0,3,6),(1,2,6)]
        r=casper_matching(4,edges,fairness=False)
        self.assertEqual({tuple(sorted(p)) for p in r['pairs']},{(0,3),(1,2)})
        self.assertEqual(r['swaps'],1)

    def test_pruned_swap_never_reappears(self):
        r=casper_matching(4,[(0,1,.8),(2,3,.1),(0,3,.95)])
        self.assertEqual(r['pairs'],[[0,3]])

    def test_deterministic_matching(self):
        r=run_pipeline(self.df,compare=False)
        self.assertEqual(self.result['pairs'],r['pairs'])

    def test_empty_graph_and_odd_cohort(self):
        r=casper_matching(5,[])
        self.assertEqual(r['pairs'],[])
        r=run_pipeline(self.df.iloc[:9].copy(),compare=False)
        self.assertEqual(len(r['unmatched'])%2,1)

    def test_online_update_preserves_existing_pairs(self):
        old=self.df.iloc[:90].copy();r=run_pipeline(old,compare=False)
        locks=[(old.iloc[a].participant_id,old.iloc[b].participant_id) for a,b in r['pairs']]
        updated=run_pipeline(self.df,locked_pairs=locks,compare=False)
        actual={frozenset((self.df.iloc[a].participant_id,self.df.iloc[b].participant_id)) for a,b in updated['pairs']}
        self.assertTrue(all(frozenset(p) in actual for p in locks))

    def test_invalid_locked_pairs_rejected(self):
        with self.assertRaises(ValueError):run_pipeline(self.df,locked_pairs=[('P001','P001')])
        with self.assertRaises(ValueError):run_pipeline(self.df,locked_pairs=[('absent','P001')])

    def test_missing_fields_and_invalid_values_rejected(self):
        public=public_measurements(self.df)
        with self.assertRaises(ValueError):load_data(public.drop(columns='sleep_time').to_csv(index=False).encode())
        public.loc[0,'sleep_time']=20
        with self.assertRaises(ValueError):load_data(public.to_csv(index=False).encode())

    def test_missing_outcome_rating_allowed_for_new_responses(self):
        public=public_measurements(self.df)
        public.loc[0,'current_sat']=np.nan
        frame,_=load_data(public.to_csv(index=False).encode())
        self.assertTrue(np.isnan(frame.iloc[0].current_sat))

    def test_settings_reject_nonfinite_and_unbounded_passes(self):
        for bad in [Settings(lambda_=float('nan')),Settings(max_sweeps=100),Settings(threshold=1.1)]:
            with self.assertRaises(ValueError):bad.validate()

    def test_exact_reference_and_pair_count_are_reported(self):
        table=self.result['comparison']
        self.assertEqual(set(table.algorithm),{'Heap greedy','CASPER','Blossom reference'})
        cpp=table.iloc[1];exact=table.iloc[2]
        self.assertGreaterEqual(exact['pairs'],cpp['pairs'])
        if exact['pairs']==cpp['pairs']:self.assertGreaterEqual(exact['total']+1e-8,cpp['total'])

    def test_export_contains_no_direct_identifiers(self):
        export=export_results(self.result,self.df)
        parsed=pd.read_csv(io.BytesIO(export))
        count=2*int((parsed.Status=='Paired').sum())+int((parsed.Status=='Unmatched').sum())
        self.assertEqual(count,98)
        self.assertNotIn('@',export.decode())

    def test_adaptive_policy_uses_measured_common_metrics(self):
        table,recommended=lambda_analysis(self.df)
        self.assertEqual(len(table),9)
        best=table.sort_values(['pairs','conflict','compatibility','lambda'],ascending=[False,True,False,True]).iloc[0]
        self.assertEqual(recommended,best['lambda'])

    def test_api_is_locked_without_credentials(self):
        old=os.environ.pop('CASPER_API_KEY',None)
        try:
            client=TestClient(app)
            self.assertEqual(client.get('/health').status_code,200)
            request={'records':public_measurements(self.df.iloc[:4]).to_dict(orient='records')}
            self.assertEqual(client.post('/run_matching/',json=request).status_code,503)
            os.environ['CASPER_API_KEY']='test-only-local-value'
            self.assertEqual(client.post('/run_matching/',json=request).status_code,401)
            response=client.post('/run_matching/',json=request,headers={'X-API-Key':'test-only-local-value'})
            self.assertEqual(response.status_code,200)
            self.assertIn('metrics',response.json())
        finally:
            os.environ.pop('CASPER_API_KEY',None)
            if old is not None:os.environ['CASPER_API_KEY']=old

if __name__=='__main__':unittest.main()
