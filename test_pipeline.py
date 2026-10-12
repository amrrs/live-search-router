import unittest,tempfile,os,json
from unittest.mock import patch
from engine import answer
from router import HeuristicRouter
from serpapi_client import SerpApiClient
class Response:
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self):return json.dumps({'organic_results':[{'title':'Evidence','link':'https://example.com/source','snippet':'A fact.'}]}).encode()
class RobustnessTests(unittest.TestCase):
 def test_adversarial_freshness_and_token_boundaries(self):
  router=HeuristicRouter()
  for q in ['Who is the Prime Minister of India?','Is it raining in Mumbai?','Who is the CEO of Apple?','Best pizza places in Bengaluru','Tell me about an unfamiliar topic','Latest Python version','Explain current exchange rates']:
   self.assertNotEqual(router.route(q).route,'direct',q)
  for q in ['Explain how photosynthesis works','What is the formula for area?','What does HTTP stand for?']:
   self.assertEqual(router.route(q).route,'direct',q)
 def test_direct_does_not_construct_search_client(self):
  with patch.dict(os.environ,{},clear=True),patch('engine.SerpApiClient') as client:
   r=answer('What is the capital of France?');client.assert_not_called();self.assertEqual(r['searches_used'],0)
 def test_sqlite_cache_hit_and_expiry(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'SEARCH_CACHE_PATH':tmp+'/cache.db','SEARCH_CACHE_TTL':'300'}),patch('urllib.request.urlopen',return_value=Response()) as network:
   first=SerpApiClient('test');first.search('latest release');self.assertEqual(first.network_calls,1)
   second=SerpApiClient('test');second.search('latest release');self.assertEqual(second.cache_hits,1);self.assertEqual(second.network_calls,0);self.assertEqual(network.call_count,1)
   second.cache_ttl=0;second.search('latest release');self.assertEqual(network.call_count,2)
 def test_empty_evidence_abstains(self):
  class Empty:
   network_calls=1;cache_hits=0;trace=[]
   def search(self,*a,**kw):return {}
  with patch.dict(os.environ,{},clear=True):r=answer('latest release',client=Empty())
  self.assertIn('empty_retrieval',r['warnings']);self.assertIn('cannot provide',r['answer'])
 def test_invalid_citations_fall_back(self):
  class Client:
   network_calls=1;cache_hits=0;trace=[]
   def search(self,*a,**kw):return {'organic_results':[{'title':'Source','link':'https://example.com','snippet':'Fact'}]}
  with patch('engine._llm_available',return_value=True),patch('engine._llm_synthesize',return_value='Invented reference [99]'):
   r=answer('latest release',client=Client())
  self.assertIn('invalid_citations: used extractive fallback',r['warnings']);self.assertNotIn('[99]',r['answer'])
if __name__=='__main__':unittest.main()
