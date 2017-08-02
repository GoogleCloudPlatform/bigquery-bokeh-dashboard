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


import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter, Paragraph
from bokeh.layouts import column

from modules.base import BaseModule
from utils import run_query
from states import NAMES_TO_CODES


QUERY = """
    SELECT
      A.zipcode,
      population,
      city,
      state_code
    FROM
      `bigquery-public-data.census_bureau_usa.population_by_zip_2010` AS A
    JOIN
      `bigquery-public-data.utility_us.zipcode_area` AS B
    ON
      A.zipcode = B.zipcode
    WHERE
      gender = ''
      AND state_code = '%(state)s'
    ORDER BY
      population DESC
    LIMIT
      100
"""

TITLE = "Top 100 most populated zipcodes:"


class Module(BaseModule):

    def __init__(self):
        super().__init__()
        self.source = None
        self.data_table = None
        self.title = None

    def fetch_data(self, state):
        dataframe = run_query(
            QUERY % {'state': NAMES_TO_CODES[state]},
            cache_key=('population-%s' % NAMES_TO_CODES[state]),
            dialect='standard')
        dataframe.index = np.arange(1, len(dataframe) + 1)
        return dataframe

    def make_plot(self, dataframe):
        self.source = ColumnDataSource(data=dataframe)
        self.title = Paragraph(text=TITLE)
        self.data_table = DataTable(source=self.source, width=390, height=275, columns=[
            TableColumn(field="zipcode", title="Zipcodes", width=100),
            TableColumn(field="population", title="Population", width=100, formatter=NumberFormatter(format="0,0")),
            TableColumn(field="city", title="City")
        ])
        return column(self.title, self.data_table)

    def update_plot(self, dataframe):
        self.source.data.update(dataframe)

    def busy(self):
        self.title.text = 'Updating...'

    def unbusy(self):
        self.title.text = TITLE
