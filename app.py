import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import time
import calendar
from datetime import datetime
today = datetime.today()
prev_month = today.month - 1 if today.month > 1 else 12
prev_month = calendar.month_name[prev_month]
# Streamlit version compatibility check for Posit deployment
try:
    # Check if we have the minimum required version features
    if not hasattr(st, 'cache_data'):
        st.error("⚠️ This app requires Streamlit 1.18.0 or higher. Please update Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"Version compatibility issue: {e}")

# Compatible rerun function for different Streamlit versions and Posit deployment
def compatible_rerun():
    """Use appropriate rerun method based on Streamlit version and deployment environment"""
    try:
        if hasattr(st, 'rerun'):
            st.rerun()
        elif hasattr(st, 'experimental_rerun'):
            st.experimental_rerun()
        else:
            # Fallback for older versions
            st.legacy_caching.clear_cache()
            st.experimental_rerun()
    except Exception as e:
        # Silent fallback - don't break the app
        pass

from helper_function import add_heading , create_metric_chart ,display_chart_with_lines,add_gsheet_link,get_req_filtered_df_scores,get_req_filtered_df_act_ques_pt
from helper_function import calc_avg , calc_active_users,get_req_filtered_df,build_cards_html , load_to_gsheets , read_from_gsheets,read_from_gsheets_area

st.set_page_config(
    page_title="MCAT Dashboard", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=900)  # Cache for 15 minutes - Compatible with Streamlit 1.50+
def load_data():
    """Load all data from Google Sheets with caching"""
    return {
        'product_code_df': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Product Code'),
        'KPI_data_all': read_from_gsheets_area('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','KPIs_sheet','A2','AF27'),
        'KPI_data_Pm_all': read_from_gsheets_area('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','KPIs_sheet_tll_PM','A2','AF27'),

        'prod_score_gain_data': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Score_Gain_Sheet'),
        'DScBd_metrics': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Detailed Score Breakdown_Metrics'),
        'monthly_fl_metrics': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Monthly Full Length Engagement_metrics'),   
        'monthwise_act_ques_pt_metrics': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Monthwise Activity_Questions_PT_metrics'),
        'act_comp_trend': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Activity_Completion_Trends(30_60_90_days)_metrics'),
        'ques_comp_trend': read_from_gsheets('1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4','Ques_Ans_Completion_Trends(30_60_90_days)_metrics')
    }



# Load all data with caching and error handling
try:
    with st.spinner("Loading data from Google Sheets..."):
        data = load_data()
    
    product_code_df = data['product_code_df']
    score_gain_kpi = data['KPI_data_all'].iloc[:,0:6]
    act_per_user_kpi = data['KPI_data_all'].iloc[:,7:13]
    active_user_kpi = data['KPI_data_all'].iloc[:,14:18]
    ques_ans_kpi = data['KPI_data_all'].iloc[:,19:25]
    test_per_user_kpi = data['KPI_data_all'].iloc[:,26:32]

    score_gain_kpi_pm = data['KPI_data_Pm_all'].iloc[:,0:6]
    act_per_user_kpi_pm = data['KPI_data_Pm_all'].iloc[:,7:13]
    active_user_kpi_pm = data['KPI_data_Pm_all'].iloc[:,14:18]
    ques_ans_kpi_pm = data['KPI_data_Pm_all'].iloc[:,19:25]
    test_per_user_kpi_pm = data['KPI_data_Pm_all'].iloc[:,26:32]

    DScBd_metrics = data['DScBd_metrics']
    monthly_fl_metrics = data['monthly_fl_metrics']
    monthwise_act_ques_pt_metrics = data['monthwise_act_ques_pt_metrics']
    prod_score_gain_data = data['prod_score_gain_data']
    act_comp_trend = data['act_comp_trend']
    ques_comp_trend = data['ques_comp_trend']
    
    # Validate data loaded successfully
    if product_code_df.empty:
        st.error("⚠️ No product code data loaded. Please check Google Sheets connection.")
        st.stop()
        
except Exception as e:
    st.error(f"🚨 Error loading data: {str(e)}")
    st.info("💡 This might be a temporary connectivity issue. Please refresh the page.")
    st.stop()

# Load CSS with error handling for deployment
try:
    with open("style.css", "r", encoding="utf-8") as f:
        css_content = f.read()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ CSS file not found. Using default styling.")
except Exception as e:
    st.warning(f"⚠️ CSS loading issue: {e}")
st.markdown("<h1 style='text-align: center;'>MCAT Student Engagement Dashboard 📊</h1>", unsafe_allow_html=True)
add_gsheet_link('https://docs.google.com/spreadsheets/d/1wZmKXpk0nXaQb1aNvzjb-PFkVlpqvOc8Lj4_o49oso4/','Data Source Link to all Kpis and Metrics')

# Initialize session state variables after data is loaded successfully
if "filter_panel" not in st.session_state:
    st.session_state.filter_panel = False
if "selected_products" not in st.session_state:
    # Ensure we have valid product codes before initializing
    available_products = product_code_df["product_code"].dropna().unique().tolist()
    st.session_state.selected_products = available_products if available_products else []

# ------------------------------
# Sidebar filter toggle (gear icon)
# ------------------------------
with st.sidebar:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
    if st.button("⚙️ Filters"):
        st.session_state.filter_panel = not st.session_state.filter_panel

    if st.session_state.filter_panel:
        st.write("### Product Filter")

        all_products = sorted(product_code_df["product_code"].unique())

        # Session State-Driven Approach - Single source of truth
        
        # Initialize debounce timers for buttons
        if "last_select_all_click" not in st.session_state:
            st.session_state.last_select_all_click = 0
        if "last_clear_all_click" not in st.session_state:
            st.session_state.last_clear_all_click = 0
            
        # Button actions with independent debounce (0.5 seconds each)
        current_time = time.time()
        select_all_disabled = (current_time - st.session_state.last_select_all_click) < 0.5
        clear_all_disabled = (current_time - st.session_state.last_clear_all_click) < 0.5
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Select All", key="select_all_btn", use_container_width=True, disabled=select_all_disabled):
                if not select_all_disabled:  # Double-check to prevent race conditions
                    # Update session state and force widget refresh by changing its key
                    st.session_state.selected_products = all_products.copy()
                    st.session_state.multiselect_key = f"multiselect_selectall_{int(time.time()*1000)}"
                    st.session_state.last_select_all_click = current_time
                    compatible_rerun()
                
        with col2:
            if st.button("Clear All", key="clear_all_btn", use_container_width=True, disabled=clear_all_disabled):
                if not clear_all_disabled:  # Double-check to prevent race conditions
                    # Update session state and force widget refresh by changing its key
                    st.session_state.selected_products = []
                    st.session_state.multiselect_key = f"multiselect_clearall_{int(time.time()*1000)}"
                    st.session_state.last_clear_all_click = current_time
                    compatible_rerun()
        
        # Initialize multiselect key if not exists
        if "multiselect_key" not in st.session_state:
            st.session_state.multiselect_key = "multiselect_initial"
        
        # Callback function to handle multiselect changes with error prevention
        def on_multiselect_change():
            # Safely update session state - prevent KeyError from rapid button clicks
            current_key = st.session_state.multiselect_key
            if current_key in st.session_state:
                st.session_state.selected_products = st.session_state[current_key]
            else:
                # Fallback: keep existing selection if key doesn't exist (race condition)
                pass
        
        # Multiselect widget with dynamic key and callback
        selected_products = st.multiselect(
            "Select Product Codes",
            options=all_products,
            default=st.session_state.selected_products,
            key=st.session_state.multiselect_key,
            on_change=on_multiselect_change,
            help="💡 Tip: Use the buttons above for Select All/Clear All operations"
        )

# Create a container for filter status that updates dynamically
filter_status_container = st.container()

with filter_status_container:
    # Calculate filter status in real-time (this runs after any session state changes)
    selected_count = len(st.session_state.selected_products)
    total_count = len(product_code_df["product_code"].unique())
    
    # Force recalculation on every render to ensure Posit compatibility
    if selected_count == total_count:
        filter_text = "All Products Selected"
        status_color = "#00923D"  # Green
    elif selected_count == 0:
        filter_text = "No Products Selected" 
        status_color = "#F57411"  # Orange
    else:
        # Show first few products and count if many selected
        if selected_count <= 3:
            products_display = ", ".join(st.session_state.selected_products)
        else:
            products_display = f"{', '.join(st.session_state.selected_products[:2])} and {selected_count - 2} more"
        filter_text = f"Selected: {products_display}"
        status_color = "#0016A8"  # Blue
    
    # Enhanced filter status display with color coding
    st.markdown(f"""
    <div class="filter-status" style="border-left: 4px solid {status_color}; padding: 10px; margin: 10px 0;">
        <div class="filter-status-text">
            <span class="filter-status-icon">🎯</span>
            <strong>{filter_text}</strong>
            <span class="product-count" style="background: {status_color}; color: black; padding: 2px 8px; border-radius: 12px; margin-left: 10px;">
                {selected_count}/{total_count}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

#--- KPIs calculation and display- Start
kpi_registry = [
    {"df": score_gain_kpi, "calc": calc_avg},
    {"df": act_per_user_kpi, "calc": calc_avg},
    {"df": active_user_kpi, "calc": calc_active_users},
    {"df": ques_ans_kpi, "calc": calc_avg},
    {"df": test_per_user_kpi, "calc": calc_avg},
]
kpi_registry_pm = [
    {"df": score_gain_kpi_pm, "calc": calc_avg},
    {"df": act_per_user_kpi_pm, "calc": calc_avg},
    {"df": active_user_kpi_pm, "calc": calc_active_users},
    {"df": ques_ans_kpi_pm, "calc": calc_avg},
    {"df": test_per_user_kpi_pm, "calc": calc_avg}
]

# Safety check for empty selections
if not st.session_state.selected_products:
    st.warning("⚠️ No products selected. Please select at least one product to view KPIs.")
    st.markdown("<div class='kpi-container'>No data to display</div>", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class="kpi-subheading">KPIs for the month of <span class="highlight-month">{prev_month}</span></div>""", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-container'>{build_cards_html(kpi_registry , st.session_state.selected_products)}</div>", unsafe_allow_html=True)
    st.markdown(f"""<div class="kpi-subheading">KPIs for January to <span class="highlight-month">{prev_month}</span></div>""", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-container'>{build_cards_html(kpi_registry_pm , st.session_state.selected_products)}</div>", unsafe_allow_html=True)



#--- KPIs calculation and display- End


def display_chart_with_lines(fig):
    st.markdown('<hr class="chart-line">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<hr class="chart-line">', unsafe_allow_html=True)
year_colors = {
    "2023": "#F57411",  # Orange
    "2024": "#0016A8",  # Blue
    "2025": "#00923D",  # Green
}
# Score Gain by Expiry Month
score_gain_data_filt = get_req_filtered_df(prod_score_gain_data, st.session_state.selected_products,'Score_gain','score_gain')
score_gain_melted = score_gain_data_filt.melt(id_vars="Expiry_month",
                    value_vars=["Score_gain_2023", "Score_gain_2024", "Score_gain_2025"],
                    var_name="Year",
                    value_name="Score Gain")
score_gain_melted["Year"] = score_gain_melted["Year"].str.split("_").str[-1]
score_gain_colors = {
    "2023": "#F57411",  # Orange
    "2024": "#0016A8",  # Blue
    "2025": "#00923D",  # Green
}
add_heading("Score Gain by Expiry Month", level=3, color="#000000")
fig = px.line(
    score_gain_melted,
    x="Expiry_month",
    y="Score Gain",
    color="Year",
    markers=True,  # add points on lines
    color_discrete_map=score_gain_colors,
    line_shape="spline"

)
fig.update_layout(
     title={
        "text": "",
        "x": 0.5,              # Center title
        "xanchor": "center",
        "yanchor": "top",
        "font": {"size": 22}
    },
    xaxis_title="Expiry Month",
    yaxis_title="Score Gain",
    legend_title="Year",
    template="plotly_dark",  # since your page is dark themed
    plot_bgcolor="rgba(0,0,0,0)",  # transparent plot area
    paper_bgcolor="rgba(0,0,0,0)",  # transparent background
)


st.markdown('<hr class="chart-line">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True)
st.markdown('<hr class="chart-line">', unsafe_allow_html=True)

# Detailed Score Breakdown Charts
add_heading("Detailed Score Breakdown by Expiry Month", level=3, color="#000000")
# Display three charts side by side
first_score_ch_filt = get_req_filtered_df_scores(DScBd_metrics.iloc[:,0:8],st.session_state.selected_products ,'Expiry_month', 'Score_Avg' , 'score_scaled_score','First')
max_score_ch_filt = get_req_filtered_df_scores(DScBd_metrics.iloc[:,8:16],st.session_state.selected_products ,'Expiry_month', 'Score_Avg' , 'score_scaled_score','Max')
latest_score_ch_filt = get_req_filtered_df_scores(DScBd_metrics.iloc[:,16:24],st.session_state.selected_products ,'Expiry_month', 'Score_Avg' , 'score_scaled_score','Latest')

col1, col2, col3 = st.columns(3)
with col1:
    display_chart_with_lines(create_metric_chart(first_score_ch_filt, 'Expiry_month',"First_Score_Avg",'Score','First Score Average'))

with col2:
    display_chart_with_lines(create_metric_chart(max_score_ch_filt, 'Expiry_month',"Max_Score_Avg",'Score','Max Score Average'))

with col3:
    display_chart_with_lines(create_metric_chart(latest_score_ch_filt, 'Expiry_month',"Latest_Score_Avg",'Score','Latest Score Average'))

## Month Wise Full length 
add_heading("Monthly Full Length Score Averages by Activity Month", level=3, color="#000000")
aamc1 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,0:8], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'AAMC1')
kfl1 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,8:16], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'KFL1')
kfl2 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,16:24], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'KFL2')
kfl3 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,24:32], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'KFL3')
col1, col2, col3 , col4 = st.columns(4)
with col1:
    display_chart_with_lines(create_metric_chart(aamc1, 'Activity_month',"AAMC1_Avg_Score",'Score','AAMC1 Average Score'))
