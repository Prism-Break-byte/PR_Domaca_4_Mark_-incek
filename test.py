import pandas as pd
import streamlit as st


@st.cache_data
def nalozi_podatke():
    POT_MOVIES = "https://media.githubusercontent.com/media/Prism-Break-byte/PR_Domaca_4_Mark_-incek/main/data/movies.csv"
    POT_RATINGS = "https://media.githubusercontent.com/media/Prism-Break-byte/PR_Domaca_4_Mark_-incek/main/data/ratings.csv"

    r = pd.read_csv(POT_RATINGS)
    m = pd.read_csv(POT_MOVIES)
    return r, m


ratings, movies = nalozi_podatke()

# --- 1. NALOGA (Analiza podatkov) ---
st.markdown("<h3 style='font-weight: bold;'>Naloga 1 (Analiza podatkov)</h3>", unsafe_allow_html=True)

# Izračun osnovnih statistik za filme
filmi = pd.DataFrame(
    ratings.groupby("movieId")["rating"].agg(["count", "mean", "std"]).sort_values(by="mean", ascending=False))

# --- 1. Filter: Število ocen ---
col1, col2 = st.columns([2, 3])
with col1:
    filter_st_ocen = st.checkbox("Filtriraj po številu ocen")
with col2:
    meja_za_filmi = st.number_input("Minimalno število ocen", min_value=int(filmi["count"].min()),
                                    max_value=int(filmi["count"].max()), value=100, step=100)

if filter_st_ocen:
    filmi = filmi[filmi["count"] >= meja_za_filmi]

# --- 2. Filter: Žanri ---
zanre = pd.DataFrame(movies['genres'].str.split('|').explode())
vsi_zanri = sorted(set(zanre["genres"].to_list()))

filmi = filmi.merge(movies, on="movieId")

col1, col2 = st.columns([2, 3])
with col1:
    filter_žanri = st.checkbox("Filtriraj po žanru")
with col2:
    izbrani_zanri = st.multiselect("Izberi žanre:", options=vsi_zanri, key="polenta")

if filter_žanri and izbrani_zanri:
    niz = "|".join(izbrani_zanri)
    filmi = filmi[filmi["genres"].str.contains(niz, na=False)]

# --- 3. Filter: Leto izdaje ---
filmi["leto"] = filmi["title"].str.extract(r'\((\d{4})\)').astype(float)

if 'shrani_min' not in st.session_state:
    st.session_state.shrani_min = int(filmi["leto"].min(skipna=True)) if not filmi["leto"].dropna().empty else 1900
    st.session_state.shrani_max = int(filmi["leto"].max(skipna=True)) if not filmi["leto"].dropna().empty else 2026

min_leto = st.session_state.shrani_min
max_leto = st.session_state.shrani_max

col1, col2 = st.columns([2, 3])
with col1:
    filter_leto = st.checkbox("Filtriraj po letu")
with col2:
    izbrana_leta = st.slider("Določi obdobje izdaje", min_value=min_leto, max_value=max_leto,
                             value=(min_leto, max_leto))

if filter_leto:
    filmi = filmi[(filmi["leto"] >= izbrana_leta[0]) & (filmi["leto"] <= izbrana_leta[1])]

# Urejanje tabele za prikaz
filmi = filmi.drop(columns=["genres", "movieId"])
filmi = filmi.set_index("title")

# Prikaz rezultatov
st.dataframe(filmi.drop(columns=["std"]).head(10),
             column_config={
                 "title": st.column_config.TextColumn("Film", width="large"),
                 "count": st.column_config.NumberColumn("Stevilo ocen"),
                 "mean": st.column_config.NumberColumn("Povprečna ocen", format="%.2f")
             },
             width='stretch')