from datetime import datetime
import numpy as np
import pandas as pd
from stats.volume_stats import volume_stats
from stats.asset_stats import asset_stats
from stats.connector_stats import connector_stats
from stats.log_source_stats import log_source_stats
from stats.linux_sensor_stats import linux_sensor_stats
from stats.windows_sensor_stats import windows_sensor_stats
from stats.network_sensor_stats import network_sensor_stats
from stats.security_sensor_stats import security_sensor_stats
from stats.alert_stats import alert_stats
from stats.alert_stage_stats import alert_stage_stats
from stats.alert_tactic_stats import alert_tactic_stats
from stats.alert_geo_stats import alert_geo_stats
from stats.top_assets_stats import top_assets_stats
from stats.incident_stats import get_incident_stats
import streamlit as st
import traceback


class StellarCyberStats():

    def __init__(self, api, tenant, start_date, end_date, org_id):
        self.api = api
        self.daily_date_scale = list(pd.Series(pd.date_range(start_date, end_date, freq='D').strftime('%Y-%m-%d')))
        self.start = start_date
        self.end = end_date


        tenant = None if tenant == "All Tenants" else tenant  # Use None for 'All Tenants'
        self.tenant = tenant
        
        self.query_timestamp = datetime.now()
        try:
            self.query_stats(tenant, start_date, end_date, org_id)
        except Exception as e:
            st.error("Unable to retrieve all statistics for this deployment.")
            print(e)
            print(traceback.format_exc())

    def query_stats(self, tenant, start_date, end_date, org_id=None):
        self.volume_stats = volume_stats(self.api, start_date, end_date, self.daily_date_scale, tenant, org_id)
        self.asset_stats = asset_stats(self.api, start_date, end_date, self.daily_date_scale, tenant, org_id)
        self.connector_stats = connector_stats(self.api, start_date, end_date, tenant, org_id)
        self.log_source_stats = log_source_stats(self.api, start_date, end_date, tenant, org_id)
        self.linux_sensor_stats = linux_sensor_stats(self.api, start_date, end_date, tenant, org_id)
        self.windows_sensor_stats = windows_sensor_stats(self.api, start_date, end_date, tenant, org_id)
        self.network_sensor_stats = network_sensor_stats(self.api, start_date, end_date, tenant, org_id)
        self.security_sensor_stats = security_sensor_stats(self.api, start_date, end_date, tenant, org_id)
        self.alert_stats = alert_stats(self.api, start_date, end_date, tenant, org_id)
        self.alert_stage_stats = alert_stage_stats(self.api, start_date, end_date, tenant, org_id)
        self.alert_tactic_stats = alert_tactic_stats(self.api, start_date, end_date, tenant, org_id)
        self.alert_geo_stats = alert_geo_stats(self.api, start_date, end_date, tenant, org_id)
        self.top_assets_stats = top_assets_stats(self.api, start_date, end_date, tenant, org_id)
        self.incident_stats = get_incident_stats(self.api, self.daily_date_scale, tenant)

    def list_stats(self):
        return {
            "Volume Stats": self.volume_stats,
            "Asset Stats": self.asset_stats,
            "Connector Stats": self.connector_stats,
            "Log Source Stats": self.log_source_stats,
            "Linux Sensor Stats": self.linux_sensor_stats,
            "Windows Sensor Stats": self.windows_sensor_stats,
            "Network Sensor Stats": self.network_sensor_stats,
            "Security Sensor Stats": self.security_sensor_stats,
            "Alert Stats": self.alert_stats,
            "Alert Stage Stats": self.alert_stage_stats,
            "Alert Tactic Stats": self.alert_tactic_stats,
            "Alert Geo Stats": self.alert_geo_stats,
            "Top Assets Stats": self.top_assets_stats,
            "Incident Stats": self.incident_stats
        }
    
    def combine_data_sources(self):
        """ Combines all unique data sources into sorted lists by volume with categories """

        # Merge all data sources into a single dict
        categories = ['Connector'] * len(self.connector_stats['cumulative_volume_by_connector']['connector_name']) + \
        ['Log Source'] * len(self.log_source_stats['cumulative_volume_by_log_source']['log_source']) + \
        ['Sensor', 'Sensor', 'Sensor'] + \
        ['Sensor'] * len(self.security_sensor_stats['cumulative_volume_by_feature']['feature'])

        data_sources = self.connector_stats['cumulative_volume_by_connector']['connector_name'] + \
        self.log_source_stats['cumulative_volume_by_log_source']['log_source'] + \
        ['Linux Sensor'] + ['Windows Sensor'] + ['Network Sensor - Traffic'] + \
        self.security_sensor_stats['cumulative_volume_by_feature']['feature']

        volume = self.connector_stats['cumulative_volume_by_connector']['volume'] + \
        self.log_source_stats['cumulative_volume_by_log_source']['volume'] + \
        [self.linux_sensor_stats['cumulative_volume']] + [self.windows_sensor_stats['cumulative_volume']] + [self.network_sensor_stats['cumulative_volume']] + \
        self.security_sensor_stats['cumulative_volume_by_feature']['volume']

        categories = np.array(categories)
        data_sources = np.array(data_sources)
        volume = np.array(volume) / 1000 / 1000 / 1000 # Get in GB
        sort_inds = volume.argsort()[::-1]
        categories_sorted = categories[sort_inds]
        data_sources_sorted = data_sources[sort_inds]
        volume_sorted = volume[sort_inds]

        return categories_sorted, data_sources_sorted, volume_sorted