with col2:
    display_chart_with_lines(create_metric_chart(kfl1, 'Activity_month',"KFL1_Avg_Score",'Score','KFL1 Average Score'))
with col3:
    display_chart_with_lines(create_metric_chart(kfl2, 'Activity_month',"KFL2_Avg_Score",'Score','KFL2 Average Score'))
with col4:
    display_chart_with_lines(create_metric_chart(kfl3, 'Activity_month',"KFL3_Avg_Score",'Score','KFL3 Average Score'))

aamc2 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,32:40], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'AAMC2')
aamc3 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,40:48], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'AAMC3')
aamc4 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,48:56], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'AAMC4')
aamc5 = get_req_filtered_df_scores(monthly_fl_metrics.iloc[:,56:64], st.session_state.selected_products, 'Activity_month','Avg_Score', 'score_scaled_score', 'AAMC5')
col1, col2, col3 , col4 = st.columns(4)
with col1:
    display_chart_with_lines(create_metric_chart(aamc2, 'Activity_month',"AAMC2_Avg_Score",'Score','AAMC2 Average Score'))
with col2:
    display_chart_with_lines(create_metric_chart(aamc3, 'Activity_month',"AAMC3_Avg_Score",'Score','AAMC3 Average Score'))
with col3:
    display_chart_with_lines(create_metric_chart(aamc4, 'Activity_month',"AAMC4_Avg_Score",'Score','AAMC4 Average Score'))
