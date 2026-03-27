import streamlit as st
import pandas as pd
import google.generativeai as genai
from pptx import Presentation
from io import StringIO

st.set_page_config(page_title="AdStrategix AI", layout="wide")

# ================= LOGIN =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "1234":
            st.session_state.logged_in = True
            st.success("Login successful")
        else:
            st.error("Invalid login")

    st.stop()

# ================= GEMINI =================
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)

def generate_ai(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)
        return res.text
    except:
        return "⚠️ Add valid API key"

# ================= FUNCTIONS =================

def detect_platform(df):
    cols = [c.lower() for c in df.columns]

    if any("ad group" in c for c in cols):
        return "Google Ads"
    elif any("adset" in c for c in cols):
        return "Meta Ads"
    elif any("line item" in c for c in cols):
        return "DV360"
    return "Unknown"

def create_ppt(brand, industry, results):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = f"{brand} Media Plan"
    slide.placeholders[1].text = industry

    for r in results:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = r["Platform"]
        slide.placeholders[1].text = f"Conv: {r['Conversions']} | CPA: {r['CPA']}"

    prs.save("plan.pptx")

# ================= UI =================
st.title("🚀 AdStrategix AI")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Planner", "📈 Analyzer", "🧾 Ad Preview", "💾 Saved"
])

# =====================================================
# TAB 1
# =====================================================
with tab1:

    brand = st.text_input("Brand")
    industry = st.selectbox("Industry", ["Real Estate", "SaaS", "Ecommerce"])
    country = st.selectbox("Country", ["India", "USA", "UK"])
    budget = st.number_input("Budget", min_value=1000)
    objective = st.selectbox("Objective", ["Leads", "Sales"])

    benchmarks = {
        "India": {"cpm": 250, "ctr": 1.2, "cvr": 3},
        "USA": {"cpm": 20, "ctr": 2, "cvr": 4},
        "UK": {"cpm": 18, "ctr": 1.8, "cvr": 3.5}
    }

    if st.button("Generate Plan"):

        data = benchmarks[country]
        results = []

        platforms = {
            "Google": 0.4,
            "Meta": 0.35,
            "LinkedIn": 0.15,
            "Programmatic": 0.1
        }

        for p, split in platforms.items():
            b = budget * split
            imp = (b / data["cpm"]) * 1000
            clk = imp * (data["ctr"] / 100)
            conv = clk * (data["cvr"] / 100)
            cpa = b / conv if conv else 0

            st.metric(p, f"{int(conv)} conv")

            results.append({
                "Platform": p,
                "Conversions": int(conv),
                "CPA": round(cpa, 2)
            })

        # AI Persona
        st.subheader("👤 Persona")
        st.write(generate_ai(f"Buyer persona for {industry} in {country}"))

        # Ads
        st.subheader("📝 Ads")
        st.write(generate_ai(f"Ad copies for {brand} in {industry}"))

        # Keywords
        st.subheader("🔍 Keywords")

        prompt = f"""
        Generate Google Ads keywords CSV for {industry} in {country}
        """

        kw = generate_ai(prompt)
        st.code(kw)

        st.download_button("Download CSV", kw, "keywords.csv")

        # Budget Optimizer
        st.subheader("🧠 Budget Optimization")
        st.write(generate_ai(f"Optimize budget for {industry} with {budget}"))

        # Save
        if "plans" not in st.session_state:
            st.session_state.plans = []

        st.session_state.plans.append({
            "brand": brand,
            "results": results
        })

        # PPT
        if st.button("Download PPT"):
            create_ppt(brand, industry, results)
            with open("plan.pptx", "rb") as f:
                st.download_button("Download", f, "plan.pptx")

# =====================================================
# TAB 2
# =====================================================
with tab2:

    file = st.file_uploader("Upload CSV")

    if file:
        df = pd.read_csv(file)
        st.dataframe(df.head())

        platform = detect_platform(df)
        st.success(f"Detected: {platform}")

        st.bar_chart(df.select_dtypes(include='number'))

        st.subheader("💬 Custom AI")

        prompt = st.text_area("Ask anything")

        if st.button("Run AI"):
            sample = df.head(20).to_string()
            st.write(generate_ai(prompt + sample))

# =====================================================
# TAB 3
# =====================================================
with tab3:

    code = st.text_area("Ad Tag")

    if st.button("Preview"):
        st.components.v1.html(code, height=400)

# =====================================================
# TAB 4
# =====================================================
with tab4:

    if "plans" in st.session_state:
        for p in st.session_state.plans:
            st.write(p["brand"])
            st.dataframe(pd.DataFrame(p["results"]))
