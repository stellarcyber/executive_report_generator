from helpers import gen_tenant_filter, gen_date_filter, gen_msgtypes_filter, gen_sensor_type_filter, \
                    gen_timeseries_query, gen_unique_count_query, process_sensor_stats

def linux_sensor_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Stats: cumulative volume for all linux sensors, daily volume timeseries
    Gets stats bucketed by day in UTC.
    """

    if not org_id:
        index = 'aella-ade-*'
    else:
        index = f"stellar-index-v1-ade-{org_id}-*"

    tenant_filter = gen_tenant_filter(tenant)
    sensor_type_filter = gen_sensor_type_filter("agent") 
    msgtype_filter = gen_msgtypes_filter([34, 37])
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

    timeseries_query = gen_timeseries_query(start_date, end_date, query_filter)
    unique_count_query = gen_unique_count_query(query_filter)

    response = api.es_search(index, timeseries_query)
    unique_count_response = api.es_search(index, unique_count_query)

    linux_sensor_stats = process_sensor_stats(response, unique_count_response)

    return linux_sensor_stats