with col4:
    display_chart_with_lines(create_metric_chart(aamc5, 'Activity_month',"AAMC5_Avg_Score",'Score','AAMC5 Average Score'))

## Monthwise Activity, Questions and Practice Test
add_heading("Monthwise Activity, Questions Answered & Practice Test Per User by Activity Month", level=3, color="#000000")
month_act = get_req_filtered_df_act_ques_pt(monthwise_act_ques_pt_metrics.iloc[:,0:8], st.session_state.selected_products, 'Activity_month', 'Avg_Activity', 'sequence_title',)
month_ques = get_req_filtered_df_act_ques_pt(monthwise_act_ques_pt_metrics.iloc[:,8:16], st.session_state.selected_products, 'Activity_month', 'Avg Question Answered', 'total_scored_items_answered')
month_pt = get_req_filtered_df_act_ques_pt(monthwise_act_ques_pt_metrics.iloc[:,16:24], st.session_state.selected_products, 'Activity_month', 'Avg Practice Test', 'sequence_name')

col1, col2, col3  = st.columns(3)
with col1:
    display_chart_with_lines(create_metric_chart(month_act, 'Activity_month',"Avg_Activity",'Average Activity','Average Activity'))
with col2:
    display_chart_with_lines(create_metric_chart(month_ques, 'Activity_month',"Avg Question Answered",'Average Questions Answered','Average Questions Answered'))
