from collections import OrderedDict
import statistics
from helpers import gen_tenant_filter, gen_date_filter
import acgs

def volume_stats(api, start_date, end_date, daily_date_scale, tenant=None, org_id=None):
    """
    Stats: average daily volume, daily volume timeseries
    Gets stats bucketed by day in UTC.
    """
    volume_stats = {'volume_per_day': {'date': [], 'volume': []},
                    'average_daily_volume': 0}

    # SaaS
    if org_id:
        # init data structure
        volume_data = OrderedDict()
        for key in daily_date_scale:
            volume_data[key] = 0

        volume_usage = acgs.get_volume_usage(org_id, start_date, end_date)
        if tenant != None and len(tenant) > 0:
            for _date, vol in volume_usage["by_tenant"][tenant].items():
                volume_data[_date] = vol*1000*1000*1000
        # all tenants
        else:
            for _date, entry in volume_usage["by_date"].items():
                volume_data[_date] = sum(entry.values())*1000*1000*1000

        volume_stats['volume_per_day']['date'] = volume_data.keys()
        volume_stats['volume_per_day']['volume'] = list(volume_data.values())
    # Onprem
    else:
        index = 'aella-metalicense-1'
        query_filter = [gen_tenant_filter(tenant), gen_date_filter(start_date, end_date)]

        query = {
          "aggs": {
            "date": {
              "date_histogram": {
                "field": "timestamp",
                "calendar_interval": "1d",
                "min_doc_count": 0,
                "extended_bounds": {
                  "min": start_date,
                  "max": end_date
                }
              },
              "aggs": {
                "volume": {
                  "max": {
                    "field": "throughput"
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
        # for b in response['aggregations']['date']['buckets']:
        for b in response.get('aggregations', {}).get('date', {}).get('buckets', {}):
          volume_stats['volume_per_day']['date'].append(b['key_as_string'][0:10])
          if b['volume']['value']:
            volume_stats['volume_per_day']['volume'].append(b['volume']['value']*1000*1000*1000)  # Represent in byte
          else:
            volume_stats['volume_per_day']['volume'].append(0)

    if volume_stats['volume_per_day']['volume']:
        volume_stats['average_daily_volume'] = statistics.fmean(volume_stats['volume_per_day']['volume'])
    print("VOLUME:", volume_stats)
    return volume_stats
