import plotly.graph_objs as go
from datetime import datetime


def lines_to_plot(df, ids):
    data = []
    for i, nm in enumerate(ids):
        line = go.Scatter(
            x = df.index,
            y = df[nm],
            mode = 'lines',
            name = nm
        )
        data.append(line)
    return data

def ql_to_datetime(d):
    return datetime(d.year(), d.month(), d.dayOfMonth())

def ql_to_date(d):
    return datetime(d.year(), d.month(), d.dayOfMonth()).date()