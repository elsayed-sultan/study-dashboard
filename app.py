import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Study & Sleep Dashboard", page_icon="📚", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');

html, body, [class*="css"], h1, h2, h3, h4, p {
    font-family: 'Amiri', serif;
}

[data-testid="stMetric"] {
    background-color: #E3EEF7;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
</style>
""", unsafe_allow_html=True)

BLUE = "#3A7CA5"

st.title("📚 لوحة متابعة المذاكرة والنوم")
st.write("متابعة ساعات المذاكرة وساعات النوم والإحصاء الوصفي لها.")


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


df = load_data("study_data.csv")
df["Month"] = df["Date"].dt.strftime("%Y-%m")

# ---------------- Sidebar ----------------
st.sidebar.header("⚙️ خيارات التصفية")

months = ["All"] + sorted(df["Month"].unique())
selected_month = st.sidebar.selectbox("اختاري الشهر", months)

subjects = ["All"] + list(df["Subject"].unique())
selected_subject = st.sidebar.selectbox("اختاري المادة", subjects)

filtered_df = df.copy()
if selected_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == selected_month]
if selected_subject != "All":
    filtered_df = filtered_df[filtered_df["Subject"] == selected_subject]



# ---------------- لو مفيش بيانات ----------------
if filtered_df.empty:
    st.warning("لا توجد بيانات للفلتر الحالي.")
    st.stop()

# ---------------- KPIs ----------------
count = len(filtered_df)
total_hours = filtered_df["StudyHours"].sum()
avg_sleep = filtered_df["SleepHours"].mean()
top_subject = filtered_df.groupby("Subject")["StudyHours"].sum().idxmax()

col1, col2, col3, col4 = st.columns(4)
col1.metric("عدد جلسات المذاكرة", count)
col2.metric("إجمالي ساعات المذاكرة", f"{total_hours:.1f} ساعة")
col3.metric("متوسط ساعات النوم", f"{avg_sleep:.1f} ساعة")
col4.metric("أكتر مادة مذاكرة", top_subject)

# ---------------- تجميع على مستوى اليوم ----------------
daily = (
    filtered_df.groupby("Date")
    .agg(Study=("StudyHours", "sum"), Sleep=("SleepHours", "mean"))
    .sort_index()
    .reset_index()
)

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 الملخص", "📉 التوزيعات", "😴 النوم", "🗂️ المواد"])

# ===== 1) الملخص =====
with tab1:
    hours = filtered_df["StudyHours"]
    q1, q3 = hours.quantile(0.25), hours.quantile(0.75)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🔹 النزعة المركزية (ساعات المذاكرة)")
        st.write(f"- المتوسط (Mean): {hours.mean():.2f}")
        st.write(f"- الوسيط (Median): {hours.median():.2f}")
        st.write(f"- المنوال (Mode): {hours.mode().iloc[0]}")
    with col_b:
        st.markdown("#### 🔹 التشتت")
        st.write(f"- الانحراف المعياري (Std): {hours.std():.2f}")
        st.write(f"- المدى الربيعي (IQR): {q3 - q1:.2f}")

    st.markdown("#### 📅 ساعات المذاكرة اليومية")
    fig = px.line(daily, x="Date", y="Study", markers=True,
                  labels={"Date": "التاريخ", "Study": "ساعات المذاكرة"})
    fig.update_traces(line_color=BLUE)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("عرض الجدول"):
        st.dataframe(filtered_df.drop(columns="Month"), use_container_width=True)

# ===== 2) التوزيعات =====
with tab2:
    st.markdown("#### 📉 التوزيع والـ Outliers")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(filtered_df, x="StudyHours", nbins=10,
                           title="Study Hours Distribution",
                           color_discrete_sequence=[BLUE])
        fig.update_layout(bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.box(filtered_df, x="Subject", y="StudyHours",
                     title="Boxplot by Subject",
                     color_discrete_sequence=["#A9CCE3"])
        st.plotly_chart(fig, use_container_width=True)

# ===== 3) النوم =====
with tab3:
    st.markdown("#### 🌙 ساعات النوم اليومية")
    fig = px.line(daily, x="Date", y="Sleep", markers=True,
                  labels={"Date": "التاريخ", "Sleep": "ساعات النوم"})
    fig.update_traces(line_color="#2F6690")
    st.plotly_chart(fig, use_container_width=True)

# ===== 4) المواد =====
with tab4:
    subj_total = filtered_df.groupby("Subject")["StudyHours"].sum().reset_index()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🗂️ إجمالي ساعات كل مادة")
        fig = px.bar(subj_total, x="Subject", y="StudyHours",
                     labels={"Subject": "المادة", "StudyHours": "الساعات"},
                     color_discrete_sequence=[BLUE])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### 🥧 نسبة كل مادة من وقت المذاكرة")
        fig = px.pie(subj_total, names="Subject", values="StudyHours",
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📆 إجمالي ساعات كل شهر")
    month_total = filtered_df.groupby("Month")["StudyHours"].sum().reset_index()
    fig = px.bar(month_total, x="Month", y="StudyHours",
                 labels={"Month": "الشهر", "StudyHours": "الساعات"},
                 color_discrete_sequence=[BLUE])
    st.plotly_chart(fig, use_container_width=True)



