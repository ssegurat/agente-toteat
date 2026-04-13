"""Supabase client for the main Toteat AI app."""
from supabase import create_client
import streamlit as st


@st.cache_resource
def get_supabase():
    """Returns a Supabase client. Requires SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)
