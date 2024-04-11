import acgs


def gen_unique_count_query(query_filter):    
    # Additional query for geting unique sensor count over time period
    unique_count_query = {
      "aggs": {
        "unique_sensors": {
          "cardinality": {
            "field": "engid.keyword"
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
    return unique_count_query

def process_sensor_stats(response, unique_count_response):
    sensor_stats = {'volume_per_day': {'date': [], 'volume': []},
                    'cumulative_volume': 0, 'unique_sensors': 0}
    for b in response['aggregations']['date']['buckets']:
        sensor_stats['volume_per_day']['date'].append(b['key_as_string'][0:10])
        sensor_stats['volume_per_day']['volume'].append(b['out_bytes_delta_total']['value'])
    sensor_stats['cumulative_volume'] = sum(sensor_stats['volume_per_day']['volume'])


    sensor_stats['unique_sensors'] = unique_count_response['aggregations']['unique_sensors']['value']
    return sensor_stats

def gen_tenant_filter(tenant=None):
    tenant_name = tenant or "All Tenants"
    tenant_filter = {
      "bool": {
        "should": [
          { 
            "match_phrase": {
              "tenant_name": tenant_name
            }
          }
        ],
        "minimum_should_match": 1
      }
    }
    return tenant_filter

def gen_date_filter(start_date, end_date):    
    date_filter = {
      "range": {
        "timestamp": {
          "gte": start_date,
          "lte": end_date,
          "format": "strict_date_optional_time"
        }
      }
    }
    return date_filter


def gen_msgtype_filter(msgtype):
    msgtype_filter = {
      "bool": {
        "should": [
          {
            "match": {
              "msgtype": msgtype 
            }
          }
        ],
        "minimum_should_match": 1
      }
    }
    return msgtype_filter

def gen_msgtypes_filter(msgtypes):
    msgtypes_filter = {
      "bool": {
         "should": [],
         "minimum_should_match": 1
      }
    }
    for msgtype in msgtypes:
        msgtypes_filter["bool"]["should"].append(gen_msgtype_filter(msgtype))
    return msgtypes_filter

def gen_sensor_type_filter(sensor_type):

    sensor_type_filter = {
      "bool": {
        "should": [
          {
            "bool": {
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "feature": "ds"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                },
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "mode": sensor_type
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ]
            }
          },
          {
            "bool": {
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "feature": "modular"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                },
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "mode": sensor_type 
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ]
            }
          }
        ],
        "minimum_should_match": 1
      }
    }
    return sensor_type_filter

def gen_timeseries_query(start_date, end_date, query_filter, agg_type=None):
    if agg_type == "security_sensor":
        aggs = {
            "feature": {
              "terms": {
                "field": "msgtype",
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
    elif agg_type == "xdr_killchain_stage":
        aggs = {
            "stage": {
              "terms": {
                "field": "xdr_event.xdr_killchain_stage.keyword",
                "order": {
                  "_count": "desc"
                },
                "size": 1000
              }
            }
        }
    elif agg_type == "alert_tactic":
        aggs = {
            "stage": {
              "terms": {
                "field": "xdr_event.xdr_killchain_stage.keyword",
                "order": {
                  "_count": "desc"
                },
                "size": 1000
              },
              "aggs": {
                "tactic": {
                  "terms": {
                    "field": "xdr_event.tactic.name.keyword"
                  }
                }
              }
            }
        }
    else:
        aggs = {
            "out_bytes_delta_total": {
              "sum": {
                "field": "out_bytes_delta"
              }
            }
          }

    timeseries_query = {
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
          "aggs": aggs
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
    return timeseries_query

def gen_base_count_query(start_date, end_date, query_filter):
    base_count_query = {
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

    return base_count_query

def gen_score_filter(field, op, score):

    score_filter = {
      "bool": {
        "should": [
          {
            "range": {
              field : {
                op : score
              }
            }
          }
        ],
        "minimum_should_match": 1
      }
    }
    return score_filter

def gen_top_query(field, query_filter):
    top_query = {
      "sort": [
        {field: {
          "order": "desc"}}
      ],
      "size": 3,
      "query": {
        "bool": {
          "must": [],
          "filter": query_filter,
          "should": [],
          "must_not": []
        }
      }
    }
    return top_query

