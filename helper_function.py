import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
import pygsheets
import calendar
from datetime import datetime
from pygsheets.address import Address

service_account_path = 'gsheet_api.json'
gc = pygsheets.authorize(service_file=service_account_path)
today = datetime.today()
prev_month = today.month - 1 if today.month > 1 else 12
prev_prev_month = today.month - 2 if today.month > 2 else 12
prev_month = calendar.month_name[prev_month]
prev_prev_month = calendar.month_name[prev_prev_month]

def read_from_gsheets(sheet_id, tab_name):

    _sheet = gc.open_by_key(sheet_id)
    _wksheet = _sheet.worksheet('title', tab_name)
    _df = _wksheet.get_as_df()

    return _df



def read_from_gsheets_area(sheet_id, tab_name, start_cell=None, end_cell=None):
    try:
        sheet = gc.open_by_key(sheet_id)
        wks = sheet.worksheet_by_title(tab_name)

        if start_cell and end_cell:
            data = wks.get_values(start=start_cell, end=end_cell, include_tailing_empty=False)
        else:
            # Read full sheet if range not given
            data = wks.get_all_values(include_tailing_empty=False)

        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])  # First row as headers
        else:
            df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        return pd.DataFrame()


def load_to_gsheets(df_in, sheet_id, tab_name):

    sheet = gc.open_by_key(sheet_id)

    # New Logic to create tab name in gsheet 
    try:
        worksheet = sheet.worksheet('title', tab_name)
        worksheet.clear()  
    except:
        worksheet = sheet.add_worksheet(title=tab_name, rows=df_in.shape[0]+10, cols=df_in.shape[1]+10)

    worksheet.set_dataframe(df_in, (1, 1), fit=True, nan='')



def load_to_gsheets_from_cell(df_in, sheet_id, tab_name, start_cell):
    sheet = gc.open_by_key(sheet_id)
    worksheet = sheet.worksheet_by_title(tab_name)

    addr = pygsheets.Address(start_cell)
    start_row, start_col = addr.row, addr.col

    values = [df_in.columns.tolist()] + df_in.values.tolist()
    end_row = start_row + len(values) -1
    end_col = start_col + len(values[0]) -1 

    start_a1 = pygsheets.Address((start_row, start_col)).label
    end_a1 = pygsheets.Address((end_row, end_col)).label
    cell_range = f"{start_a1}:{end_a1}"

    worksheet.update_values(crange=cell_range, values=values)



def display_chart_with_lines(fig):
    st.markdown('<hr class="chart-line">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<hr class="chart-line">', unsafe_allow_html=True)
year_colors = {
    "2023": "#F57411",  # Orange
    "2024": "#0016A8",  # Blue
    "2025": "#00923D",  # Green
}
years = [2023,2024,2025]

def create_metric_chart(df, month_prefix,metric_prefix,y_label , chart_title):
    # Select columns that match this metric
    # value_cols = [col for col in df.columns if col.startswith(metric_prefix)]
    value_cols=[]
    for yrs in years:
        value_cols.append(metric_prefix+f'_{yrs}')
    # Melt dataframe
    df_melted = df.melt(
        id_vars=month_prefix,
        value_vars=value_cols,
        var_name="Year",
        value_name=y_label
    )
    # Extract year only from column name
    df_melted["Year"] = df_melted["Year"].str.split("_").str[-1]

    fig = px.line(
        df_melted,
        x=month_prefix,
        y=y_label,
        color="Year",
        markers=True,
        color_discrete_map=year_colors,
        line_shape="spline"
    )
    fig.update_layout(
        title={
            "text": f"{chart_title}", 
            "x": 0.5,              # Center title
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 22}
            },
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
    )
    return fig
## Helper function to add styled headings
def add_heading(text, level=1, color="#000000", align="center", margin_top=10, margin_bottom=5):
    """
    Display a styled heading in Streamlit.
    """
    html = f"""
    <h{level} style="
        color: {color};
        text-align: {align};
        margin-top: {margin_top}px;
        margin-bottom: {margin_bottom}px;
        font-family: 'Arial', sans-serif;
    ">
        {text}
    </h{level}>
    """
    st.markdown(html, unsafe_allow_html=True)

