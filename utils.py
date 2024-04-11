import jinja2
from numerize import numerize


def humansize(nbytes, decimals):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1000 and i < len(suffixes)-1:
        nbytes /= 1000.
        i += 1
    f = ('%.{}f'.format(decimals) % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def get_report_html(template_dir, sc_stats, customer_name, start_date, end_date):
    categories_sorted, data_sources_sorted, volume_sorted = sc_stats.combine_data_sources()

    j2_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), trim_blocks = True)
    report_template = j2_env.get_template("report.html.template")

    report_html = report_template.render(
        customer_name = customer_name,
        start_date = start_date,
        end_date = end_date,

        critical_incident_count = numerize.numerize(sc_stats.incident_stats['cumulative_critical_incident_count'],2),
        critical_alert_count = numerize.numerize(sc_stats.alert_stats['cumulative_critical_alert_count'],2),

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
