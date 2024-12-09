from datetime import datetime, timedelta
from os import path, listdir, mkdir
import sys
from glob import glob
import pickle
import streamlit as st
from stellar_api import StellarCyberAPI
from stellar_plots import StellarCyberPlots
from report_pages import *
from report import REPORT_DIR, REPORT_TEMPLATE_DIR, run_report


def load_config():
    if path.exists(".saved"):
        with open(".saved", "rb") as f:
            conf_dict = pickle.load(f)
        for var in ["host", "user", "api_key", "deployment_type"]:
            st.session_state[var] = conf_dict[var]


def load_saved_data(saved_stats_file):
    with open(saved_stats_file, "rb") as f:
        sc_stats = pickle.load(f)
    st.session_state.sc_stats = sc_stats
    st.session_state.sc_plots = StellarCyberPlots(sc_stats)


def show_status_caption():
    st.caption(
            "No Data Loaded" if 'sc_stats' not in st.session_state 
            else f'Report prepared for {st.session_state.sc_stats.tenant} for time period: {st.session_state.sc_stats.start} to {st.session_state.sc_stats.end}'
        )


def save_config():
    stss = st.session_state
    file_name = stss.host.replace("https://", '')
    config_path = "{}/{}".format(get_config_directory(), file_name)
    with open(config_path, "wb") as f:
        # with open(".saved", "wb") as f:
        pickle.dump({"host": stss.host, "user": stss.user, "api_key": stss.api_key, "deployment_type": stss.deployment_type}, f)

    st.session_state.api = StellarCyberAPI(
        url=stss.host,
        username=stss.user,
        api_key=stss.api_key,
        deployment=stss.deployment_type
    )
    stss['last_config'] = file_name


def load_config():
    selected_config = st.session_state.config_list
    if selected_config:
        st.session_state['last_config'] = selected_config
        with open(path.join(get_config_directory(), selected_config), "rb") as f:
            conf_dict = pickle.load(f)
        for var in ["host", "user", "api_key", "deployment_type"]:
            st.session_state[var] = conf_dict[var]

def get_configs():
    saved_configs = []
    config_dir = get_config_directory()
    if not path.exists(config_dir):
        mkdir(config_dir)
    saved_configs = listdir(config_dir)
    return saved_configs

def get_config_directory():
    config_dir = "{}/{}".format(path.dirname(path.realpath(sys.argv[0])), ".config")
    return config_dir

def get_list_index(list_to_search :list, value_to_find=''):
    index_value = None
    try:
        if value_to_find:
            index_value = list_to_search.index(value_to_find)
    except Exception as e:
        pass
    return index_value


def show_config_form():

    st.subheader("API Authentication", divider='gray')

    config_list = get_configs()
    last_config = st.session_state.get('last_config')
    list_index = get_list_index(config_list, last_config)

    st.selectbox("Saved Configurations", config_list, on_change=load_config, key="config_list", index=list_index, placeholder="Choose a config to load")

    host = st.text_input(
        "Instance URL",
        key="host",
        placeholder="https://salesdemo.stellarcyber.ai",
    )
    user = st.text_input(
        "Stellar Cyber User",
        key="user",
        autocomplete="on",
        placeholder="example.user@stellarcyber.ai"
    )
    api_key = st.text_input(
        "Stellar Cyber API Key",
        key="api_key",
        type="password",
        autocomplete="password",
        placeholder="API Key",
        disabled=False,
        label_visibility="visible",
    )
    deployment_type = st.selectbox(
        "Deployment Type",
        ["SaaS", "On-Prem"],
        key="deployment_type"
    )
    col1, col2 = st.columns(2)
    with col1:
        st.button("Save and Connect", on_click=save_config)
    with col2:
        st.write("Not Connected" if 'api' not in st.session_state else ":white_check_mark: Connected")


def show_query_form():

    timeframe = st.date_input(
        "Time Range",
        value=[
            datetime.today() - timedelta(days=7),
            datetime.today(),
        ],
        key="timeframe",
    )
    try:
        tenant_options = st.session_state.api.get_tenants()
        tenants = st.multiselect("Tenant(s)", ["All Tenants"] + tenant_options)
    except:
        st.error("Failed to retrieve tenants")
        tenants = ["All Tenants"]
    
    template_files = [f for f in listdir(REPORT_TEMPLATE_DIR) if f.endswith(".html.template")]
    selected_template = st.selectbox("HTML Template", template_files)

    if st.button(f"Run Report{'s' if len(tenants) > 1 else ''}"):
        for tenant in tenants:
            with st.spinner(f"Retrieving Data for {tenant}"):
                sc_stats, sc_plots = run_report(st.session_state.api, tenant, str(timeframe[0]), str(timeframe[1]), template=selected_template)
                st.session_state.sc_stats = sc_stats
                st.session_state.sc_plots = sc_plots


def show_sidebar():
    
    st.subheader("Run New Report", divider="green")
    with st.expander("Not Configured" if 'api' not in st.session_state else ":white_check_mark: Configured"):
        show_config_form()
    if 'api' in st.session_state:
        show_query_form()
    
    st.subheader("Open Existing Report", divider="green")

    pdf_files = list(glob(REPORT_DIR + "/*/*.pdf", recursive=True))
    folder_file_map = {f.split("/")[-2]: f for f in pdf_files}

    selected_folder = st.selectbox(f"{len(pdf_files)} Reports Generated", folder_file_map.keys())
    if selected_folder:
        load_saved_data(path.join(REPORT_DIR, selected_folder, ".saved"))

        with open(folder_file_map[selected_folder], "rb") as file:
            btn = st.download_button(
                    label="Download PDF",
                    data=file,
                    file_name=f"{selected_folder}.pdf",
                    mime="application/pdf"
                  )


def run_app():

    st.set_page_config(
        page_title="Stellar Cyber Executive Reporting App", layout="wide", initial_sidebar_state="expanded"
    )

    with st.sidebar:
        show_sidebar()

    st.header('Stellar Cyber Executive Report', divider="blue")
    show_status_caption()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Deployment Summary", "Cases", "Alerts", "Assets", "Visibility"]
    )

    with tab1:
        show_deployment_summary()
    with tab2:
        show_incidents_stats()
    with tab3:
        show_alerts()
    with tab4:
        show_assets()
    with tab5:
        show_visibility()


if __name__ == '__main__':
    run_app()

