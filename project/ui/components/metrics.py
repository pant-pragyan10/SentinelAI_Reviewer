import streamlit as st


def metric_card(column, label: str, value, delta: str = None):
    with column:
        st.metric(label, value, delta)
