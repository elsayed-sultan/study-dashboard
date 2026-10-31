import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

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

st.title("📚 لوحة متابعة المذاكرة والنوم")
st.write("متابعة ساعات المذاكرة وساعات النوم والإحصاء الوصفي لها.")


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


df = load_data("study_data.csv")

# Sidebar
st.sidebar.header("⚙️ خيارات التصفية")

df["Month"] = df["Date"].dt.strftime("%Y-%m")

months = ["All"] + sorted(df["Month"].unique())
selected_month = st.sidebar.selectbox("اختاري الشهر", months)

subjects = ["All"] + list(df["Subject"].unique())
selected_subject = st.sidebar.selectbox("اختاري المادة", subjects)

filtered_df = df.copy()
if selected_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == selected_month]
if selected_subject != "All":
    filtered_df = filtered_df[filtered_df["Subject"] == selected_subject]

# KPIs
st.markdown("### 📊 الملخص")
col1, col2, col3, col4 = st.columns(4)

count = len(filtered_df)
total_hours = filtered_df["StudyHours"].sum()
avg_sleep = filtered_df["SleepHours"].mean() if count > 0 else 0
top_subject = (
    filtered_df.groupby("Subject")["StudyHours"].sum().idxmax() if count > 0 else "-"
)

col1.metric("عدد جلسات المذاكرة", count)
col2.metric("إجمالي ساعات المذاكرة", f"{total_hours:.1f} ساعة")
col3.metric("متوسط ساعات النوم", f"{avg_sleep:.1f} ساعة")
col4.metric("أكتر مادة مذاكرة", top_subject)

# الإحصاء الوصفي
st.markdown("---")
st.subheader("📈 الإحصاء الوصفي والتوزيعات")

