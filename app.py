import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Configure page
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# Title
st.title("Sales Performance Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/sales_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

# Display key metrics
st.header("Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    total_revenue = df['Total'].sum()
    st.metric("Total Revenue", f"${total_revenue:,.0f}")

with col2:
    total_sales = len(df)
    st.metric("Total Sales", f"{total_sales:,}")

with col3:
    avg_sale = df['Total'].mean()
    st.metric("Average Sale", f"${avg_sale:.0f}")

st.divider()

# Visualization 1: Sales by Product
st.header("Revenue by Product")

product_revenue = df.groupby('Product')['Total'].sum().sort_values(ascending=True)

fig1, ax1 = plt.subplots(figsize=(10, 6))
sns.barplot(x=product_revenue.values, y=product_revenue.index, palette='viridis', ax=ax1)
ax1.set_xlabel('Revenue ($)')
ax1.set_ylabel('Product')
ax1.set_title('Revenue by Product')
st.pyplot(fig1)

st.divider()

# Visualization 2: Monthly Sales Trend
st.header("Monthly Sales Trend")

df['Month'] = df['Date'].dt.to_period('M').astype(str)
monthly_sales = df.groupby('Month')['Total'].sum()

fig2, ax2 = plt.subplots(figsize=(10, 6))
monthly_sales.plot(kind='line', marker='o', ax=ax2)
ax2.set_xlabel('Month')
ax2.set_ylabel('Revenue ($)')
ax2.set_title('Monthly Revenue Trend')
ax2.grid(True, alpha=0.3)
plt.xticks(rotation=45)
st.pyplot(fig2)

st.divider()

# Visualization 3: Sales by Region
st.header("Sales by Region")

region_sales = df.groupby('Region')['Total'].sum()

fig3, ax3 = plt.subplots(figsize=(8, 8))
colors = sns.color_palette('pastel')
ax3.pie(region_sales.values, labels=region_sales.index, autopct='%1.1f%%', 
        colors=colors, startangle=90)
ax3.set_title('Revenue Distribution by Region')
st.pyplot(fig3)

st.divider()

# Show raw data
st.header("Raw Data")
st.dataframe(df, use_container_width=True)