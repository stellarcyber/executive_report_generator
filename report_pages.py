import pandas as pd
import streamlit as st
from numerize import numerize
from utils import humansize


def stats_page(fn):
    def wrapper():
        if 'sc_stats' not in st.session_state:
            st.info("No Data Loaded")
        elif 'sc_plots' not in st.session_state:
            st.warning("No Charts Available")
        else:
            fn()
    return wrapper


@stats_page
def show_deployment_summary():
    sc_stats = st.session_state.sc_stats
    categories_sorted, data_sources_sorted, volume_sorted = sc_stats.combine_data_sources()

    st.caption("The following summary captures high level statistics for the deployment over the specified time period.")

    st.divider()
    st.subheader("Detections")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(":orange[Critical Cases Detected]", numerize.numerize(sc_stats.incident_stats['cumulative_critical_incident_count'],2))
    with col2:
        st.metric(":orange[Critical Alerts Detected]", numerize.numerize(sc_stats.alert_stats['cumulative_critical_alert_count'],2))
    with col3:
        st.metric(":orange[Distinct Alert Types Triggered]", numerize.numerize(sc_stats.alert_stats['unique_alert_type_count'],2))
    st.divider()
    st.subheader("Visibility")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(":orange[Average Daily Data Volume]", humansize(sc_stats.volume_stats['average_daily_volume'],2))
    with col2:
        st.metric(":orange[Average Daily Discovered Assets]", numerize.numerize(sc_stats.asset_stats['average_daily_assets'],2))
    with col3:
        st.metric(":orange[Distinct Data Sources]", numerize.numerize(len(data_sources_sorted),0))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(":orange[Security Sensors Deployed]", numerize.numerize(sc_stats.security_sensor_stats['unique_sensors']))
    with col2:
        st.metric(":orange[Windows Sensors Deployed]", numerize.numerize(sc_stats.windows_sensor_stats['unique_sensors']))
    with col3:
        st.metric(":orange[Linux Sensors Deployed]", numerize.numerize(sc_stats.linux_sensor_stats['unique_sensors']))
        

@stats_page
def show_incidents_stats():
    st.caption("A Case is a single attack story, correlating multiple likely related alerts and observables together from every data source. Stellar Cyber uses Machine Learning to perform correlation and security analysts can further edit or build custom Cases. A Critical Case represents very high risk connected behaviors and is defined as a risk score >= 75 in Stellar Cyber.")
    incident_stats = st.session_state.sc_stats.incident_stats

    st.subheader("Critical Cases Over Time")
    st.line_chart(pd.DataFrame(incident_stats["critical_count_per_day"]), x="date", y="count")
    
    st.subheader("Top 3 Cases by Risk Score")
    top_incidents = incident_stats['top_3_incidents']
    top_incidents = pd.DataFrame(top_incidents).rename(columns={'created_at': "Start", "name": "Title", "incident_score": "Score"}) #.iloc[:,[1,0,2]]
    st.markdown(top_incidents.style.hide(axis="index").to_html(), unsafe_allow_html=True)


@stats_page
def show_alerts():
    st.caption("""Alerts detected in Stellar Cyber are derived from a combination of raw telemetry and Third
                    Party Native Alerts. Alerts are generated via Machine Learning and rules. All Alerts are
                    mapped to the XDR Killchain which is a superset of MITRE ATT&CK. A Critical Alert
                    represents a very high risk individual behavior and is defined as a risk score >= 75 in Stellar
                    Cyber. A High Fidelity Alert represents high confidence that certain behavior happened, is
                    defined as fidelity >= 75 in Stellar Cyber, and is an input to the overall risk score.""")

    st.subheader("Alerts Over Time")
    sc_stats = st.session_state.sc_stats
    alert_stage_stats = sc_stats.alert_stage_stats
    alert_tactic_stats = sc_stats.alert_tactic_stats
    alert_geo_stats = sc_stats.alert_geo_stats
    top_alerts = sc_stats.alert_stats['top_3_alerts']


    st.write(st.session_state.sc_plots.get_figure("alert_line_graph"))
    st.write(st.session_state.sc_plots.get_figure("stage_heatmap"))
    st.write(st.session_state.sc_plots.get_figure("tactic_heatmap"))

    st.divider()
    st.subheader("High Fidelity Alerts Source Map")
    st.caption("""This map shows the geocoded source (typically from an IP address) involved with all High
                    Fidelity Alerts. Not all Alerts will have geocodable elements, so this map is not exhaustive of
                    all Alerts. 
               """)
    st.write(st.session_state.sc_plots.get_figure("alert_map"))

    st.subheader("Top 3 Alerts by Risk Score")
    st.write(pd.DataFrame(top_alerts))


@stats_page
def show_assets():
    top_assets = st.session_state.sc_stats.top_assets_stats['top_5_assets']

    st.header("Assets")
    st.caption("""Assets are continuously discovered and resolved across every data source in Stellar Cyber.
                Vulnerabilities, alerts, and other activity are used together to produce a risk score for
                providing context in investigations. """)
    
    st.subheader("Top 5 Assets by Risk Score")
    st.write(pd.DataFrame(top_assets))


@stats_page
def show_visibility():
    sc_stats = st.session_state.sc_stats
    volume_stats = sc_stats.volume_stats
    asset_stats = sc_stats.asset_stats

    st.header("Visibility")
    st.caption("""Stellar Cyber collects data from its own Sensors and Third Party Tools. The following charts
                use the following categories - Sensors are defined as data generated from Stellar Cyber
                Sensors, NOT including Third Party Log Sources. Connectors are defined as Third Party Tools
                collected via API Connectors. Log Sources are defined as Third Party Tools collected via
                streaming logs.""")
    st.subheader("Visibility Over Time")
    st.write(st.session_state.sc_plots.get_figure("volume_assets_line_graph"))
    st.write(st.session_state.sc_plots.get_figure("volume_category_trends"))

    st.subheader("Top 10 Data Sources by Cumulative Volume")
    st.write(st.session_state.sc_plots.get_figure("top_data_sources_volume"))

    st.subheader("Top 20 Data Sources by Cumulative Volume")
    st.write(st.session_state.sc_plots.get_figure("all_data_sources_volume_sankey"))