with col3:
    display_chart_with_lines(create_metric_chart(month_pt, 'Activity_month',"Avg Practice Test",'Average Practice Test','Average Practice Test'))

## Activities Completed Trends 30,60,90 days
add_heading("Activity Completion Trend First 30,60,90 days from ESD", level=3, color="#000000")
act_30_days = get_req_filtered_df_act_ques_pt(act_comp_trend.iloc[:,0:8], st.session_state.selected_products, 'ESD_month', 'Activity_30_days', 'sequence_title')
act_60_days = get_req_filtered_df_act_ques_pt(act_comp_trend.iloc[:,8:16], st.session_state.selected_products, 'ESD_month', 'Activity_60_days', 'sequence_title')
act_90_days = get_req_filtered_df_act_ques_pt(act_comp_trend.iloc[:,16:24], st.session_state.selected_products, 'ESD_month', 'Activity_90_days', 'sequence_title')

col1, col2, col3  = st.columns(3)
with col1:
    display_chart_with_lines(create_metric_chart(act_30_days, 'ESD_month',"Activity_30_days",'Activity Completed in 30 Days','Activity Completed in 30 Days'))
with col2:
    display_chart_with_lines(create_metric_chart(act_60_days, 'ESD_month',"Activity_60_days",'Activity Completed in 60 Days','Activity Completed in 60 Days'))
