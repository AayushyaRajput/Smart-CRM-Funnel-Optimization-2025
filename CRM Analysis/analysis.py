# smart_crm_gradio_2025.py

import gradio as gr
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
from datetime import datetime, timedelta

# -----------------------------------------
# MOCK DATA GENERATION
# -----------------------------------------
INDUSTRIES = ["SaaS", "E-Commerce", "Healthcare", "FinTech", "EdTech", "Manufacturing"]
SOURCES = ["Facebook Ads", "Email Campaign", "LinkedIn DMs", "Referral", "Organic", "Webinar"]

def seed(seed_val=42):
    random.seed(seed_val)
    np.random.seed(seed_val)
seed(2025)

def generate_contacts(n=1000, start_date=None):
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)
    rows = []
    for i in range(n):
        created = start_date + timedelta(days=int(np.random.exponential(scale=20)))
        source = np.random.choice(SOURCES, p=[0.35, 0.2, 0.15, 0.1, 0.15, 0.05])
        industry = np.random.choice(INDUSTRIES)
        engagement = min(100, max(0, int(20 + np.random.normal(0, 18) + (15 if source=="Email Campaign" else 0))))
        converted = np.random.rand() < (engagement / 300)
        conversion_date = created + timedelta(days=random.randint(7,45)) if converted else None
        rows.append({
            'contact_id': i,
            'name': f"Lead_{i}",
            'email': f"lead{i}@example.com",
            'company': f"Company_{random.randint(1,300)}",
            'industry': industry,
            'source': source,
            'created_at': created.date(),
            'engagement_score': engagement,
            'converted': converted,
            'conversion_date': conversion_date.date() if conversion_date else None
        })
    return pd.DataFrame(rows)

# Assign funnel stage
FUNNEL_STAGES = ['Lead', 'MQL', 'SQL', 'POC', 'Customer']
def assign_stage(row):
    s = row['engagement_score']
    if row['converted']:
        return 'Customer'
    if s >= 65:
        return 'SQL' if np.random.rand() < 0.6 else 'POC'
    if s >= 40:
        return 'MQL'
    return 'Lead'

# Nurturing templates
NURTURING_TEMPLATES = {
    'high': {
        'subject': "Quick follow-up: tailored plan for {company}",
        'body': (
            "Hi {name},\n\nThanks for taking a demo with us. "
            "Here's a case study showing how we reduced CAC for a similar {industry} company by 40%. "
            "Can I block a 15-min call to discuss a custom pilot?\n\nBest,\nFounder"
        )
    },
    'mid': {
        'subject': "Webinar recording + CAC case study",
        'body': (
            "Hi {name},\n\nThanks for attending our webinar! "
            "Here's the recording and a short case study on CAC optimization for {industry} companies. "
            "Reply if you'd like a 10-min discovery chat.\n\nCheers,\nGrowth Team"
        )
    },
    'low': {
        'subject': "Monthly LTV insights for {industry}",
        'body': (
            "Hello {name},\n\nHere's this month's newsletter with 3 quick LTV growth experiments "
            "for {industry} companies. Reply if you'd like a personalized breakdown.\n\nBest,\nFounder"
        )
    }
}

# -----------------------------------------
# ANALYTICS PREPARATION
# -----------------------------------------
def prepare_dataset(n=2000):
    df = generate_contacts(n)
    df['funnel_stage'] = df.apply(assign_stage, axis=1)
    cost_map = {
        'Facebook Ads': 90_000,
        'Email Campaign': 10_000,
        'LinkedIn DMs': 25_000,
        'Referral': 2_500,
        'Organic': 0,
        'Webinar': 5_000
    }
    agg = df.groupby('source').agg(
        leads=('contact_id','count'),
        conversions=('converted','sum'),
        avg_engagement=('engagement_score','mean')
    ).reset_index()
    agg['cost_incurred'] = agg['source'].map(cost_map)
    agg['conversion_rate'] = (agg['conversions'] / agg['leads']).fillna(0)
    agg['cost_per_conversion'] = agg.apply(lambda r: r['cost_incurred']/r['conversions'] if r['conversions']>0 else np.nan, axis=1)
    return df, agg

# -----------------------------------------
# DASHBOARD FUNCTIONS
# -----------------------------------------

def dashboard(n):
    df, agg = prepare_dataset(n)
    stage_counts = df['funnel_stage'].value_counts().reindex(FUNNEL_STAGES, fill_value=0)
    funnel_fig = go.Figure(go.Funnel(
        y=stage_counts.index.tolist(),
        x=stage_counts.values.tolist(),
        textinfo="value+percent initial"
    ))
    conversion_fig = px.bar(agg, x='source', y='conversion_rate', title='Conversion Rate by Channel')
    return funnel_fig, conversion_fig, agg

def nurturing(contact_id, intent, n):
    df, _ = prepare_dataset(n)
    lead = df[df['contact_id']==contact_id].iloc[0]
    template = NURTURING_TEMPLATES[intent]
    subject = template['subject'].format(**lead)
    body = template['body'].format(**lead)
    return subject, body

# -----------------------------------------
# GRADIO UI
# -----------------------------------------

with gr.Blocks(theme=gr.themes.Soft(), title="Smart CRM 2025") as demo:
    gr.Markdown("# 🚀 Smart CRM & Funnel Optimization — 2025")
    gr.Markdown("AI-powered CRM simulation, funnel insights, nurturing engine, and CAC optimization in one dashboard.")

    with gr.Tab("📊 Dashboard"):
        n_slider = gr.Slider(200, 5000, step=100, value=1200, label="Number of Mock Contacts")
        funnel_plot = gr.Plot()
        conversion_plot = gr.Plot()
        channel_table = gr.DataFrame(interactive=False)
        n_slider.change(dashboard, inputs=n_slider, outputs=[funnel_plot, conversion_plot, channel_table])

    with gr.Tab("📧 Nurturing Engine"):
        n_slider2 = gr.Slider(200, 5000, step=100, value=1200, label="Number of Mock Contacts")
        df, _ = prepare_dataset(1200)
        lead_dropdown = gr.Dropdown(choices=[f"{row.contact_id} | {row.name} | {row.company}" for row in df.itertuples()],
                                    label="Choose a Lead")
        intent_radio = gr.Radio(["high", "mid", "low"], value="mid", label="Intent Level")
        subject_box = gr.Textbox(label="Email Subject")
        body_box = gr.Textbox(label="Email Body", lines=10)
        generate_btn = gr.Button("Generate Nurturing Email")
        generate_btn.click(
            fn=lambda lead_info, intent, n: nurturing(int(lead_info.split('|')[0]), intent, n),
            inputs=[lead_dropdown, intent_radio, n_slider2],
            outputs=[subject_box, body_box]
        )

    with gr.Tab("📈 CAC Analytics"):
        gr.Markdown("Interactive table showing cost per conversion, conversion rates, and channel-level experiments.")
        df_view = gr.DataFrame(interactive=False)
        def analytics(n):
            _, agg = prepare_dataset(n)
            return agg
        n_slider3 = gr.Slider(200, 5000, step=100, value=1200, label="Number of Mock Contacts")
        n_slider3.change(analytics, inputs=n_slider3, outputs=df_view)

# Launch app
demo.launch()

