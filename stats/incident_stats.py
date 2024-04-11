import datetime


def incident_stats(api, start_date, end_date, daily_date_scale, tenant=None, org_id=None):
    """
    Critical incidents per day, total critical incidents, top 3 incidents by risk score
    """
  
    incident_stats = {'critical_count_per_day': {'date': [], 'count': []},
          'top_3_incidents': [], 'cumulative_critical_incident_count': 0}

    # Get tenant ID from tenant name
    if tenant:
        tenant_id = api.tenant_info[tenant].get("cust_id")


    # Since no API aggregations are possible, iterate through each date to get the critical count
    for d in daily_date_scale:
        query_date_start = datetime.datetime.strptime(d, "%Y-%m-%d")
        query_date_end = query_date_start + datetime.timedelta(days=1, milliseconds=-1)

        query_params = {
          'FROM~created_at': int(query_date_start.timestamp()*1000),
          'TO~created_at': int(query_date_end.timestamp()*1000),
          'limit': 1,
          'FROM~incident_score': 75
        }

        if tenant:
            query_params['cust_id'] = tenant_id

        day_count_response = api.rest_search('v1/incidents', query_params)
        incident_stats['critical_count_per_day']['date'].append(d)
        incident_stats['critical_count_per_day']['count'].append(day_count_response['data']['total'])

    # Top 3 by risk
    query_date_start = datetime.datetime.strptime(daily_date_scale[0], "%Y-%m-%d")
    query_date_end = datetime.datetime.strptime(daily_date_scale[-1], "%Y-%m-%d")
    query_date_end = query_date_end + datetime.timedelta(days=1, milliseconds=-1)

    query_params = {
        'FROM~created_at': int(query_date_start.timestamp()*1000),
        'TO~created_at': int(query_date_end.timestamp()*1000),
        'limit': 3,
        'sort': 'incident_score',
        'order': 'desc'
    }

    if tenant:
        query_params['cust_id'] = tenant_id

    top_response = api.rest_search('v1/incidents', query_params)
    for i in top_response['data']['incidents']:
        incident_stats['top_3_incidents'].append({
            'created_at': datetime.datetime.fromtimestamp(i['created_at']//1000).strftime('%c'),
            'name': i['name'],
            # 'description': i['metadata']['description_auto'].replace('\n', '<br>'),
            'incident_score': i['incident_score']
        })

    incident_stats['cumulative_critical_incident_count'] = sum(incident_stats['critical_count_per_day']['count'])
    return incident_stats