def add_gsheet_link(url, text="View Full Pivot Data"):
    html = f"""
    <div style="
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    ">
        <a href="{url}" target="_blank" style="
            font-size: 18px;
            font-weight: bold;
            color: #2ECC71;
            text-decoration: none;
        ">
            🔗 {text}
        </a>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
kpis_metrics_definition = read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Kpi_Metrics_definition')
@st.cache_data
def calc_avg(df ,selected_products):
    df_f = df[df["product_code"].isin(selected_products)]
    if df_f.empty:
        return None
    col_para_n = ""
    col_para_d = ""
    if df_f["Parameter"].iloc[0] == "Score Gain":
        col_para_n = "total_diff_score"
        col_para_d = "total_eid"
    elif df_f["Parameter"].iloc[0] == "Avg Activity / User":
        col_para_n = "total_sequence_name"
        col_para_d = "total_eid"
    elif df_f["Parameter"].iloc[0] == "Avg Questions Answered / User":
        col_para_n = "total_total_scored_items_answered"
        col_para_d = "total_eid"
    elif df_f["Parameter"].iloc[0] == "Avg Tests / User":
        col_para_n = "total_sequence_name"
        col_para_d = "total_eid"

    for c in [f'{col_para_n}_24', f'{col_para_d}_24', f'{col_para_n}_25', f'{col_para_d}_25']:
        df_f[c] = pd.to_numeric(df_f[c], errors='coerce')

    v2024 = df_f[f'{col_para_n}_24'].sum() / df_f[f'{col_para_d}_24'].sum()
    v2025 = df_f[f'{col_para_n}_25'].sum() / df_f[f'{col_para_d}_25'].sum()
    title = df_f["Parameter"].iloc[0]
    return title, v2024, v2025

@st.cache_data
def calc_active_users(df , selected_products):
    df_f = df[df["product_code"].isin(selected_products)]
    if df_f.empty:
        return None
    for c in ['total_active_user_24', 'total_active_user_25']:
        df_f[c] = pd.to_numeric(df_f[c], errors='coerce')
    v2024 = df_f["total_active_user_24"].sum()  
    v2025 = df_f["total_active_user_25"].sum()  
    title = df_f["Parameter"].iloc[0]
    return title, v2024, v2025

@st.cache_data
def get_req_filtered_df(df_in, prod_code , param_col,agg_col):
    filtered_df = df_in[df_in['product_code'].isin(prod_code)]
    final_df = pd.DataFrame(df_in['Expiry_month'].unique(), columns=['Expiry_month'])
    for yrs in years:
        agg_df = filtered_df.groupby(['Expiry_month']).agg({
            f'kbs_enrollment_id_{yrs}':'sum',
            f'{agg_col}_{yrs}':'sum',
        }).reset_index()
        agg_df[f'{param_col}_{yrs}'] = agg_df[f'{agg_col}_{yrs}'] / agg_df[f'kbs_enrollment_id_{yrs}']
        final_df = pd.merge(final_df, agg_df, on='Expiry_month', how='left')
    final_df = final_df.fillna(0)
    return final_df

@st.cache_data
def get_req_filtered_df_scores(df_in, prod_code , agg_month,param_col,agg_col,prefix_name):
    filtered_df = df_in[df_in['product_code'].isin(prod_code)]
    final_df = pd.DataFrame(df_in[agg_month].unique(), columns=[agg_month])
    for yrs in years:
        agg_df = filtered_df.groupby([agg_month]).agg({
            f'{prefix_name}_score_kbs_enrollment_id_{yrs}':'sum',
            f'{prefix_name}_{agg_col}_{yrs}':'sum',
        }).reset_index()
        agg_df[f'{prefix_name}_{param_col}_{yrs}'] = agg_df[f'{prefix_name}_{agg_col}_{yrs}'] / agg_df[f'{prefix_name}_score_kbs_enrollment_id_{yrs}']
        final_df = pd.merge(final_df, agg_df, on=agg_month, how='left')
    final_df = final_df.fillna(0)
    final_df = final_df.replace(0,'')
    # print(prefix_name , prod_code, final_df.head())
    return final_df

def get_req_filtered_df_act_ques_pt(df_in, prod_code , agg_month,param_col,agg_col):
    filtered_df = df_in[df_in['product_code'].isin(prod_code)]
    final_df = pd.DataFrame(df_in[agg_month].unique(), columns=[agg_month])
    for yrs in years:
        agg_df = filtered_df.groupby([agg_month]).agg({
            f'{param_col}_kbs_enrollment_id_{yrs}':'sum',
            f'{param_col}_{agg_col}_{yrs}':'sum',
        }).reset_index()
        agg_df[f'{param_col}_{yrs}'] = agg_df[f'{param_col}_{agg_col}_{yrs}'] / agg_df[f'{param_col}_kbs_enrollment_id_{yrs}']
        final_df = pd.merge(final_df, agg_df, on=agg_month, how='left')
    final_df = final_df.fillna(0)
    final_df = final_df.replace(0,'')
    # print(param_col , final_df.columns)
    return final_df

def build_cards_html(registry , selected_products):
    cards = []
  
    for item in registry:
        df = item["df"]
        calc = item["calc"]
        result = calc(df , selected_products)
        if result is None:
            # optional: show a placeholder card for empty result
            continue
        title, v2024, v2025 = result

        try:
            change = float(v2025) - float(v2024)
        except Exception:
            change = 0.0

        arrow = "🔼" if change >= 0 else "🔻"
        change_class = "positive" if change >= 0 else "negative"

        # Format display values (choose formatting per KPI type)
        def fmt(x):
            if pd.isna(x):
                return "—"
            # for percentages you might format differently, but keep generic here
            if abs(float(x)) >= 1000:
                return f"{(float(x)):,.0f}"
            return f"{float(x):.1f}" if isinstance(x, (int,float,np.floating)) else str(x)
        KPIs_def = ''
        if title == 'Score Gain':
            KPIs_def = kpis_metrics_definition.loc[kpis_metrics_definition['KPI_Metrics'] == 'Score Gain', 'Definition'].iloc[0]
        elif title == 'Avg Activity / User':
            KPIs_def = kpis_metrics_definition.loc[kpis_metrics_definition['KPI_Metrics'] == 'Avg Activity / User', 'Definition'].iloc[0]   
        elif title == 'Active Users':
            KPIs_def = kpis_metrics_definition.loc[kpis_metrics_definition['KPI_Metrics'] == 'Active Users', 'Definition'].iloc[0]
        elif title == 'Avg Questions Answered / User':
            KPIs_def = kpis_metrics_definition.loc[kpis_metrics_definition['KPI_Metrics'] == 'Avg Questions Answered / User', 'Definition'].iloc[0]
        elif title == 'Avg Tests / User':
            KPIs_def = kpis_metrics_definition.loc[kpis_metrics_definition['KPI_Metrics'] == 'Avg Tests / User', 'Definition'].iloc[0]
        else:
            KPIs_def = "Somethig went wrong"
        card_html = f"""
<div class="kpi-card">
    <div class="kpi-section">
    <div class="kpi-title">
        {title}
        <span class="tooltip">
            💡
            <span class="tooltiptext">
                {KPIs_def}
            </span>
        </span>
    </div>
    <p class="kpi-value">2024: {fmt(v2024)}</p>
    <p class="kpi-value">2025: {fmt(v2025)}</p>
    <div class="kpi-change {change_class}">{arrow} {fmt(change)}</div>
    </div>
    </div>
"""

        cards.append(card_html.strip())

    # Join cards cleanly without extra newlines or spaces
    return "\n".join(cards)

