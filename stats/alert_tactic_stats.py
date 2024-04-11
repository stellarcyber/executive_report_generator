import numpy as np
from helpers import gen_tenant_filter, gen_date_filter, \
                    gen_score_filter, gen_timeseries_query

def alert_tactic_stats(api, start_date, end_date, tenant=None, org_id=None):
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

    query = gen_timeseries_query(start_date, end_date, query_filter, "alert_tactic")

    response = api.es_search(index, query)

    stage_tactic_counts = {'Initial Attempts': {}, 'Persistent Foothold': {}, 'Exploration': {}, 'Propagation': {}, 'Exfiltration & Impact': {}}
    stage_tactic_list = [[], []]
    stage_order = ['Initial Attempts', 'Persistent Foothold', 'Exploration', 'Propagation', 'Exfiltration & Impact']
    dates = set([])

    # fill in stage_tactic_naames and counts
    for b in response['aggregations']['date']['buckets']:
      for s in b['stage']['buckets']:
        for t in s['tactic']['buckets']:
          if s['key'] in stage_tactic_counts:
            if t['key'] in stage_tactic_counts[s['key']]:
              stage_tactic_counts[s['key']][t['key']][b['key_as_string'][0:10]] = t['doc_count']
            else:
              stage_tactic_counts[s['key']][t['key']] = {b['key_as_string'][0:10]: t['doc_count']}
          dates.add(b['key_as_string'][0:10])

    # Create flattened 2d list of tactics and stages
    for s in stage_order:
      for t in stage_tactic_counts[s].keys():
        stage_tactic_list[0].append(s)
        stage_tactic_list[1].append(t)

    # create zeroed out matrix
    stage_tactic_matrix =  np.zeros(shape=(len(stage_tactic_list[0]), len(dates)))
    dates_sorted = sorted(dates)

    # Fill in matrix
    for i in range(0, len(stage_tactic_list[0])):
      for k in range(0, len(dates_sorted)):
        if dates_sorted[k] in stage_tactic_counts[stage_tactic_list[0][i]][stage_tactic_list[1][i]]:
          stage_tactic_matrix[i,k] = stage_tactic_counts[stage_tactic_list[0][i]][stage_tactic_list[1][i]][dates_sorted[k]]


    alert_stats = {
      'stage_tactic_counts': stage_tactic_counts, 'stage_tactic_list': stage_tactic_list, 'dates_sorted': dates_sorted,
      'stage_tactic_matrix': stage_tactic_matrix
    }

    return alert_stats
