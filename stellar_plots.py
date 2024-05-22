import os
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px


class StellarCyberPlots():

    def __init__(self, sc_stats):
        self.sc_stats = sc_stats
        self.figures = {p:self.get_figure(p) for p in [
            "incident_line_graph",
            "alert_line_graph",
            "stage_heatmap",
            "tactic_heatmap",
            "alert_map",
            "volume_assets_line_graph",
            "volume_category_trends",
            "top_data_sources_volume",
            "all_data_sources_volume_sankey",
            "volume_pie_chart"
        ]}
    
    def save_figures(self, dst_folder):
        os.makedirs(dst_folder, exist_ok=True)
        for figure_name, figure in self.figures.items():
          figure.write_image(f"{os.path.join(dst_folder, figure_name)}.svg")

    def get_figure(self, fig_name):
      sc_stats = self.sc_stats
      daily_date_scale = sc_stats.daily_date_scale

      if fig_name == "incident_line_graph":
          incident_stats = self.sc_stats.incident_stats
          fig = go.Figure()
          fig.add_trace(go.Scatter(x=incident_stats['critical_count_per_day']['date'], y=incident_stats['critical_count_per_day']['count'], name='Critical Incidents',
                                  line=dict(color="rgb(217,72,1)", width=2)))

          fig.update_layout(
              width=630,
              height=300,
              margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=0, #top margin
              ),
              font={
                    "family": "Lato",
                    "size": 12,
                    "color": "#707070",
                },
              xaxis=dict(showgrid=False, title_text='Date', title_font = {"size": 16}),
              yaxis=dict(showgrid=False, title_text='Count', title_font = {"size": 16}, rangemode='tozero'),
              plot_bgcolor='rgba(0,0,0,0)'
          )

      elif fig_name == "alert_line_graph":
          alert_stats = self.sc_stats.alert_stats

          days = daily_date_scale
          alerts = alert_stats['count_per_day']['count']
          critical_alerts = alert_stats['critical_count_per_day']['count']
          high_fidelity_alerts = alert_stats['high_fidelity_count_per_day']['count']

          fig = go.Figure()
          # Removing alert lines to reduce noise
          #fig.add_trace(go.Scatter(x=days, y=alerts, name='Alerts',
          #                        line=dict(color='black', width=2)))
          fig.add_trace(go.Scatter(x=days, y=critical_alerts, name='Critical Alerts',
                                  line=dict(color="rgb(217,72,1)", width=2)))
          fig.add_trace(go.Scatter(x=days, y=high_fidelity_alerts, name='High Fidelity Alerts',
                                  line=dict(color="#EAAA00", width=2)))

          fig.update_layout(
              width=630,
              height=280,
              margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=0, #top margin
              ),
              font={
                    "family": "Lato",
                    "size": 12,
                    "color": "#707070",
                },
              xaxis=dict(showgrid=False, title_text='Date', title_font = {"size": 16}),
              yaxis=dict(showgrid=False, title_text='Count', title_font = {"size": 16}, rangemode='tozero'),
              plot_bgcolor='rgba(0,0,0,0)'
          )

      elif fig_name == "stage_heatmap":
        alert_stage_stats = sc_stats.alert_stage_stats
        stages = alert_stage_stats['daily_high_fidelity_count_by_stage']['stage']
        stages.reverse()

        fig = go.Figure(data=go.Heatmap(
                z=np.flip(alert_stage_stats['daily_high_fidelity_count_by_stage']['count_matrix'], 0),
                x=alert_stage_stats['daily_high_fidelity_count_by_stage']['date'],
                y=stages,
                colorscale='geyser',
                colorbar=dict(title='High<br>Fidelity<br>Count', title_font = {"size": 12})
                )
            )

        fig.update_layout(
            width=630,
            height=280,
            margin=go.layout.Margin(
              l=0, #left margin
              r=0, #right margin
              b=0, #bottom margin
              t=50, #top margin
            ),
            font={
                    "family": "Lato",
                    "size": 12,
                    "color": "#707070",
                },
            xaxis=dict(showgrid=False, title_text='Date', title_font = {"size": 16}),
            yaxis=dict(showgrid=False, title_text='Kill Chain Stage', title_font = {"size": 16}, nticks=len(alert_stage_stats['daily_high_fidelity_count_by_stage']['stage'])),
        )

      elif fig_name == "tactic_heatmap":
        alert_tactic_stats = sc_stats.alert_tactic_stats
        tactics = []
        for i in range(0, len(alert_tactic_stats['stage_tactic_list'][0])):
            tactics.append(alert_tactic_stats['stage_tactic_list'][0][i] + ' - ' + alert_tactic_stats['stage_tactic_list'][1][i] )

        fig = go.Figure(data=go.Heatmap(
                z=alert_tactic_stats['stage_tactic_matrix'],
                x=alert_tactic_stats['dates_sorted'],
                y=tactics,
                colorscale='geyser',
                colorbar=dict(title='High<br>Fidelity<br>Count', title_font = {"size": 12})
                )
            )

        fig.update_layout(
            width=630,
            height=900,
            margin=go.layout.Margin(
              #l=100, #left margin
              #r=100, #right margin
              #b=0, #bottom margin
              t=40, #top margin
            ),
            font={
                  "family": "Lato",
                  "size": 10,
                  "color": "#707070",
              },
            xaxis=dict(showgrid=False, title_text='Date', title_font = {"size": 16}),
            yaxis=dict(showgrid=False, title_text='Tactics Grouped By Kill Chain Stage', title_font = {"size": 16}, nticks=len(tactics), autorange='reversed'),
        )

      elif fig_name == "volume_assets_line_graph":
        days = daily_date_scale
        volume_stats = sc_stats.volume_stats
        asset_stats = sc_stats.asset_stats
        volume = np.array(volume_stats['volume_per_day']['volume']) / 1000 / 1000 / 1000  # Get value in GB
        assets = asset_stats['assets_per_day']['count']
  
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=days, y=volume, name='Data Volume (GB)', line=dict(color='#1a76ff', width=2)),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=days, y=assets, name='Assets', line=dict(color='#00c698', width=2)),
            secondary_y=True)

        fig.update_layout(
            width=630,
            height=300,
            margin=go.layout.Margin(
              l=0, #left margin
              r=0, #right margin
              b=0, #bottom margin
              t=0, #top margin
            ),
            font={
                  "family": "Lato",
                  "size": 12,
                  "color": "#707070",
              },
            xaxis=dict(showgrid=False, title_text='Date', title_font = {"size": 16}),
            plot_bgcolor='rgba(0,0,0,0)'
        )
  
        fig.update_yaxes(title_text='Data Volume (GB)', secondary_y=False, rangemode='tozero', title_font = {"size": 16})
        fig.update_yaxes(title_text="Assets", secondary_y=True, rangemode='tozero', title_font = {"size": 16})
  
      elif fig_name == "alert_map":
        alert_geo_stats = sc_stats.alert_geo_stats
        fig = go.Figure(data=go.Choropleth(
            locations = alert_geo_stats['high_fidelity_count_by_country']['alpha_3'],
            z = alert_geo_stats['high_fidelity_count_by_country']['count'],
            colorscale = 'geyser',
            autocolorscale=False,
            marker_line_color='darkgray',
            marker_line_width=0.5,
            colorbar_title = 'High<br>Fidelity<br>Count',
            colorbar_thickness=5,
            zmin=0,
            zmax= max(alert_geo_stats.get('high_fidelity_count_by_country',{}).get('count', []), default=0)
        ))

        fig.update_layout(
            width=630,
            height=400,
            geo=dict(
                showframe=False,
                showcoastlines=False,
                projection_type='kavrayskiy7'
            ),
            margin=go.layout.Margin(
              l=0, #left margin
              r=0, #right margin
              b=0, #bottom margin
              t=0, #top margin
            ),
            font={
                  "family": "Lato",
                  "size": 12,
                  "color": "#707070",
              },
        )
 
      elif fig_name == "volume_category_trends":
        days = daily_date_scale
        connectors = np.array(sc_stats.connector_stats['volume_per_day']['volume']) / 1000 / 1000 / 1000  # Get value in GB
        logs = np.array(sc_stats.log_source_stats['volume_per_day']['volume']) / 1000 / 1000 / 1000  # Get value in GB

        # Combine all sensors together
        sensors = np.array(sc_stats.linux_sensor_stats['volume_per_day']['volume']) + \
          np.array(sc_stats.windows_sensor_stats['volume_per_day']['volume']) + \
          np.array(sc_stats.network_sensor_stats['volume_per_day']['volume']) + \
          np.array(sc_stats.security_sensor_stats['volume_per_day']['volume'])
        sensors = sensors / 1000 / 1000 / 1000  # Get value in GB

        fig = go.Figure(data=[
            go.Bar(name='Sensors', x=days, y=sensors, marker_color='#1a76ff'),
            go.Bar(name='Connectors', x=days, y=connectors, marker_color='#00c698'),
            go.Bar(name='Logs', x=days, y=logs, marker_color='#bc5090')
        ])

        fig.update_layout(
              barmode='stack',
              width=630,
              height=280,
              margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=40, #top margin
              ),
              font={
                    "family": "Lato",
                    "size": 12,
                    "color": "#707070",
                },
              xaxis=dict(showgrid=False, title_text='Date', title_font = {"size": 16}),
              yaxis=dict(showgrid=False, title_text='Data Volume (GB)', title_font = {"size": 16}),
              plot_bgcolor='rgba(0,0,0,0)'
          )
      elif fig_name == 'volume_pie_chart':
        categories_sorted, data_sources_sorted, volume_sorted = sc_stats.combine_data_sources()
        df = pd.DataFrame({'Volume': volume_sorted[:10], 'Data Source': data_sources_sorted[:10]})
        fig = px.pie(df, values='Volume', names='Data Source', color_discrete_sequence=px.colors.sequential.RdBu)
         
      elif fig_name == "top_data_sources_volume":

        # Merge all data sources into a single dict
        categories_sorted, data_sources_sorted, volume_sorted = sc_stats.combine_data_sources()

        fig = go.Figure(data=[
            go.Bar(x=data_sources_sorted[0:10], y=volume_sorted[0:10], marker_color='#1a76ff')
        ])

        fig.update_layout(
              width=630,
              height=300,
              margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=0, #top margin
              ),
              font={
                    "family": "Lato",
                    "size": 12,
                    "color": "#707070",
                },
              xaxis=dict(showgrid=False, title_text='Data Source', title_font = {"size": 16}),
              yaxis=dict(showgrid=False, title_text='Data Volume (GB)', title_font = {"size": 16}),
              plot_bgcolor='rgba(0,0,0,0)'
          )
      elif fig_name == "all_data_sources_volume_sankey":

        categories_sorted, data_sources_sorted, volume_sorted = sc_stats.combine_data_sources()

        # Only consider 20
        categories_sorted = categories_sorted[0:20]
        data_sources_sorted = data_sources_sorted[0:20]
        volume_sorted = volume_sorted[0:20]

        # Get connector, log source, sensor totals
        sensor_total = 0
        connector_total = 0
        log_source_total = 0
        for i in range(0, len(categories_sorted)):
          if categories_sorted[i] == 'Sensor':
            sensor_total += volume_sorted[i]
          elif categories_sorted[i] == 'Connector':
            connector_total += volume_sorted[i]
          elif categories_sorted[i] == 'Log Source':
            log_source_total += volume_sorted[i]

        data_source_labels = ['Sensor', 'Connector', 'Log Source'] + list(data_sources_sorted)
        data_source_parents = ['', '', ''] + list(categories_sorted)
        volume = [sensor_total, connector_total, log_source_total] + list(volume_sorted)

        # Prepare sankey data
        colors = {'All Volume': '#D4D4D4', 'Sensor': '#1a76ff', 'Connector': '#00c698', 'Log Source': '#bc5090', 'Edges': '#ECECEC'}
        source = []
        target = []
        label = data_source_labels.copy()
        label.insert(0, 'All Volume')
        node_colors = [colors['All Volume']]

        for i in range(0, len(data_source_labels)):
            if data_source_parents[i] == '':
                source.append(0)
                target.append(label.index(data_source_labels[i]))
                node_colors.append(colors[data_source_labels[i]])
            else:
                source.append(label.index(data_source_parents[i]))
                target.append(i+1)
                node_colors.append(colors[data_source_parents[i]])

        #import pdb; pdb.set_trace()
        fig = go.Figure(data=[go.Sankey(
          node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = label,
            color = node_colors
          ),
          link = dict(
            source = source,
            target = target,
            value = volume,
            color = '#ECECEC'
        ))])

        fig.update_layout(
              height=450,
              margin=go.layout.Margin(
                l=0, #left margin
                r=120, #right margin
                b=10, #bottom margin
                t=0, #top margin
              ),
              font={
                    "family": "Lato",
                    "size": 10,
                    #"color": "#707070",
                },
          )

      return fig