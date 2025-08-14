import dash
import os
from dash import dcc, html, Input, Output
import pandas as pd
import pyodbc
import plotly.express as px

driver = os.environ['DB_DRIVER']
server = os.environ['DB_SERVER']
database = os.environ['DB_NAME']
username = os.environ['DB_USER']
password = os.environ['DB_PASSWORD']

def get_connection():
    return pyodbc.connect(
        f"DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
    )

# Load distinct security descriptions for dropdown
def get_security_descriptions():
    conn = get_connection()
    query = "SELECT DISTINCT SecurityDescription FROM dbo.India_regular_market ORDER BY SecurityDescription"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['SecurityDescription'].tolist()

# Load data for selected security
def get_security_data(security_desc):
    conn = get_connection()
    query = f"""
    SELECT ScrapeTimestamp, Trades, TTA
    FROM dbo.India_regular_market
    WHERE [SecurityDescription] = ?
    ORDER BY [ScrapeTimestamp] 
    """
    df = pd.read_sql(query, conn, params=[security_desc])
    conn.close()

    
    def day_with_suffix(day):
        if 11 <= day <= 13:
            return f"{day}th"
        last_digit = day % 10
        if last_digit == 1:
            return f"{day}st"
        elif last_digit == 2:
            return f"{day}nd"
        elif last_digit == 3:
            return f"{day}rd"
        else:
            return f"{day}th"

    df['ScrapeTimestampFormatted'] = df['ScrapeTimestamp'].apply(
        lambda x: f"{x.strftime('%b')} {day_with_suffix(x.day)}, {x.strftime('%H:%M')}"
    )

    return df

# Dash app
app = dash.Dash(__name__)
app.title = "Regular Market Dashboard"

app.layout = html.Div([
    html.H1("Regular Market Time Series Dashboard"),
    
    html.Label("Select Security Description:"),
    dcc.Dropdown(
        id='security-dropdown',
        options=[{'label': desc, 'value': desc} for desc in get_security_descriptions()],
        value=None,
        placeholder="Choose a Security Description"
    ),
    
    dcc.Graph(id='timeseries-chart')
])

@app.callback(
    Output('timeseries-chart', 'figure'),
    Input('security-dropdown', 'value')
)

def update_chart(security_desc):
    if not security_desc:
        return px.line(title="Select a Security Description to view data")

    df = get_security_data(security_desc)
    if df.empty:
        return px.line(title="No data available")

    fig = px.line(df, x="ScrapeTimestampFormatted", y=["Trades", "TTA"],
                  labels={"value": "Count / Amount", "variable": "Metric"},
                  title=f"Trades & TTA for {security_desc}")
    fig.update_traces(mode="lines+markers")
    return fig

if __name__ == "__main__":
    app.run(debug=True)
