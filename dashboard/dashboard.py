import streamlit as st

st.subheader("Setlist Dashboard de la Iglesia Dios es Amor Mérida")

conn = st.connection("postgres", type="sql")
df = conn.query("SELECT version();")
st.dataframe(df)
