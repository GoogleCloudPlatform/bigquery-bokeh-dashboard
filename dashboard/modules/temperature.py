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
from bokeh.models import ColumnDataSource, HoverTool, DataRange1d, Paragraph
from bokeh.layouts import column
from bokeh.palettes import Blues4
from bokeh.plotting import figure

from modules.base import BaseModule
from states import NAMES_TO_CODES
from utils import run_query


QUERY = """
    SELECT
      year,
      mo as month,
      da as day,
      MAX(max) as max_temp,
      MIN(min) as min_temp,
      AVG(temp) as avg_temp,
      state
    FROM
      [bigquery-public-data:noaa_gsod.gsod%(year)s] a
    JOIN
      [bigquery-public-data:noaa_gsod.stations] b
    ON
      a.stn=b.usaf
      AND a.wban=b.wban
    WHERE
      state IS NOT NULL
      AND max < 1000
      AND country = 'US'
      AND state = '%(state)s'
    GROUP BY
      year, month, day, state
    ORDER BY
      year, month, day, state
"""

YEAR = 2016
TITLE = "Temperatures (F) in %s:" % YEAR


class Module(BaseModule):

    def __init__(self):
        super().__init__()
        self.source = None
        self.plot = None
        self.title = None

    def fetch_data(self, state):
        query = QUERY % {'state': NAMES_TO_CODES[state], 'year': YEAR}
        dataframe = run_query(query, cache_key='temperature-%s' % NAMES_TO_CODES[state])
        dataframe['date'] = pd.to_datetime(dataframe[['year', 'month', 'day']])
        dataframe['date_readable'] = dataframe['date'].apply(lambda x: x.strftime("%Y-%m-%d"))
        dataframe['left'] = dataframe.date - pd.DateOffset(days=0.5)
        dataframe['right'] = dataframe.date + pd.DateOffset(days=0.5)
        dataframe = dataframe.set_index(['date'])
        dataframe.sort_index(inplace=True)
        return dataframe

    def make_plot(self, dataframe):
        self.source = ColumnDataSource(data=dataframe)
        self.plot = figure(
            x_axis_type="datetime", plot_width=600, plot_height=300,
            tools='', toolbar_location=None)
        self.plot.quad(
            top='max_temp', bottom='min_temp', left='left', right='right',
            color=Blues4[2], source=self.source, legend='Magnitude')
        line = self.plot.line(
            x='date', y='avg_temp', line_width=3, color=Blues4[1],
            source=self.source, legend='Average')
        hover_tool = HoverTool(tooltips=[
            ('Value', '$y'),
            ('Date', '@date_readable'),
        ], renderers=[line])
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
