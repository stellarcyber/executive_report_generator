import argparse
import jinja2
from numerize import numerize
from os import path, mkdir
import pickle
from shutil import copytree
import weasyprint
from stellar_api import StellarCyberAPI
from stellar_stats import StellarCyberStats
from stellar_plots import StellarCyberPlots
from utils import humansize


REPORT_TEMPLATE_DIR = __file__.replace("report.py", "report_template")
REPORT_DIR = __file__.replace("report.py", "reports_generated")


def get_report_html(template_dir, sc_stats, customer_name, start_date, end_date, template='report.html.template'):
    categories_sorted, data_sources_sorted, volume_sorted = sc_stats.combine_data_sources()

    j2_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), trim_blocks = True)
    report_template = j2_env.get_template(template)

    report_html = report_template.render(
        customer_name = customer_name,
        start_date = start_date,
        end_date = end_date,

        critical_incident_count = numerize.numerize(sc_stats.incident_stats['cumulative_critical_incident_count'],2),
        critical_alert_count = numerize.numerize(sc_stats.alert_stats['cumulative_critical_alert_count'],2),
        high_incident_count = numerize.numerize(sc_stats.incident_stats['high_incident_count']),

        average_daily_volume = humansize(sc_stats.volume_stats['average_daily_volume'],2),
        average_daily_assets = numerize.numerize(sc_stats.asset_stats['average_daily_assets'],2),

        distinct_data_sources = numerize.numerize(len(data_sources_sorted),0),
        distinct_alert_types = numerize.numerize(sc_stats.alert_stats['unique_alert_type_count'],2),

        unique_security_sensor_count=numerize.numerize(sc_stats.security_sensor_stats['unique_sensors']),
        unique_windows_sensor_count=numerize.numerize(sc_stats.windows_sensor_stats['unique_sensors']),
        unique_linux_sensor_count=numerize.numerize(sc_stats.linux_sensor_stats['unique_sensors']),

        top_alerts = sc_stats.alert_stats['top_3_alerts'],
        top_assets = sc_stats.top_assets_stats['top_5_assets'],
        top_incidents = sc_stats.incident_stats['top_3_incidents']
    )
    return report_html


def run_report(api, tenant, start, end, template='report.html.template'):
    report_dir = path.join(REPORT_DIR, f"{tenant}_{start.replace('-','')}-{end.replace('-','')}")
    template_dir = path.join(report_dir, "report_template")
    plots_dir = path.join(template_dir, "plots")
    html_filename = path.join(template_dir, "report.html")
    saved_stats_filename = path.join(report_dir, ".saved")
    pdf_filename = path.join(report_dir, f"{tenant} Executive Report.pdf")

    if not path.exists(REPORT_DIR):
        mkdir(REPORT_DIR)

    if not path.exists(report_dir):
        mkdir(report_dir)
        copytree(REPORT_TEMPLATE_DIR, template_dir)

    sc_stats = StellarCyberStats(api, tenant, start, end, "")

    df = sc_stats.incident_stats['incidents_df']
    df[df.Is_Critical == True].to_csv(path.join(report_dir, "critical_incidents.csv"))

    with open(saved_stats_filename, "wb") as f:
        pickle.dump(sc_stats, f)

    sc_plots = StellarCyberPlots(sc_stats)
    sc_plots.save_figures(plots_dir)

    report_html = get_report_html(REPORT_TEMPLATE_DIR, sc_stats, tenant, start, end, template=template)
    with open(html_filename, 'w') as fd:
        fd.write(report_html)
    
    weasyprint.HTML(html_filename).write_pdf(pdf_filename, options={'optimize_images': True})                    

    return sc_stats, sc_plots


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ExecutiveReportGenerator',
        description='Generate PDF reports from Stellar Cyber',
        epilog='Text at the bottom of help'
    )
    parser.add_argument('tenant')
    parser.add_argument('start_date')
    parser.add_argument('end_date')

    args = parser.parse_args()
    print(args)

    if path.exists(".saved"):
        with open(".saved", "rb") as f:
            conf_dict = pickle.load(f)
            host = conf_dict['host']
            user = conf_dict['user']
            api_key = conf_dict['api_key']
            deployment_type = conf_dict['deployment_type']
    
    api = StellarCyberAPI(
        url=host, 
        username=user, 
        api_key=api_key, 
        deployment=deployment_type
    )

    run_report(api, args.tenant, args.start_date, args.end_date)