import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Color palette ─────────────────────────────────────────────────────────────
COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52",
          "#8172B2", "#937860", "#DA8BC3", "#8C8C8C"]
ACCENT = "#4C72B0"

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("sales_data.csv", parse_dates=["Date"])
    df.dropna(subset=["Region"], inplace=True)
    df["Month"]   = df["Date"].dt.to_period("M").astype(str)
    df["MonthDT"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    return df

df = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

regions = ["All"] + sorted(df["Region"].unique().tolist())
sel_region = st.sidebar.selectbox("Region", regions)

sel_product = st.sidebar.multiselect(
    "Product(s)", sorted(df["Product"].unique().tolist()),
    default=sorted(df["Product"].unique().tolist())
)

date_min, date_max = df["Date"].min().date(), df["Date"].max().date()
sel_dates = st.sidebar.date_input(
    "Date range", value=(date_min, date_max),
    min_value=date_min, max_value=date_max
)

# ── Apply filters ─────────────────────────────────────────────────────────────
filt = df.copy()
if sel_region != "All":
    filt = filt[filt["Region"] == sel_region]
if sel_product:
    filt = filt[filt["Product"].isin(sel_product)]
if len(sel_dates) == 2:
    filt = filt[(filt["Date"].dt.date >= sel_dates[0]) &
                (filt["Date"].dt.date <= sel_dates[1])]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Sales Performance Dashboard")
st.caption(
    f"Showing **{len(filt):,}** transactions · "
    f"{filt['Date'].min().date() if len(filt) else '–'}  →  "
    f"{filt['Date'].max().date() if len(filt) else '–'}"
)
st.divider()

# ── KPI cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Total Revenue",   f"${filt['Total'].sum():,.0f}")
k2.metric("🛒 Transactions",    f"{len(filt):,}")
k3.metric("📦 Units Sold",      f"{filt['Quantity'].sum():,}")
k4.metric("📈 Avg Order Value",
          f"${filt['Total'].mean():.2f}" if len(filt) else "$0.00")

st.divider()

# ── Helper ────────────────────────────────────────────────────────────────────
def make_fig(w=7, h=4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    return fig, ax

# ─────────────────────────────────────────────────────────────────────────────
# Row 1 — Product Performance  |  Regional Distribution
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

# ── Product bar chart ─────────────────────────────────────────────────────────
with col_left:
    st.subheader("🏆 Product Performance")
    metric_choice = st.radio("Compare by", ["Revenue", "Units"],
                             horizontal=True, key="prod_metric")

    by_product = (
        filt.groupby("Product")
            .agg(Revenue=("Total", "sum"), Units=("Quantity", "sum"))
            .sort_values(metric_choice, ascending=False)
            .reset_index()
    )

    fig, ax = make_fig(7, 4)
    bars = ax.bar(by_product["Product"], by_product[metric_choice],
                  color=COLORS[:len(by_product)],
                  edgecolor="white", linewidth=0.6)

    for bar in bars:
        h = bar.get_height()
        label = f"${h:,.0f}" if metric_choice == "Revenue" else f"{h:,.0f}"
        ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
                label, ha="center", va="bottom", fontsize=8, color="#333333")

    ax.set_ylabel("Revenue ($)" if metric_choice == "Revenue"
                  else "Units Sold", fontsize=9)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda x, _: f"${x:,.0f}" if metric_choice == "Revenue"
            else f"{x:,.0f}"
        )
    )
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ── Regional donut chart ──────────────────────────────────────────────────────
with col_right:
    st.subheader("🌍 Regional Distribution")
    by_region = (
        filt.groupby("Region")["Total"]
            .sum()
            .reset_index()
            .rename(columns={"Total": "Revenue"})
    )

    fig, ax = make_fig(5, 4)
    wedges, texts, autotexts = ax.pie(
        by_region["Revenue"],
        labels=by_region["Region"],
        autopct="%1.1f%%",
        colors=COLORS[:len(by_region)],
        startangle=140,
        wedgeprops=dict(width=0.55, edgecolor="white"),
        pctdistance=0.75,
    )
    for t in autotexts:
        t.set_fontsize(8)
    for t in texts:
        t.set_fontsize(9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Row 2 — Monthly Sales Trend
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📅 Monthly Sales Trend")

by_month = (
    filt.groupby(["MonthDT", "Month"])
        .agg(Revenue=("Total", "sum"), Transactions=("SaleID", "count"))
        .reset_index()
        .sort_values("MonthDT")
)

trend_metric = st.radio("Show monthly", ["Revenue", "Transactions"],
                         horizontal=True, key="trend_metric")

fig, ax = make_fig(12, 4)
x = range(len(by_month))
ax.plot(x, by_month[trend_metric],
        color=ACCENT, linewidth=2.5, marker="o", markersize=6,
        markerfacecolor="white", markeredgewidth=2)
ax.fill_between(x, by_month[trend_metric], alpha=0.12, color=ACCENT)

ax.set_xticks(x)
ax.set_xticklabels(by_month["Month"], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Revenue ($)" if trend_metric == "Revenue"
              else "Transactions", fontsize=9)
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(
        lambda x, _: f"${x:,.0f}" if trend_metric == "Revenue"
        else f"{x:,.0f}"
    )
)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Row 3 — Heatmap  |  Top 10 Transactions
# ─────────────────────────────────────────────────────────────────────────────
col_heat, col_tbl = st.columns([2, 1])

# ── Revenue heatmap ───────────────────────────────────────────────────────────
with col_heat:
    st.subheader("🔥 Revenue Heatmap: Product × Region")
    pivot = (
        filt.groupby(["Product", "Region"])["Total"]
            .sum()
            .unstack(fill_value=0)
    )

    fig, ax = make_fig(7, 4)
    im = ax.imshow(pivot.values, cmap="Blues", aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=9)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)

    max_val = pivot.values.max() if pivot.values.max() > 0 else 1
    for r in range(pivot.shape[0]):
        for c in range(pivot.shape[1]):
            val = pivot.values[r, c]
            text_color = "white" if val > max_val * 0.6 else "#333333"
            ax.text(c, r, f"${val:,.0f}",
                    ha="center", va="center",
                    fontsize=7.5, color=text_color)

    plt.colorbar(im, ax=ax,
                 format=mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ── Top 10 table ──────────────────────────────────────────────────────────────
with col_tbl:
    st.subheader("📋 Top 10 Transactions")
    top10 = (
        filt.nlargest(10, "Total")[
            ["Date", "Product", "Region", "Quantity", "Total"]
        ]
        .assign(
            Date=lambda d: d["Date"].dt.strftime("%b %d"),
            Total=lambda d: d["Total"].map("${:,.0f}".format),
        )
        .reset_index(drop=True)
    )
    top10.index += 1
    st.dataframe(top10, use_container_width=True, height=360)

st.divider()

# ── Raw data expander ─────────────────────────────────────────────────────────
with st.expander("🗂 View raw data"):
    st.dataframe(
        filt.drop(columns=["MonthDT", "Month"])
            .sort_values("Date", ascending=False)
            .reset_index(drop=True),
        use_container_width=True,
        height=400,
    )
    st.download_button(
        "⬇️ Download filtered data as CSV",
        data=filt.drop(columns=["MonthDT", "Month"]).to_csv(index=False),
        file_name="filtered_sales.csv",
        mime="text/csv",
    )