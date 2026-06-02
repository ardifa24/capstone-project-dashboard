import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import Counter

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CarPathMu Dashboard",
    page_icon="💼",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("job_posting_clean.csv")

df_raw = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filter")
    st.markdown("---")

    selected_years = st.multiselect(
        "Tahun",
        options=sorted(df_raw["year"].unique().tolist()),
        default=sorted(df_raw["year"].unique().tolist()),
    )
    selected_educations = st.multiselect(
        "Pendidikan",
        options=sorted(df_raw["education_required"].unique().tolist()),
        default=sorted(df_raw["education_required"].unique().tolist()),
    )
    selected_exp = st.multiselect(
        "Level Pengalaman",
        options=["Entry (0-2 yrs)", "Mid (3-5 yrs)", "Senior (6-9 yrs)", "Lead (10-15 yrs)", "Executive (15+ yrs)"],
        default=["Entry (0-2 yrs)", "Mid (3-5 yrs)", "Senior (6-9 yrs)", "Lead (10-15 yrs)", "Executive (15+ yrs)"],
    )
    st.markdown("---")

# ── Filter dataframe ──────────────────────────────────────────────────────────
df = df_raw[
    df_raw["year"].isin(selected_years)
    & df_raw["education_required"].isin(selected_educations)
    & df_raw["experience_level"].isin(selected_exp)
].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Career Path Dashboard")
st.caption("Eksplorasi tren karir masa depanmu!")
st.markdown("---")

# ── KPI Scorecards ────────────────────────────────────────────────────────────
n = len(df)
avg_salary = df["salary_midpoint"].mean() if n > 0 else 0
pct_remote = (df["work_type"] == "Remote").sum() / n * 100 if n > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Rata-rata Gaji",  f"{avg_salary:,.0f} USD")
c2.metric("Total Pekerjaan",  f"{n:,}")
c3.metric("% Remote Jobs",   f"{pct_remote:.1f}%")

st.markdown("---")

# ── Color palette & shared layout ─────────────────────────────────────────────
NAVY      = "#0f2a4a"
BLUE_MID  = "#7ab3e0"
TEAL_DARK = "#1a6b5a"
TEAL_MID  = "#4ecfaf"
ORANGE    = "#e8824a"

BASE = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="sans-serif", size=12, color="#333"),
    margin=dict(l=20, r=60, t=40, b=20),
)

def apply_axis_colors(fig):
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#e8e8e8",
        title_font=dict(color="#000000"),
        tickfont=dict(color="#000000"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#e8e8e8",
        title_font=dict(color="#000000"),
        tickfont=dict(color="#000000"),
    )
    return fig

# ── Pre-compute skill data ────────────────────────────────────────────────────
@st.cache_data
def compute_skills(data_json):
    d = pd.read_json(data_json, orient="split")
    freq, salary_rows = [], []
    for _, row in d.iterrows():
        if pd.isna(row["skills_required"]):
            continue
        for s in row["skills_required"].split("|"):
            s = s.strip()
            freq.append(s)
            salary_rows.append({"skill": s, "salary": row["salary_midpoint"]})
    return freq, salary_rows

all_skills, skill_salary = compute_skills(df.to_json(orient="split"))

# ═════════════════════════════════════════════════════════════════════════════
# BARIS 1 — Tren rata-rata salary: Tech vs Non-Tech
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Tren rata-rata salary: Tech vs Non-Tech")

TECH_JOB_TITLES = [
    'Backend Developer', 'Cloud Architect', 'Software Engineer',
    'Senior Software Engineer', 'Data Engineer', 'Frontend Developer',
    'Cybersecurity Analyst', 'Machine Learning Engineer', 'UX Designer',
    'Data Analyst', 'Data Scientist', 'Research Scientist', 'DevOps Engineer'
]

# ✅ BENAR — pakai df yang sudah difilter sidebar
df_plot = df.copy()
df_plot["Tipe"] = df_plot["job_title"].apply(
    lambda x: "Tech" if x in TECH_JOB_TITLES else "Non-Tech"
)

trend = (
    df_plot
    .groupby(["year", "Tipe"])["salary_midpoint"]
    .mean()
    .reset_index()
)

fig1 = go.Figure()
for label, color in [("Non-Tech", BLUE_MID), ("Tech", ORANGE)]:
    sub = trend[trend["Tipe"] == label]
    fig1.add_trace(go.Scatter(
        x=sub["year"], y=sub["salary_midpoint"],
        mode="lines+markers", name=label,
        line=dict(color=color, width=2),
        marker=dict(size=7),
    ))