with col3:
    display_chart_with_lines(create_metric_chart(act_90_days, 'ESD_month',"Activity_90_days",'Activity Completed in 90 Days','Activity Completed in 90 Days'))

## Questions Completed Trends 30,60,90 days
add_heading("Questions Completion Trend First 30,60,90 days from ESD", level=3, color="#000000")
ques_30_days = get_req_filtered_df_act_ques_pt(ques_comp_trend.iloc[:,0:8], st.session_state.selected_products, 'ESD_month', 'Ques_Ans_30_days', 'total_scored_items_answered')
ques_60_days = get_req_filtered_df_act_ques_pt(ques_comp_trend.iloc[:,8:16], st.session_state.selected_products, 'ESD_month', 'Ques_Ans_60_days', 'total_scored_items_answered')
ques_90_days = get_req_filtered_df_act_ques_pt(ques_comp_trend.iloc[:,16:24], st.session_state.selected_products, 'ESD_month', 'Ques_Ans_90_days', 'total_scored_items_answered')

col1, col2, col3  = st.columns(3)
with col1:
    display_chart_with_lines(create_metric_chart(ques_30_days, 'ESD_month',"Ques_Ans_30_days",'Questions Answered in 30 Days','Questions Answered in 30 Days'))
with col2:
    display_chart_with_lines(create_metric_chart(ques_60_days, 'ESD_month',"Ques_Ans_60_days",'Questions Answered in 60 Days','Questions Answered in 60 Days'))
with col3:
    display_chart_with_lines(create_metric_chart(ques_90_days, 'ESD_month',"Ques_Ans_90_days",'Questions Answered in 90 Days','Questions Answered in 90 Days'))

