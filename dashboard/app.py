import streamlit as st
import polars as pl
import duckdb
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="BigSpark EDA Dashboard", page_icon="📈", layout="wide")

# --- Data Caching & Loading System ---
# We use st.cache_data to guarantee the expensive parsing and cleaning 
# only happens once per user session.
@st.cache_data
def load_and_clean_data():
    ## 1. NHS Data
    df_nhs = pl.read_csv("data/dirty_nhs_appointments_v3.csv", null_values=["", "NA", "N/A", "null", "NULL"])
    df_nhs_clean = df_nhs.with_columns([
        pl.col("patient_name").str.strip_chars().str.to_titlecase(),
        pl.col("appointment_date").str.to_date("%Y-%m-%d"),
        pl.col("delay_minutes").fill_null(0.0)
    ])

    ## 2. SaaS CRM Data
    df_crm = pl.read_csv("data/dirty_saas_crm_v3.csv", null_values=["", "NA", "N/A", "null", "NULL"])
    country_map = {"UK": "United Kingdom", "U.K.": "United Kingdom", "England": "United Kingdom", "Scotland": "United Kingdom"}
    df_crm_clean = df_crm.with_columns([
        pl.col("country").replace(country_map, default=pl.col("country")).fill_null("Unknown"),
        pl.col("billing_issue").fill_null("none"),
        pl.col("signup_date").str.to_date("%Y-%m-%d"),
        pl.col("postcode").str.to_uppercase()
    ])

    ## 3. eCommerce Data
    df_ecom = pl.read_csv("data/dirty_uk_ecommerce_orders_v3.csv", null_values=["", "NA", "N/A", "null", "NULL"])
    country_code_map = {"uk": "gb", "g.b.": "gb", "gb": "gb"}
    df_ecom_clean = df_ecom.with_columns([
        pl.col("email").str.to_lowercase().str.strip_chars(),
        pl.col("country_code").str.to_lowercase().replace(country_code_map, default=pl.col("country_code")).fill_null("unknown").str.to_uppercase(),
        pl.col("order_date").str.to_date("%Y-%m-%d"),
        pl.col("vat_rate").fill_null(0.2),
        pl.col("suspected_fraud").fill_null("no").str.to_lowercase()
    ])
    
    return df_nhs_clean, df_crm_clean, df_ecom_clean

# Load data utilizing the cache
with st.spinner('Ingesting and cleaning data with Polars...'):
    df_nhs, df_crm, df_ecom = load_and_clean_data()


# --- UI Layout & Navigation ---
st.title("BigSpark Interactive EDA Dashboard")
st.markdown("This dashboard migrates our Jupyter notebook research report into an interactive data product. Visuals are powered by **DuckDB** aggregations over cached **Polars** dataframes.")

tab1, tab2, tab3 = st.tabs(["🏥 NHS Appointments", "🏢 SaaS CRM", "🛒 UK eCommerce"])

# --- TAB 1: NHS API ---
with tab1:
    st.header("NHS Appointments Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Attendance by Department")
        query = """
            SELECT appointment_type, status, COUNT(*) as count 
            FROM df_nhs 
            GROUP BY appointment_type, status 
            ORDER BY appointment_type, status
        """
        attendance_stats = duckdb.query(query).pl()
        fig = px.bar(attendance_stats, x="appointment_type", y="count", color="status", barmode="group", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Scheduling Delays vs. Patient Abandonment")
        st.markdown("""
        **What this shows:** We are looking at whether a patient is more likely to miss their appointment if the clinic is running behind schedule.
        
        Using statistical probability, we compared the average no-show rate against the no-show rate for appointments that were delayed by 30 minutes or more.
        """)
        
        # Calculate Probabilities
        total_no_shows = df_nhs.filter(pl.col("status") == "No-show").shape[0]
        p_no_show_base = total_no_shows / df_nhs.shape[0]
        
        delayed_appts = df_nhs.filter(pl.col("delay_minutes") >= 30)
        p_no_show_given_delay = delayed_appts.filter(pl.col("status") == "No-show").shape[0] / delayed_appts.shape[0] if delayed_appts.shape[0] > 0 else 0
        
        st.metric(label="Average No-Show Rate", value=f"{p_no_show_base * 100:.2f}%")
        st.metric(label="No-Show Rate (When Delayed 30+ mins)", value=f"{p_no_show_given_delay * 100:.2f}%", delta=f"{(p_no_show_given_delay - p_no_show_base) * 100:.2f}% (Increase)", delta_color="inverse")
        st.info("**Takeaway:** There is a clear link between severe scheduling delays and patients leaving without being seen. Improving clinic punctuality directly reduces the no-show rate.")


# --- TAB 2: SaaS CRM ---
with tab2:
    st.header("SaaS CRM Analysis")
    
    st.subheader("Customer Retention by Signup Month")
    st.markdown("""
    **What this shows:** Instead of looking at a single overall cancellation rate, we group customers by the month they signed up (their "cohort"). 
    This allows us to see if customers who joined recently are sticking around longer than those who joined earlier in the year, helping us measure product health over time.
    """)
    
    df_crm_cohorts = df_crm.with_columns(pl.col("signup_date").dt.strftime("%Y-%m").alias("signup_cohort"))
    query = """
        SELECT signup_cohort, COUNT(*) as total_users,
               SUM(CASE WHEN subscription_status = 'cancelled' THEN 1 ELSE 0 END) as churned_users,
               ROUND(SUM(CASE WHEN subscription_status = 'cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as cohort_churn_rate
        FROM df_crm_cohorts GROUP BY signup_cohort ORDER BY signup_cohort
    """
    cohort_analysis = duckdb.query(query).to_df()
    
    fig2 = px.bar(cohort_analysis, x="signup_cohort", y="cohort_churn_rate", text="cohort_churn_rate", template="plotly_white")
    fig2.update_traces(textposition='auto', marker_color='indianred')
    st.plotly_chart(fig2, use_container_width=True)

# --- TAB 3: eCommerce ---
with tab3:
    st.header("UK eCommerce Orders Analysis")
    
    st.subheader("Automated Outlier Detection")
    st.markdown("""
    **What this shows:** We automatically scan all orders to find transactions that are unusually high compared to the normal spending behavior for that specific country. 
    Instead of guessing a threshold (like "orders over £2000"), the system mathematically flags orders that fall far outside the average (highlighted in yellow below). This is useful for catching potential fraud or errors.
    """)
    
    df_ecom_anomalies = df_ecom.with_columns([
        pl.col("order_value").mean().over("country_code").alias("country_mean_order"),
        pl.col("order_value").std().over("country_code").alias("country_std_order")
    ]).with_columns([
        ((pl.col("order_value") - pl.col("country_mean_order")) / pl.col("country_std_order")).alias("z_score")
    ])
    
    # Checkbox for interaction
    show_only_anomalies = st.checkbox("Show Only Anomalies (Z > 2.5)")
    
    df_plot = df_ecom_anomalies.to_pandas()
    if show_only_anomalies:
        df_plot = df_plot[abs(df_plot["z_score"]) > 2.5]
    
    fig3 = px.scatter(
        df_plot, x="order_date", y="order_value", color=abs(df_plot["z_score"]) > 2.5,
        labels={"color": "Is Anomaly (Z > 2.5)"}, template="plotly_white"
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    outliers = df_ecom_anomalies.filter(pl.col("z_score").abs() > 2.5).shape[0]
    st.warning(f"Engine statistically flagged {outliers} anomalous transactions across {df_ecom.shape[0]} total orders.")