if not filtered_df.empty:
    hours = filtered_df["StudyHours"]
    q1 = hours.quantile(0.25)
    q3 = hours.quantile(0.75)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🔹 النزعة المركزية (ساعات المذاكرة)")
        st.write(f"- المتوسط (Mean): {hours.mean():.2f}")
        st.write(f"- الوسيط (Median): {hours.median():.2f}")
        st.write(f"- المنوال (Mode): {hours.mode().iloc[0]}")

        st.markdown("#### 🔹 التشتت")
        st.write(f"- الانحراف المعياري (Std): {hours.std():.2f}")
        st.write(f"- المدى الربيعي (IQR): {q3 - q1:.2f}")

    with col_b:
        st.markdown("#### 🔹 مقارنة المواد")
        summary = filtered_df.groupby("Subject")["StudyHours"].agg(["count", "mean", "median", "std"])
        st.dataframe(summary.round(2))

    # Insight للإحصاء
    if hours.mean() > hours.median() * 1.1:
        st.info(
            f"💡 Insight: متوسط الجلسة ({hours.mean():.1f} ساعة) أكبر من الوسيط ({hours.median():.1f} ساعة) "
            "بفرق واضح، يعني فيه جلسات طويلة جداً بتشد المتوسط لفوق، والوسيط أصدق في تمثيل الجلسة العادية."
        )
    else:
        st.info(
            f"💡 Insight: المتوسط ({hours.mean():.1f}) والوسيط ({hours.median():.1f}) قريبين من بعض، "
            "يعني جلسات المذاكرة متوازنة ومفيش جلسات طويلة بتشد المتوسط."
        )

    # Histogram + Boxplot
    st.markdown("#### 📉 التوزيع والـ Outliers")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(data=filtered_df, x="StudyHours", kde=True, bins=10, ax=axes[0], color="#3A7CA5")
    axes[0].set_title("Study Hours Distribution")
    sns.boxplot(data=filtered_df, x="Subject", y="StudyHours", ax=axes[1], color="#A9CCE3")
    axes[1].set_title("Boxplot by Subject")
    plt.tight_layout()
    st.pyplot(fig)

    subj_median = filtered_df.groupby("Subject")["StudyHours"].median()
    if hours.skew() > 0.5:
        shape_txt = "أغلب الجلسات قصيرة وفيه ذيل طويل ناحية الجلسات الطويلة."
    else:
        shape_txt = "توزيع طول الجلسات متماثل تقريباً من غير ذيل واضح."
    st.info(
        f"💡 Insight: {shape_txt} "
        f"وأعلى وسيط للجلسة كان لمادة {subj_median.idxmax()} ({subj_median.max():.1f} ساعة)."
    )

    # 1) جلسات المذاكرة الشاذة (Outliers) بقاعدة IQR
    st.markdown("#### 🚨 جلسات المذاكرة الشاذة (Outliers)")
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = filtered_df[(hours < lower) | (hours > upper)]
    st.write(f"الحدود الطبيعية: من {lower:.1f} إلى {upper:.1f} ساعة، وعدد الجلسات الشاذة: {len(outliers)}")
    if not outliers.empty:
        st.dataframe(outliers[["Date", "Subject", "StudyHours"]])
        share = len(outliers) / len(filtered_df) * 100
        st.info(
            f"💡 Insight: عدد الجلسات الشاذة {len(outliers)} ({share:.1f}% من الجلسات)، "
            f"وأطولهم {outliers['StudyHours'].max():.1f} ساعة. "
            "الـ IQR بيتحسب على الفلتر الحالي، فاختاري مادة واحدة عشان الحدود تبقى أدق."
        )
    else:
        st.info("💡 Insight: مفيش جلسات شاذة في الفلتر الحالي.")

    # بيانات يومية (مجموع المذاكرة ومتوسط النوم لكل يوم)
    daily = filtered_df.groupby("Date").agg(
        Study=("StudyHours", "sum"), Sleep=("SleepHours", "mean")
    )

    # 2) ساعات المذاكرة اليومية
    st.markdown("#### 📅 ساعات المذاكرة اليومية")
    st.line_chart(daily["Study"])
    st.info(
        f"💡 Insight: أكتر يوم مذاكرة كان {daily['Study'].idxmax().strftime('%Y-%m-%d')} "
        f"بمجموع {daily['Study'].max():.1f} ساعة، ومتوسط المذاكرة اليومية {daily['Study'].mean():.1f} ساعة."
    )

    # 3) إجمالي ساعات كل مادة
    st.markdown("#### 🗂️ إجمالي ساعات كل مادة")
    subj_total = filtered_df.groupby("Subject")["StudyHours"].sum()
    st.bar_chart(subj_total)
    top_share = subj_total.max() / subj_total.sum() * 100
    st.info(
        f"💡 Insight: مادة {subj_total.idxmax()} أخدت أكتر وقت بإجمالي "
        f"{subj_total.max():.1f} ساعة ({top_share:.1f}% من وقت المذاكرة)."
    )

    # 4) نسبة كل مادة (Pie)
    st.markdown("#### 🥧 نسبة كل مادة من وقت المذاكرة")
    pie_colors = ["#3A7CA5", "#A9CCE3", "#2F6690", "#81C3D7", "#D9E8F2"]
    fig2, ax2 = plt.subplots(figsize=(5, 5))
    ax2.pie(
        subj_total,
        labels=subj_total.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=pie_colors[:len(subj_total)],
    )
    st.pyplot(fig2)
    st.info(
        f"💡 Insight: أقل مادة وقتاً هي {subj_total.idxmin()} "
        f"({subj_total.min() / subj_total.sum() * 100:.1f}% من وقت المذاكرة)."
    )

    # 5) إجمالي كل شهر
    st.markdown("#### 📆 إجمالي ساعات كل شهر")
    month_total = filtered_df.groupby("Month")["StudyHours"].sum()
    st.bar_chart(month_total)
    if len(month_total) > 1:
        st.info(
            f"💡 Insight: أكتر شهر مذاكرة هو {month_total.idxmax()} ({month_total.max():.1f} ساعة)."
        )

    # 6) النوم مقابل المذاكرة (Scatter)
    st.markdown("#### 😴 النوم مقابل المذاكرة (كل نقطة يوم)")
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.scatter(daily["Sleep"], daily["Study"], color="#3A7CA5", alpha=0.7)
    ax3.set_xlabel("Sleep Hours")
    ax3.set_ylabel("Study Hours (daily total)")
    plt.tight_layout()
    st.pyplot(fig3)

    if len(daily) >= 3:
        corr = daily["Sleep"].corr(daily["Study"])
        if pd.isna(corr) or abs(corr) < 0.2:
            corr_txt = "مفيش علاقة واضحة بين ساعات النوم وساعات المذاكرة في اليوم."
        elif corr > 0:
            corr_txt = "كل ما ساعات النوم زادت، ساعات المذاكرة بتميل تزيد (علاقة طردية)."
        else:
            corr_txt = "كل ما ساعات النوم قلّت، ساعات المذاكرة بتميل تزيد (علاقة عكسية)."
        low_sleep = daily[daily["Sleep"] < 5]
        st.info(
            f"💡 Insight: معامل الارتباط ({corr:.2f}). {corr_txt} "
            f"وعدد الأيام اللي نومها أقل من 5 ساعات: {len(low_sleep)}. "
            "الارتباط مش معناه إن واحد سبب التاني."
        )

else:
    st.warning("لا توجد بيانات للفلتر الحالي.")

st.markdown("---")
if st.checkbox("📋 عرض السجل التفصيلي"):
    st.dataframe(filtered_df)
