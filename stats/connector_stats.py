from helpers import gen_tenant_filter, gen_date_filter, gen_msgtype_filter

def connector_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Stats: cumulative volume by connector, connector volume timeseries
    Gets stats bucketed by day in UTC.
    """

    if not org_id:
        index = 'aella-ade-*'
    else:
        index = f"stellar-index-v1-ade-{org_id}-*"

    msgtype_filter = gen_msgtype_filter(40)

    if tenant:
      bool_filter = {
        "bool": {
          "filter": [
            gen_tenant_filter(tenant),
            msgtype_filter
          ]
        }
      }
    else:
      bool_filter = msgtype_filter

    query_filter = [bool_filter, gen_date_filter(start_date, end_date)]

    query = {
      "aggs": {
        "date": {
          "date_histogram": {
            "field": "timestamp",
            "calendar_interval": "1d",
            "time_zone": "+00:00",
            "min_doc_count": 0,
            "extended_bounds": {
              "min": start_date,
              "max": end_date
            }
          },
          "aggs": {
            "connector_name": {
              "terms": {
                "field": "msg_origin.source.keyword",
                "order": {
                  "out_bytes_delta_total": "desc"
                },
                "size": 1000
              },
              "aggs": {
                "out_bytes_delta_total": {
                  "sum": {
                    "field": "out_bytes_delta"
                  }
                }
              }
            }
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
    connector_stats = {'daily_volume_by_connector': {'date': [], 'connector_name': [], 'volume': []},
                    'cumulative_volume_by_connector': {'connector_name': [], 'volume': []},
                    'volume_per_day': {'date': [], 'volume': []},
                    'unique_connectors': 0}

    cumulative_connectors_stats = {}
    for b in response['aggregations']['date']['buckets']:
        date = b['key_as_string'][0:10]
        daily_volume = 0
        for c in b['connector_name']['buckets']:
            connector_stats['daily_volume_by_connector']['date'].append(date)
            connector_stats['daily_volume_by_connector']['connector_name'].append(c['key'])
            connector_stats['daily_volume_by_connector']['volume'].append(c['out_bytes_delta_total']['value'])
            daily_volume = daily_volume + c['out_bytes_delta_total']['value']
  
            if c['key'] in cumulative_connectors_stats:
                cumulative_connectors_stats[c['key']] = cumulative_connectors_stats[c['key']] + c['out_bytes_delta_total']['value']
            else:
                cumulative_connectors_stats[c['key']] = c['out_bytes_delta_total']['value']
  
        connector_stats['volume_per_day']['date'].append(date)
        connector_stats['volume_per_day']['volume'].append(daily_volume)

    for c, v in sorted(cumulative_connectors_stats.items(), key=lambda item: item[1], reverse=True):
        connector_stats['cumulative_volume_by_connector']['connector_name'].append(c)
        connector_stats['cumulative_volume_by_connector']['volume'].append(v)

    connector_stats['unique_connectors'] = len(cumulative_connectors_stats)

    return connector_stats