fig1.update_layout(
    **BASE,
    xaxis_title="Tahun",
    yaxis_title="Rata-rata Salary (USD)",
    yaxis_tickformat=",.0f",
    legend=dict(x=0.98, y=0.05, xanchor="right", yanchor="bottom",
                font=dict(color="#000000", size=12), bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#e8e8e8", borderwidth=1,
                ),
    height=380)
apply_axis_colors(fig1)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# BARIS 2 — Top 5 Job Title berdasarkan gaji
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Top 5 job title — rata-rata salary tertinggi")

top5_title = (
    df.groupby("job_title")["salary_midpoint"]
    .mean()
    .sort_values(ascending=True)
    .tail(5)
    .reset_index()
)
top5_title.columns = ["job_title", "avg_salary"]

fig2 = go.Figure(go.Bar(
    x=top5_title["avg_salary"],
    y=top5_title["job_title"],
    orientation="h",
    marker_color=[TEAL_MID] * (len(top5_title) - 1) + [TEAL_DARK],
    text=top5_title["avg_salary"].apply(lambda x: f"{x:,.0f}"),
    textposition="outside",
))
# fig2
fig2.update_layout(
    **BASE, 
    xaxis_title="Rata-rata Salary (USD)",
    xaxis_tickformat=",.0f",
    xaxis_range=[0, top5_title["avg_salary"].max() * 1.15],
    height=380)
apply_axis_colors(fig2)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# BARIS 3 — Top 5 Industri berdasarkan gaji
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Top 5 industri — rata-rata gaji tertinggi")

top5_ind = (
    df.groupby("industry")["salary_midpoint"]
    .mean()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)
top5_ind.columns = ["industry", "avg_salary"]

fig3 = go.Figure(go.Bar(
    x=top5_ind["industry"],
    y=top5_ind["avg_salary"],
    marker_color=[NAVY] + [BLUE_MID] * (len(top5_ind) - 1),
    text=top5_ind["avg_salary"].apply(lambda x: f"{x:,.0f}"),
    textposition="outside",
))
# fig3
fig3.update_layout(
    **BASE,
    xaxis_title="Industri",
    yaxis_title="Rata-rata Salary (USD)",
    yaxis_tickformat=",.0f",
    yaxis_range=[top5_ind["avg_salary"].min() * 0.997, top5_ind["avg_salary"].max() * 1.005],
    height=380)
apply_axis_colors(fig3)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# BARIS 4 — Top 10 Keahlian dengan frekuensi permintaan tertinggi
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Top 10 keahlian dengan frekuensi permintaan tertinggi")

skill_freq = pd.DataFrame(Counter(all_skills).most_common(10), columns=["skill", "count"])

fig4 = go.Figure(go.Bar(
    x=skill_freq["skill"],
    y=skill_freq["count"],
    marker_color=[NAVY] + [BLUE_MID] * (len(skill_freq) - 1),
    text=skill_freq["count"].apply(lambda x: f"{x:,}"),
    textposition="outside",
))
# fig4
fig4.update_layout(
    **BASE,
    xaxis_title="Keahlian",
    yaxis_title="Frekuensi kemunculan",
    yaxis_range=[0, skill_freq["count"].max() * 1.15], height=380)
apply_axis_colors(fig4)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# BARIS 5 — Top 10 Skill dengan rata-rata salary tertinggi
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Top 10 skill dengan rata-rata salary tertinggi")

skill_sal_df = pd.DataFrame(skill_salary)
skill_sal_agg = (
    skill_sal_df.groupby("skill")
    .agg(avg_salary=("salary", "mean"), count=("salary", "count"))
    .reset_index()
)
top10_skill_sal = (
    skill_sal_agg[skill_sal_agg["count"] >= 50]
    .sort_values("avg_salary", ascending=True)
    .tail(10)
)

fig5 = go.Figure(go.Bar(
    x=top10_skill_sal["avg_salary"],
    y=top10_skill_sal["skill"],
    orientation="h",
    marker_color=[TEAL_MID] * (len(top10_skill_sal) - 1) + [TEAL_DARK],
    text=top10_skill_sal["avg_salary"].apply(lambda x: f"{x:,.0f}"),
    textposition="outside",
))
# fig5
fig5.update_layout(
    **BASE,
    xaxis_title="Rata-rata Salary (USD)",
    xaxis_tickformat=",.0f",
    xaxis_range=[0, top10_skill_sal["avg_salary"].max() * 1.15], height=420)
apply_axis_colors(fig5)
st.plotly_chart(fig5, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("© 2026 Capstone Team Carpathmu")