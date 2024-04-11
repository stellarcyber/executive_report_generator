from helpers import gen_tenant_filter, gen_date_filter

def top_assets_stats(api, start_date, end_date, tenant=None, org_id=None):
    """
    Gets the top 5 risky assets on the end date
    """
  
    if not org_id:
        index = 'aella-assets-*'
    else:
        index = f"stellar-index-v1-assets-{org_id}-*"
  
    # Top 3 by score
    tenant_filter = gen_tenant_filter(tenant)
    date_filter = gen_date_filter(start_date, end_date)
  
    if tenant:
        query_filter = [tenant_filter, date_filter]
    else:
        query_filter = date_filter
  
    top_query = {
      "sort": [
        {"risk_score": {
          "order": "desc"}}
      ],
      "size": 5,
      "query": {
        "bool": {
          "must": [],
          "filter": query_filter,
          "should": [],
          "must_not": []
        }
      }
    }
  
    response = api.es_search(index, top_query)
    asset_stats = {'top_5_assets': []}
  
    for h in response['hits']['hits']:
        asset_details = {
          'name': h['_source']['name'],
          'risk_score': h['_source']['risk_score'],
          'macs': h['_source']['mac'],
          'ips': '<br>'.join(str(e) for e in h['_source']['ip']),
          'data_sources': '<br>'.join(str(e) for e in h['_source']['data_sources'])
        }
        if 'location' in h['_source']:
            asset_details['location'] = h['_source']['location'].replace(',', ', ')
        else:
            asset_details['location'] = ''
        asset_stats['top_5_assets'].append(asset_details)
  
    return asset_stats
  
