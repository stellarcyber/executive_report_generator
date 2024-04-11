from collections import OrderedDict
import statistics
from helpers import gen_tenant_filter, gen_date_filter
import acgs

def asset_stats(api, start_date, end_date, daily_date_scale, tenant=None, org_id=None):
    """
    Stats: average daily assets, asset count timeseries
    Gets stats bucketed by day in UTC.
    """
    asset_stats = {'assets_per_day': {'date': [], 'count': []},
                    'average_daily_assets': 0}

    if org_id:
        # init data structure
        asset_data = OrderedDict()
        for key in daily_date_scale:
            asset_data[key] = 0

        asset_usage = acgs.get_asset_usage(org_id, start_date, end_date)
        if tenant != None and len(tenant) > 0:
            for _date, vol in asset_usage["by_tenant"][tenant].items():
                asset_data[_date] = int(vol)
        # all tenants
        else:
            for _date, entry in asset_usage["by_date"].items():
                asset_data[_date] = int(sum(entry.values()))
        asset_stats['assets_per_day']['date'] = asset_data.keys()
        asset_stats['assets_per_day']['count'] = list(asset_data.values())
    else:
        index = 'aella-assetlicense-1'
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
                "asset_count": {
                  "sum": {
                    "field": "asset_usage"
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
        for b in response['aggregations']['date']['buckets']:
          asset_stats['assets_per_day']['date'].append(b['key_as_string'][0:10])
          asset_stats['assets_per_day']['count'].append(b['asset_count']['value'])

    asset_stats['average_daily_assets'] = statistics.fmean(asset_stats['assets_per_day']['count'])
    print("ASSET:", asset_stats)
    return asset_stats
