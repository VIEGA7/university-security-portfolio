"""Meaningful checks of reconstructed numerical and ingestion behavior. No dependencies."""
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


maths = load('analysis', 'portfolio/multicriteria-analysis/analysis.py')
poisson = load('poisson', 'portfolio/ias-threat-model/poisson_model.py')
traffic = load('traffic', 'portfolio/opensearch-traffic/import_traffic.py')


class NumericalChecks(unittest.TestCase):
    def test_pareto_with_duplicates_and_directions(self):
        self.assertEqual(maths.pareto([(1,1),(2,2),(2,2),(3,0)]), [1,2,3])
        self.assertEqual(maths.pareto([(1,1),(2,2),(2,2),(3,0)], True), [0,3])
        self.assertEqual(maths.efficiency([(1,1)]), [1])

    def test_generated_projects_satisfy_region_and_optimality(self):
        rows = maths.kdz1(200)
        self.assertEqual(rows, maths.kdz1(200))
        self.assertEqual(len(rows), 200)
        for row in rows:
            x,y = row['f1'],row['f2']
            self.assertLessEqual((x-11)**2/484 + (y-11)**2/121, 1+1e-12)
            self.assertEqual(row['pareto'], row['efficiency'] == 1)

    def test_omega_is_subset_of_pareto(self):
        for row in maths.kdz2(200):
            if row['omega']:
                self.assertTrue(row['pareto'])

    def test_threshold_solution_matches_report(self):
        result = maths.kdz3()
        self.assertEqual(result['point'], (24.75,30.25))
        self.assertEqual(result['criteria'], [55,-44,-66])

    def test_concessions_match_report(self):
        stages = maths.kdz4()['stages']
        self.assertEqual(stages[0]['point'], (0,16.5))
        self.assertAlmostEqual(stages[1]['point'][0], 2/3)
        self.assertEqual(stages[2]['point'], (0,14.5))
        self.assertEqual(stages[2]['f3'], -43.5)

    def test_ideal_point_solution_is_feasible_and_locally_optimal(self):
        result = maths.kdz5()
        x,y = result['point']
        self.assertAlmostEqual(x+y, 22)
        self.assertAlmostEqual(x, 11.366666666666667)
        self.assertTrue(all(a*x+b*y <= c+1e-9 for a,b,c in maths.BASE))
        ideal = result['ideal']
        def cost(p):
            return sum((maths.dot(c,p)-f)**2 for c,f in zip(maths.CRITERIA,ideal))
        for dx,dy in [(-.01,.01),(.01,-.01),(0,.01),(.01,0)]:
            self.assertGreaterEqual(cost((x+dx,y+dy)),cost((x,y))-1e-9)

    def test_zero_attempts_is_degenerate_not_security_claim(self):
        self.assertEqual(poisson.pmf(0,0,30),1)
        self.assertEqual(poisson.pmf(1,0,30),0)
        self.assertEqual(poisson.at_least_one(0,30),0)

    def test_nonzero_poisson_probabilities_and_independent_actors(self):
        self.assertAlmostEqual(poisson.pmf(0,.11,30), math.exp(-3.3))
        self.assertAlmostEqual(sum(poisson.pmf(k,.11,30) for k in range(60)),1)
        row = poisson.scenario(11)[-1]
        self.assertGreater(row['p_any_two_independent_actors'],row['p_any_one_actor'])
        self.assertAlmostEqual(row['expected_attempts_two_actors'],9.9)
        with self.assertRaises(ValueError):
            poisson.pmf(1,-1,30)


class TrafficChecks(unittest.TestCase):
    def test_typed_fields_and_repeated_ips(self):
        row = {'frame.time_epoch':'1760000000.123456','ip.src':'192.0.2.1,192.0.2.2',
               'tcp.dstport':'443','frame.len':'512','http.host':''}
        doc = traffic.convert_row(row)
        self.assertEqual(doc['tcp']['dstport'],443)
        self.assertEqual(doc['ip']['src'],['192.0.2.1','192.0.2.2'])
        self.assertNotIn('http',doc)
        self.assertIsInstance(doc['frame']['time_epoch'],float)

    def test_rejects_missing_time_bad_ip_and_nonfinite_numbers(self):
        for row in [{}, {'frame.time_epoch':'nan'},
                    {'frame.time_epoch':'1','ip.src':'not-an-ip'},
                    {'frame.time_epoch':'1','tcp.dstport':'65536'}]:
            with self.assertRaises(ValueError):
                traffic.convert_row(row)

    def test_bulk_idempotency_and_error_detection(self):
        a = traffic.bulk_lines({'frame':{'len':1}},'packets-mbm-001','capture',1)
        self.assertEqual(a,traffic.bulk_lines({'frame':{'len':1}},'packets-mbm-001','capture',1))
        b = traffic.bulk_lines({'frame':{'len':1}},'packets-mbm-001','capture',2)
        self.assertNotEqual(a,b)
        self.assertTrue(a.endswith('\n'))
        for line in a.splitlines():
            json.loads(line)
        with self.assertRaises(RuntimeError):
            traffic.check_bulk({'errors':True,'items':[{'index':{'status':400}}]})

    def test_sample_and_query_json_are_valid(self):
        import csv
        with (ROOT/'portfolio/opensearch-traffic/sample.csv').open(newline='') as f:
            rows=list(csv.DictReader(f,delimiter=';'))
        self.assertEqual(len(rows),3)
        for row in rows:
            self.assertNotIn(None,row)
            traffic.convert_row(row)
        for line in (ROOT/'portfolio/opensearch-traffic/queries.http').read_text().splitlines():
            if line.startswith('{'):
                json.loads(line)


if __name__ == '__main__':
    unittest.main()
