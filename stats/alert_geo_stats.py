import pycountry
from helpers import gen_tenant_filter, gen_date_filter, gen_score_filter

def alert_geo_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Stats: High fidelity alert count by country
    """

    alert_stats = {'high_fidelity_count_by_country': {'alpha_2': [], 'alpha_3': [], 'count': []}}

    if not org_id:
        index = 'aella-ser-*'
    else:
        index = f"stellar-index-v1-ser-{org_id}-*"

    # All Alerts counts
    tenant_filter = gen_tenant_filter(tenant)
    date_filter = gen_date_filter(start_date, end_date)
    score_filter = gen_score_filter("fidelity", "gte", 75)

    if tenant:
      bool_filter = {
        "bool": {
          "filter": [
            tenant_filter,
            score_filter
          ]
        }
      }
    else:
      bool_filter = score_filter

    query_filter = [bool_filter, date_filter]

    query = {
      "aggs": {
        "country": {
          "terms": {
            "field": "srcip_geo.countryCode.keyword",
            "order": {
              "_count": "desc"
            },
            "size": 1000
          }
        }
      },
      "size": 0,
      "query": {
        "bool": {
          "must": [],
          "filter": query_filter,
          "should": [],
          "must_not": []
        }
      }
    }

    response = api.es_search(index, query)
    for b in response['aggregations']['country']['buckets']:
      alert_stats['high_fidelity_count_by_country']['alpha_2'].append(b['key'])
      alert_stats['high_fidelity_count_by_country']['count'].append(b['doc_count'])
      country = pycountry.countries.get(alpha_2=b['key'])
      if country:
        alert_stats['high_fidelity_count_by_country']['alpha_3'].append(country.alpha_3)
      else:
        alert_stats['high_fidelity_count_by_country']['alpha_3'].append('')

    return alert_stats
