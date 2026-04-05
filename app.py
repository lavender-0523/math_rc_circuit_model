import streamlit as st
import numpy as np
import pandas as pd
from scipy.integrate import odeint

# Set up the page layout and title
st.set_page_config(page_title="RC Circuit Model", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS injected for Premium Aesthetics ---
st.markdown("""
<style>
    /* Dark Mode Glassmorphism Theme */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        background-attachment: fixed;
        color: #f0f0f0;
    }
    
    /* Center and Style Main Headers */
    h1 {
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        text-align: center;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem !important;
        padding-top: 1rem;
        text-shadow: 0px 4px 15px rgba(0, 201, 255, 0.4);
    }
    
    h2, h3 {
        color: #92FE9D !important;
        font-weight: 600 !important;
    }

    /* Glassmorphism containers */
    .glass-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease;
    }
    .glass-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0, 201, 255, 0.2);
    }

    /* Style the sidebar elements */
    [data-testid="stSidebar"] {
        background: rgba(15, 32, 39, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        color: #00C9FF !important;
        font-size: 2.5rem !important;
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        color: #e0e0e0 !important;
        font-size: 1.1rem !important;
    }
    
    /* Custom insight box */
    .insight-box {
        background: linear-gradient(120deg, rgba(0, 201, 255, 0.15), rgba(146, 254, 157, 0.15));
        border-left: 6px solid #00C9FF;
        padding: 20px 25px;
        border-radius: 12px;
        color: #ffffff;
        font-size: 1.15rem;
        letter-spacing: 0.5px;
        line-height: 1.6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    /* Ensure chart block looks cool */
    .chart-box {
        background: rgba(0,0,0,0.25); 
        padding: 1.5rem; 
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Smart RC Circuit Dashboard")
st.markdown("<p style='text-align: center; color: #b0bec5; font-size: 1.2rem; margin-bottom: 3rem;'>Dynamic computation and visual analysis of first-order differential equations.</p>", unsafe_allow_html=True)

st.sidebar.markdown("## 🎛️ Circuit Parameters")
st.sidebar.markdown("<p style='color: #b0bec5; margin-bottom: 1rem;'>Adjust properties to see real-time ODE shifts.</p>", unsafe_allow_html=True)

# Interactive sliders
R = st.sidebar.slider("Resistance, R (Ohms)", min_value=10, max_value=10000, value=1000, step=10)
C_uF = st.sidebar.slider("Capacitance, C (microFarads)", min_value=1, max_value=1000, value=100, step=1)
V_s = st.sidebar.slider("Source Voltage, Vs (Volts)", min_value=1.0, max_value=24.0, value=5.0, step=0.5)

# Convert Capacitance from microFarads to Farads for calculation
C = C_uF * 1e-6

# Calculate Time Constant (tau)
tau = R * C

# Top Metrics Row for nice UX
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Resistance (R)", value=f"{R} Ω")
with col2:
    st.metric(label="Capacitance (C)", value=f"{C_uF} µF")
with col3:
    st.metric(label="Source Voltage", value=f"{V_s} V")
with col4:
    st.metric(label="Time Constant (τ)", value=f"{tau:.4f} s", delta="Rate of Charge", delta_color="normal")

st.markdown("<hr style='border:1px solid rgba(255,255,255,0.1); margin: 2rem 0;'>", unsafe_allow_html=True)

# Layout for Theory vs Simulation
left_col, right_col = st.columns([1, 2.2], gap="large")

with left_col:
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.markdown("### 🧮 The Mathematics")
    st.markdown("<p style='color: #CFD8DC;'>We model the charging RC circuit using the standard first-order ODE:</p>", unsafe_allow_html=True)
    st.latex(r"R \frac{dq}{dt} + \frac{q}{C} = V(t)")
    st.markdown("<br><p style='color: #CFD8DC;'>Since charge $q = C \\cdot V_c$, substituting this gives:</p>", unsafe_allow_html=True)
    st.latex(r"RC \frac{dV_c}{dt} + V_c = V_s")
    st.markdown("<br><p style='color: #CFD8DC;'>The <b>analytical solution</b> (starting at 0V) evaluates to:</p>", unsafe_allow_html=True)
    st.latex(r"V_c(t) = V_s \left(1 - e^{-\frac{t}{RC}}\right)")
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    # Time vector for simulation
    t_max = st.sidebar.slider("Simulation Time (seconds)", min_value=max(0.1, float(tau)), max_value=float(10*max(0.01, tau)), value=float(5*max(0.01, tau)), step=float(max(0.01, tau))/10)
    t = np.linspace(0, t_max, 500)

    # 1. Analytical Solution
    V_c_analytical = V_s * (1 - np.exp(-t / tau))

    # 2. ODE Solver (Computational Analysis)
    def rc_ode_system(V_c, t, V_s, R, C):
        return (V_s - V_c) / (R * C)

    V_c_initial = 0.0
    V_c_numerical = odeint(rc_ode_system, V_c_initial, t, args=(V_s, R, C)).flatten()

    # Prepare data for beautiful rendering
    df = pd.DataFrame({
        'Time (s)': t,
        'Mathematical (Analytical)': V_c_analytical,
        'Computational (ODE Solved)': V_c_numerical
    })
    df = df.set_index('Time (s)')

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 📈 Capacitor Voltage Over Time")
    st.line_chart(df, color=["#00C9FF", "#92FE9D"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div class="insight-box">
<b>✨ AI & Compute Insight:</b> We aren't just plotting a standard mathematical equation! Streamlit calculates the green curve dynamically by solving the differential equation numerically step-by-step using Python. When the physical math equation and the computational ODE engine yield the exact same overlapping curves, it proves the validity of computational analysis in Engineering & Physics!
</div>
""", unsafe_allow_html=True)
