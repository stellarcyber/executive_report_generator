from datetime import datetime, timedelta
from os import path, listdir, mkdir
import sys
from glob import glob
import pickle
import streamlit as st
import webbrowser
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


def show_config_form():
    st.subheader("API Authentication", divider='gray')
    # if st.button("Load Saved Config", help="Loads the previously saved credentials"):
    #     load_config()

    # config_dir = __file__.replace("app.py", ".config")
    config_dir = "{}/{}".format(path.dirname(path.realpath(sys.argv[0])), ".config")
    if not path.exists(config_dir):
        mkdir(config_dir)

    saved_configs = listdir(config_dir)
    selected_config = st.radio("Saved Configurations", saved_configs)
    if selected_config:
        with open(path.join(config_dir, selected_config), "rb") as f:
            conf_dict = pickle.load(f)
        for var in ["host", "user", "api_key", "deployment_type"]:
            st.session_state[var] = conf_dict[var]


    host = st.text_input(
        "Instance URL",
        key="host",
        placeholder="https://salesdemo.stellarcyber.ai"
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
        if st.button("Save and Connect"):
            file_name = host.replace("https://",'')
            config_path = "{}/{}".format(config_dir, file_name)
            with open(config_path, "wb") as f:
            # with open(".saved", "wb") as f:
                pickle.dump({"host": host, "user": user, "api_key": api_key, "deployment_type": deployment_type}, f)

            st.session_state.api = StellarCyberAPI(
                url=st.session_state.host, 
                username=st.session_state.user, 
                api_key=st.session_state.api_key, 
                deployment=st.session_state.deployment_type
            )
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
        # if st.button("Open PDF"):
        #     webbrowser.open_new_tab("file://" + folder_file_map[selected_folder])



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

