import datetime
import pandas as pd

COLUMNS = ['_id', 'created_at', 'name', 'tags', 'severity', 'score', 'assignee_name']


def get_incidents(api, start, end):
    response = api.rest_search(
        'v1/cases',
        {
            'FROM~created_at': int(start.timestamp() * 1000),
            'TO~created_at': int(end.timestamp() * 1000),
            'FROM~score': 50,
        }
    )
    df = pd.DataFrame(
        columns=COLUMNS,
        data=[[i[c] for c in COLUMNS] for i in response['data']['cases']]
    )
    df['Date'] = df.created_at.astype('datetime64[ms]').dt.date
    df['Is_Critical'] = df.score >= 75
    return df


def get_case_summaries(api, incidents_df):
    case_summaries = []
    for case_id in incidents_df._id.values:
        response = api.rest_search(f'v1/cases/{case_id}/summary', {'formatted': True})
        case_summaries.append(response.get('data', ''))
    incidents_df['summary'] = case_summaries
    return incidents_df


def get_incident_stats(api, daily_date_scale, tenant):
    """
    Critical incidents per day, total critical incidents, top 3 incidents by risk score
    """

    try:

        incident_stats = {
            'critical_count_per_day': {'date': [], 'count': []},
            'high_count_per_day': {'date': [], 'count': []},
            'top_3_incidents': [],
            'cumulative_critical_incident_count': 0
        }

        if tenant:
            cust_id = api.tenant_info[tenant].get("cust_id")

        daily_dfs = []
        for d in daily_date_scale:
            query_date_start = datetime.datetime.strptime(d, "%Y-%m-%d")
            query_date_end = query_date_start + datetime.timedelta(days=1, milliseconds=-1)

            query_params = {
                'FROM~created_at': int(query_date_start.timestamp() * 1000),
                'TO~created_at': int(query_date_end.timestamp() * 1000),
                'limit': 1,
                'FROM~score': 75
            }
            if tenant:
                query_params['cust_id'] = cust_id

            response = api.rest_search('v1/cases', query_params)

            incident_stats['critical_count_per_day']['date'].append(d)
            incident_stats['critical_count_per_day']['count'].append(response['data']['total'])

            query_params = {
                'FROM~created_at': int(query_date_start.timestamp() * 1000),
                'TO~created_at': int(query_date_end.timestamp() * 1000),
                'limit': 1,
                'FROM~score': 50,
                'TO~score': 74.99999
            }
            if tenant:
                query_params['cust_id'] = cust_id

            response = api.rest_search('v1/cases', query_params)

            incident_stats['high_count_per_day']['date'].append(d)
            incident_stats['high_count_per_day']['count'].append(response['data']['total'])

            daily_dfs.append(get_incidents(api, query_date_start, query_date_end))

        # Top 3 by risk
        query_date_start = datetime.datetime.strptime(daily_date_scale[0], "%Y-%m-%d")
        query_date_end = datetime.datetime.strptime(daily_date_scale[-1], "%Y-%m-%d")
        query_date_end = query_date_end + datetime.timedelta(days=1, milliseconds=-1)

        query_params = {
            'FROM~created_at': int(query_date_start.timestamp() * 1000),
            'TO~created_at': int(query_date_end.timestamp() * 1000),
            'limit': 3,
            'sort': 'score',
            'order': 'desc'
        }

        if tenant:
            query_params['cust_id'] = cust_id

        top_response = api.rest_search('v1/cases', query_params)
        # print(json.dumps(top_response, indent=3))
        for i in top_response['data']['cases']:
            incident_stats['top_3_incidents'].append({
                'created_at': datetime.datetime.fromtimestamp(i['created_at'] // 1000).strftime('%c'),
                'name': i['name'],
                # 'description': i['metadata']['description_auto'].replace('\n', '<br>'),
                'incident_score': i['score']
            })

        incident_stats['cumulative_critical_incident_count'] = sum(incident_stats['critical_count_per_day']['count'])
        # print(json.dumps(incident_stats, indent=3))

        df = pd.concat(daily_dfs)
        # df = get_case_summaries(api, df)
        incident_stats['incidents_df'] = df
        incident_stats['high_incident_count'] = sum(incident_stats['high_count_per_day']['count'])
        # top3 = df.sort_values(by='incident_score', ascending=False).iloc[:3][['created_at', 'name', 'summary', 'incident_score']]

    except Exception as e:
        print("exception {}".format(e))
        # exit(0)

    return incident_stats

