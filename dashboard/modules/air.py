# Copyright Google Inc. 2017
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from bokeh.models import ColumnDataSource, HoverTool, Paragraph
from bokeh.plotting import figure
from bokeh.palettes import all_palettes
from bokeh.layouts import column

from modules.base import BaseModule
from utils import run_query
from states import NAMES_TO_CODES


QUERY = """
    SELECT
      pm10.year AS year,
      pm10.avg AS pm10,
      pm25_frm.avg AS pm25_frm,
      pm25_nonfrm.avg AS pm25_nonfrm,
      lead.avg AS lead
    FROM
      ( SELECT avg(arithmetic_mean) as avg, YEAR(date_local) as year
        FROM [bigquery-public-data:epa_historical_air_quality.pm10_daily_summary]
        WHERE state_name = '%(state)s'
        GROUP BY year
      ) AS pm10
    JOIN
      ( SELECT avg(arithmetic_mean) as avg, YEAR(date_local) as year
        FROM [bigquery-public-data:epa_historical_air_quality.pm25_frm_daily_summary]
        WHERE state_name = '%(state)s'
        GROUP BY year
      ) AS pm25_frm ON pm10.year = pm25_frm.year
    JOIN
      ( SELECT avg(arithmetic_mean) as avg, YEAR(date_local) as year
        FROM [bigquery-public-data:epa_historical_air_quality.pm25_nonfrm_daily_summary]
        WHERE state_name = '%(state)s'
        GROUP BY year
      ) AS pm25_nonfrm ON pm10.year = pm25_nonfrm.year
    JOIN
      ( SELECT avg(arithmetic_mean) * 100 as avg, YEAR(date_local) as year
        FROM [bigquery-public-data:epa_historical_air_quality.lead_daily_summary]
        WHERE state_name = "%(state)s"
        GROUP BY year
      ) AS lead ON pm10.year = lead.year
    ORDER BY
      year
"""

TITLE = 'Evolution of air pollutant levels:'


class Module(BaseModule):

    def __init__(self):
        super().__init__()
        self.source = None
        self.plot = None
        self.title = None

    def fetch_data(self, state):
        return run_query(
            QUERY % {'state': state},
            cache_key=('air-%s' % NAMES_TO_CODES[state]))

# [START make_plot]
    def make_plot(self, dataframe):
        self.source = ColumnDataSource(data=dataframe)
        palette = all_palettes['Set2'][6]
        hover_tool = HoverTool(tooltips=[
            ("Value", "$y"),
            ("Year", "@year"),
        ])
        self.plot = figure(
            plot_width=600, plot_height=300, tools=[hover_tool],
            toolbar_location=None)
        columns = {
            'pm10': 'PM10 Mass (µg/m³)',
            'pm25_frm': 'PM2.5 FRM (µg/m³)',
            'pm25_nonfrm': 'PM2.5 non FRM (µg/m³)',
            'lead': 'Lead (¹/₁₀₀ µg/m³)',
        }
        for i, (code, label) in enumerate(columns.items()):
            self.plot.line(
                x='year', y=code, source=self.source, line_width=3,
                line_alpha=0.6, line_color=palette[i], legend=label)

        self.title = Paragraph(text=TITLE)
        return column(self.title, self.plot)
# [END make_plot]

    def update_plot(self, dataframe):
        self.source.data.update(dataframe)

    def busy(self):
        self.title.text = 'Updating...'
        self.plot.background_fill_color = "#efefef"

    def unbusy(self):
        self.title.text = TITLE
        self.plot.background_fill_color = "white"
