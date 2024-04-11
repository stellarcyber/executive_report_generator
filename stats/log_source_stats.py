from helpers import gen_tenant_filter, gen_date_filter, gen_msgtype_filter

def log_source_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Stats: cumulative volume by log source, log source volume timeseries
    Gets stats bucketed by day in UTC.
    """

    if not org_id:
        index = 'aella-ade-*'
    else:
        index = f"stellar-index-v1-ade-{org_id}-*"


    msgtype_filter = gen_msgtype_filter(39)

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
            "log_source": {
              "terms": {
                "field": "stage_output.msg_origin_source.keyword",
                "order": {
                  "out_bytes_delta_total": "desc"
                },
                "size": 1000
              },
              "aggs": {
                "out_bytes_delta_total": {
                  "sum": {
                    "field": "stage_output.stats.bytes"
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
    log_source_stats = {'daily_volume_by_log_source': {'date': [], 'log_source': [], 'volume': []},
                    'cumulative_volume_by_log_source': {'log_source': [], 'volume': []},
                    'volume_per_day': {'date': [], 'volume': []},
                    'unique_log_sources': 0}

    cumulative_log_source_stats = {}
    for b in response['aggregations']['date']['buckets']:
        date = b['key_as_string'][0:10]
        daily_volume = 0
        for c in b['log_source']['buckets']:
            log_source_stats['daily_volume_by_log_source']['date'].append(date)
            log_source_stats['daily_volume_by_log_source']['log_source'].append(c['key'])
            log_source_stats['daily_volume_by_log_source']['volume'].append(c['out_bytes_delta_total']['value'])
            daily_volume = daily_volume + c['out_bytes_delta_total']['value']

            if c['key'] in cumulative_log_source_stats:
                cumulative_log_source_stats[c['key']] = cumulative_log_source_stats[c['key']] + c['out_bytes_delta_total']['value']
            else:
                cumulative_log_source_stats[c['key']] = c['out_bytes_delta_total']['value']

        log_source_stats['volume_per_day']['date'].append(date)
        log_source_stats['volume_per_day']['volume'].append(daily_volume)

    for c, v in sorted(cumulative_log_source_stats.items(), key=lambda item: item[1], reverse=True):
        log_source_stats['cumulative_volume_by_log_source']['log_source'].append(c)
        log_source_stats['cumulative_volume_by_log_source']['volume'].append(v)

    log_source_stats['unique_log_sources'] = len(cumulative_log_source_stats)

    return log_source_stats
