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


import pandas as pd

from bokeh.models import ColumnDataSource, HoverTool, Paragraph, DataRange1d
from bokeh.plotting import figure
from bokeh.layouts import column

from modules.base import BaseModule
from utils import run_query
from states import NAMES_TO_CODES


QUERY = """
    SELECT
      YEAR(date) as year,
      MONTH(date) as month,
      DAY(date) as day,
      AVG(prcp) AS prcp
    FROM (
      SELECT
        STRING(date) AS date,
        IF (element = 'PRCP', value/10, NULL) AS prcp
      FROM
        [bigquery-public-data:ghcn_d.ghcnd_%(year)s] AS weather
      JOIN
        [bigquery-public-data:ghcn_d.ghcnd_stations] as stations
      ON
        weather.id = stations.id
      WHERE
        stations.state = '%(state)s'
    )
    GROUP BY
      year, month, day
    ORDER BY
      year, month, day
"""

YEAR = 2016
TITLE = 'Precipitation (mm) in %s:' % YEAR


class Module(BaseModule):

    def __init__(self):
        super().__init__()
        self.source = None
        self.plot = None
        self.title = None

    def fetch_data(self, state):
        dataframe = run_query(
            QUERY % {'state': NAMES_TO_CODES[state], 'year': YEAR},
            cache_key=('precipitation-%s' % NAMES_TO_CODES[state]))
        dataframe['date'] = pd.to_datetime(dataframe[['year', 'month', 'day']])
        dataframe['date_readable'] = dataframe['date'].apply(lambda x: x.strftime("%Y-%m-%d"))
        return dataframe

    def make_plot(self, dataframe):
        self.source = ColumnDataSource(data=dataframe)
        self.plot = figure(
            x_axis_type="datetime", plot_width=400, plot_height=300,
            tools='', toolbar_location=None)

        vbar = self.plot.vbar(
            x='date', top='prcp', width=1, color='#fdae61', source=self.source)
        hover_tool = HoverTool(tooltips=[
            ('Value', '$y'),
            ('Date', '@date_readable'),
        ], renderers=[vbar])
        self.plot.tools.append(hover_tool)

        self.plot.xaxis.axis_label = None
        self.plot.yaxis.axis_label = None
        self.plot.axis.axis_label_text_font_style = 'bold'
        self.plot.x_range = DataRange1d(range_padding=0.0)
        self.plot.grid.grid_line_alpha = 0.3

        self.title = Paragraph(text=TITLE)
        return column(self.title, self.plot)

    def update_plot(self, dataframe):
        self.source.data.update(dataframe)

    def busy(self):
        self.title.text = 'Updating...'
        self.plot.background_fill_color = "#efefef"

    def unbusy(self):
        self.title.text = TITLE
        self.plot.background_fill_color = "white"
