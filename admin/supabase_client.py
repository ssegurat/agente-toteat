from supabase import create_client
import streamlit as st


@st.cache_resource
def get_supabase():
    url = st.secrets.get("SUPABASE_URL", "https://kdeirfyatgmnxwzccrqi.supabase.co")
    key = st.secrets.get("SUPABASE_KEY", "")
    return create_client(url, key)
