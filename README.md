In this tutorial you learn how to build a demo dashboard application on [Google Cloud Platform](https://cloud.google.com/) by using the [Bokeh](http://bokeh.pydata.org/en/latest/) library to visualize data from publicly available [Google BigQuery](https://cloud.google.com/bigquery/) datasets. You also learn how to deploy this application with both security and scalability in mind.

Please refer to the related article for all the steps to follow in this tutorial: https://cloud.google.com/solutions/bokeh-and-bigquery-dashboards

Contents of this repository:

* `dashboard`: Python code to generate the dashboard using the Bokeh library. This folder also contains a `Dockerfile` in case you wish to build the container.
* `kubernetes`: Configuration files to deploy the application using [Kubernetes](https://kubernetes.io/).
