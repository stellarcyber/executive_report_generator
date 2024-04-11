import datetime
from helpers import gen_tenant_filter, gen_date_filter, gen_base_count_query, \
                    gen_score_filter, gen_top_query

def alert_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Stats: daily timeseries, top 3 by score
    """

    alert_stats = {'count_per_day': {'date': [], 'count': []},
        'critical_count_per_day': {'date': [], 'count': []},
        'high_fidelity_count_per_day': {'date': [], 'count': []},
        'top_3_alerts': [], 'cumulative_alert_count': 0, 'cumulative_critical_alert_count': 0,
        'cumulative_high_fidelity_alert_count': 0, 'unique_alert_type_count': 0}

    if not org_id:
        index = 'aella-ser-*'
    else:
        index = f"stellar-index-v1-ser-{org_id}-*"

    # All Alerts counts
    tenant_filter = gen_tenant_filter(tenant)
    date_filter = gen_date_filter(start_date, end_date)

    if tenant:
        query_filter = [tenant_filter, date_filter]
    else:
        query_filter = date_filter

    base_count_query = gen_base_count_query(start_date, end_date, query_filter)

    count_response = api.es_search(index, base_count_query)
    for b in count_response['aggregations']['date']['buckets']:
        alert_stats['count_per_day']['date'].append(b['key_as_string'][0:10])
        alert_stats['count_per_day']['count'].append(b['doc_count'])
    alert_stats['cumulative_alert_count'] = sum(alert_stats['count_per_day']['count'])

    # Critical Alert counts
    score_filter = gen_score_filter("event_score", "gte", 75)

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

    base_count_query = gen_base_count_query(start_date, end_date, query_filter)

    critical_count_response = api.es_search(index, base_count_query)
    for b in critical_count_response['aggregations']['date']['buckets']:
        alert_stats['critical_count_per_day']['date'].append(b['key_as_string'][0:10])
        alert_stats['critical_count_per_day']['count'].append(b['doc_count'])
    alert_stats['cumulative_critical_alert_count'] = sum(alert_stats['critical_count_per_day']['count'])

    # High Fidelity Alert counts
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

    base_count_query = gen_base_count_query(start_date, end_date, query_filter)

    critical_count_response = api.es_search(index, base_count_query)
    for b in critical_count_response['aggregations']['date']['buckets']:
      alert_stats['high_fidelity_count_per_day']['date'].append(b['key_as_string'][0:10])
      alert_stats['high_fidelity_count_per_day']['count'].append(b['doc_count'])
    alert_stats['cumulative_high_fidelity_alert_count'] = sum(alert_stats['high_fidelity_count_per_day']['count'])

    # Unique alert type count
    tenant_filter = gen_tenant_filter(tenant)
    date_filter = gen_date_filter(start_date, end_date)

    if tenant:
      query_filter = [tenant_filter, date_filter]
    else:
      query_filter = date_filter

    base_count_query = {
      "aggs": {
        "alert_type": {
          "terms": {
            "field": "xdr_event.name.keyword",
            "order": {
              "_count": "desc"
            },
            "size": 10000
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

    count_response = api.es_search(index, base_count_query)
    alert_stats['unique_alert_type_count'] = len(count_response['aggregations']['alert_type']['buckets'])

    # Top 3 by score
    tenant_filter = gen_tenant_filter(tenant)
    date_filter = gen_date_filter(start_date, end_date)

    if tenant:
      query_filter = [tenant_filter, date_filter]
    else:
      query_filter = date_filter

    top_query = gen_top_query("event_score", query_filter)

    top_response = api.es_search(index, top_query)
    for h in top_response['hits']['hits']:
      record = {
        'datetime': datetime.datetime.fromtimestamp(h['_source']['timestamp']//1000).strftime('%c'),
        'xdr_event.display_name': h['_source']['xdr_event']['display_name'],
        'event_score': h['_source']['event_score'],
        #'xdr_event.tactic_name': h['_source']['xdr_event']['tactic']['name'],
        'xdr_event.tactic_name': h.get('_source',{}).get('xdr_event',{}).get('tactic',{}).get('name', "null"),
        #'xdr_event.killchain_stage': h['_source']['xdr_event']['xdr_killchain_stage'],
        'xdr_event.killchain_stage': h.get('_source',{}).get('xdr_event',{}).get('xdr_killchain_stage', "null"),
        #'xdr_event.technique_name': h['_source']['xdr_event']['technique']['name'],
        'xdr_event.technique_name': h.get('_source',{}).get('xdr_event',{}).get('technique',{}).get('name', "null"),
        #'killchain_overview_print': 'Stage: {}<br>Tactic: {}<br>Technique: {}'.format(h['_source']['xdr_event']['xdr_killchain_stage'], h['_source']['xdr_event']['tactic']['name'], h['_source']['xdr_event']['technique']['name'])
      }
      record['killchain_overview_print'] = 'Stage: {}<br>Tactic: {}<br>Technique: {}'.format(record['xdr_event.killchain_stage'], record['xdr_event.tactic_name'], record['xdr_event.technique_name'])
      if 'description' in h['_source']['xdr_event']:
        record['xdr_event.description'] = h['_source']['xdr_event']['description']

      alert_stats['top_3_alerts'].append(record)

    return alert_stats
