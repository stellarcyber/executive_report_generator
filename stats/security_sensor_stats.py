from helpers import gen_tenant_filter, gen_date_filter, gen_msgtypes_filter, gen_sensor_type_filter, \
                    gen_timeseries_query, gen_unique_count_query, process_sensor_stats

def security_sensor_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Stats: (Flow and IDS & MW) cumulative volume for all security sensors, daily volume timeseries
    Gets stats bucketed by day in UTC.
    """

    if not org_id:
        index = 'aella-ade-*'
    else:
        index = f"stellar-index-v1-ade-{org_id}-*"

    tenant_filter = gen_tenant_filter(tenant)

    sensor_type_filter = {
      "bool": {
        "should": [
          {
            "match": {
              "feature": "sds"
            }
          }
        ],
        "minimum_should_match": 1
      }
    }

    msgtype_filter = gen_msgtypes_filter([37, 33])

    date_filter = gen_date_filter(start_date, end_date)

    if tenant:
      bool_filter = {
        "bool": {
          "filter": [
            tenant_filter,
            sensor_type_filter,
            msgtype_filter
          ]
        }
      }
    else:
      bool_filter = {
        "bool": {
          "filter": [
            sensor_type_filter,
            msgtype_filter
          ]
        }
      }

    query_filter = [bool_filter, date_filter]

    timeseries_query = gen_timeseries_query(start_date, end_date, query_filter, "security_sensor")
    unique_count_query = gen_unique_count_query(query_filter)

    response = api.es_search(index, timeseries_query)
    unique_count_response = api.es_search(index, unique_count_query)

    security_sensor_stats = {'daily_volume_by_feature': {'date': [], 'feature': [], 'volume': []},
                    'cumulative_volume_by_feature': {'feature': [], 'volume': []},
                    'volume_per_day': {'date': [], 'volume': []},
                    'unique_sensors': 0}

    cumulative_feature_stats = {}
    for b in response['aggregations']['date']['buckets']:
      date = b['key_as_string'][0:10]
      daily_volume = 0
      for f in b['feature']['buckets']:
        if f['key'] == 33:
          feature_name = 'Security Sensor - IDS & Malware'
        else:
          feature_name = 'Security Sensor - Traffic'
        security_sensor_stats['daily_volume_by_feature']['date'].append(date)
        security_sensor_stats['daily_volume_by_feature']['feature'].append(feature_name)
        security_sensor_stats['daily_volume_by_feature']['volume'].append(f['out_bytes_delta_total']['value'])
        daily_volume = daily_volume + f['out_bytes_delta_total']['value']

        if feature_name in cumulative_feature_stats:
          cumulative_feature_stats[feature_name] = cumulative_feature_stats[feature_name] + f['out_bytes_delta_total']['value']
        else:
          cumulative_feature_stats[feature_name] = f['out_bytes_delta_total']['value']

      security_sensor_stats['volume_per_day']['date'].append(date)
      security_sensor_stats['volume_per_day']['volume'].append(daily_volume)

    for f, v in sorted(cumulative_feature_stats.items(), key=lambda item: item[1], reverse=True):
      security_sensor_stats['cumulative_volume_by_feature']['feature'].append(f)
      security_sensor_stats['cumulative_volume_by_feature']['volume'].append(v)

    security_sensor_stats['unique_sensors'] = unique_count_response['aggregations']['unique_sensors']['value']

    return security_sensor_stats
