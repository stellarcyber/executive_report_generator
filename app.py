from datetime import datetime, timedelta
from os import mkdir, path
from glob import glob
import pickle
from shutil import copytree
import streamlit as st
import weasyprint
import webbrowser
from stellar_api import StellarCyberAPI
from stellar_stats import StellarCyberStats
from stellar_plots import StellarCyberPlots
from utils import get_report_html
from report_pages import *


REPORT_TEMPLATE_DIR = __file__.replace("app.py", "report_template")
REPORT_DIR = __file__.replace("app.py", "reports_generated")



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


def run_report(tenant, start, end):
    report_dir = path.join(REPORT_DIR, f"{tenant}_{start.replace('-','')}-{end.replace('-','')}")
    template_dir = path.join(report_dir, "report_template")
    plots_dir = path.join(template_dir, "plots")
    html_filename = path.join(template_dir, "report.html")
    saved_stats_filename = path.join(report_dir, ".saved")
    pdf_filename = path.join(report_dir, f"{tenant} Executive Report.pdf")

    if not path.exists(REPORT_DIR):
        mkdir(REPORT_DIR)

    if path.exists(report_dir):
        st.error(f"Report already exists: {tenant}_{start.replace('-','')}-{end.replace('-','')}")
        return

    mkdir(report_dir)
    copytree(REPORT_TEMPLATE_DIR, template_dir)

    with st.spinner(f"Retrieving Data for {tenant}"):
        sc_stats = StellarCyberStats(st.session_state.api, tenant, start, end, "")

    with open(saved_stats_filename, "wb") as f:
        pickle.dump(sc_stats, f)

    sc_plots = StellarCyberPlots(sc_stats)
    sc_plots.save_figures(plots_dir)

    report_html = get_report_html(REPORT_TEMPLATE_DIR, sc_stats, tenant, start, end)
    with open(html_filename, 'w') as fd:
        fd.write(report_html)
    
    weasyprint.HTML(html_filename).write_pdf(pdf_filename)                    

    st.session_state.sc_stats = sc_stats
    st.session_state.sc_plots = sc_plots


def show_config_form():
    st.subheader("API Authentication")
    if st.button("Load Saved Config", help="Loads the previously saved credentials"):
        load_config()
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
            with open(".saved", "wb") as f:
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

    if st.button(f"Run Report{'s' if len(tenants) > 1 else ''}"):
        for tenant in tenants:
            run_report(tenant, str(timeframe[0]), str(timeframe[1]))


def show_sidebar():
    st.header("Stellar Cyber Report Generator", divider="orange")
    
    st.subheader("Run New Report", divider="gray")
    with st.expander("Not Configured" if 'api' not in st.session_state else ":white_check_mark: Configured"):
        show_config_form()
    if 'api' in st.session_state:
        show_query_form()
    
    st.subheader("Open Existing Report", divider="gray")

    pdf_files = list(glob(REPORT_DIR + "/*/*.pdf", recursive=True))
    folder_file_map = {f.split("/")[-2]: f for f in pdf_files}

    selected_folder = st.selectbox(f"{len(pdf_files)} Reports Generated", folder_file_map.keys())
    if selected_folder:
        load_saved_data(path.join(REPORT_DIR, selected_folder, ".saved"))

        if st.button("Open PDF"):
            webbrowser.open_new_tab("file://" + folder_file_map[selected_folder])



def run_app():
    st.set_page_config(
        page_title="Stellar Cyber Executive Reporting App", layout="wide", initial_sidebar_state="expanded"
    )
    with st.sidebar:
        show_sidebar()

    st.header('Stellar Cyber Executive Report', divider="blue")
    show_status_caption()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Deployment Summary", "Incidents", "Alerts", "Assets", "Visibility"]
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

