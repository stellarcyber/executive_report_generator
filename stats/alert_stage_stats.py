import numpy as np
from helpers import gen_tenant_filter, gen_date_filter, \
                    gen_score_filter, gen_timeseries_query

def alert_stage_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    High fidelity counts by stage and by day
    """
    if not org_id:
        index = 'aella-ser-*'
    else:
        index = f"stellar-index-v1-ser-{org_id}-*"

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
    query = gen_timeseries_query(start_date, end_date, query_filter, "xdr_killchain_stage")

    response = api.es_search(index, query)
    stage = ['Initial Attempts', 'Persistent Foothold', 'Exploration', 'Propagation', 'Exfiltration & Impact']
    stage_index = {'Initial Attempts': 0, 'Persistent Foothold': 1, 'Exploration': 2, 'Propagation': 3, 'Exfiltration & Impact': 4}

    alert_stats = {'daily_high_fidelity_count_by_stage': {'date': [], 'stage': [],
          'count_matrix': np.zeros(shape=(len(stage), len(response['aggregations']['date']['buckets'])))}}

    for i in range(0, len(response['aggregations']['date']['buckets'])):
      b = response['aggregations']['date']['buckets'][i]
      alert_stats['daily_high_fidelity_count_by_stage']['date'].append(b['key_as_string'][0:10])

      for s in b['stage']['buckets']:
        if s['key'] in stage_index:
          # Adds into future z matrix for plots, stages by row, date by column
          alert_stats['daily_high_fidelity_count_by_stage']['count_matrix'][stage_index[s['key']], i] = s['doc_count']

    alert_stats['daily_high_fidelity_count_by_stage']['stage'] = stage

    return alert_stats
