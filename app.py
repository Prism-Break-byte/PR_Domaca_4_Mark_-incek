import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import os
from sklearn.linear_model import Lasso

@st.cache_data
def nalozi_podatke():
    r = pd.read_csv("data/ratings.csv")
    m = pd.read_csv("data/movies.csv")
    return r, m

@st.cache_data
def pripravi_matriko(ratings_df, movies_df):
    veljavni_filmi = pd.DataFrame(ratings_df.groupby("movieId")["rating"].count())
    veljavni_filmi = veljavni_filmi[veljavni_filmi["rating"] >= 10000]

    veljvni_ocenjevalci = pd.DataFrame(ratings_df.groupby("userId")["rating"].count())
    veljvni_ocenjevalci = veljvni_ocenjevalci[veljvni_ocenjevalci["rating"] >= 3000]

    veljavni_filmi_list = veljavni_filmi.index.to_list() 
    veljvni_ocenjevalci_list = veljvni_ocenjevalci.index.to_list() 

    tab_podatkov = ratings_df[ratings_df["movieId"].isin(veljavni_filmi_list) & ratings_df["userId"].isin(veljvni_ocenjevalci_list)]

    tab_podatkov = tab_podatkov.pivot(index='movieId', columns='userId', values='rating')
    tab_podatkov = movies_df.merge(tab_podatkov, on ="movieId")

    tab_podatkov = tab_podatkov.drop(columns=['movieId', 'genres'])
    matrika = tab_podatkov.set_index("title").fillna(0)
    
    return matrika

ratings, movies = nalozi_podatke()

#1 Naloga
st.markdown("<h3 style='font-weight: bold;'>Naloga 1 (Analiza podatkov)</h3>", unsafe_allow_html=True)
filmi = pd.DataFrame(ratings.groupby("movieId")["rating"].agg(["count", "mean", "std"]).sort_values(by="mean", ascending=False))

#---Sortiranje po stevilu ocen---
col1, col2 = st.columns([2, 3])

with col1:
    filter_st_ocen = st.checkbox("Filtriraj po številu ocen")

with col2:
    meja_za_filmi = st.number_input("Minimalno število ocen", min_value=int(filmi["count"].min()), max_value=int(filmi["count"].max()), value=100, step=100)

if filter_st_ocen:
    filmi = filmi[filmi["count"] >= meja_za_filmi]


#---Sortiranje po žanri filma---
zanre = pd.DataFrame(movies['genres'].str.split('|').explode())
seznam = zanre["genres"].to_list()
vsi_zanri = sorted(set(seznam))

filmi = filmi.merge(movies, on="movieId")

col1, col2 = st.columns([2, 3])
with col1:
    filter_žanri = st.checkbox("Filtriraj po žanru")

with col2:
    izbrani_zanri = st.multiselect("Izberi žanre:", options=vsi_zanri, key="polenta")

#odločil sem se da filtriram tako da je ALI, sepravi če uproabnik izbere "Children" in "Animation" bo algoritem podal vse filme ki so ALI animirani ALI namenjni za otroke
if filter_žanri:
    niz = "|".join(izbrani_zanri)
    filmi = filmi[filmi["genres"].str.contains(niz)]

#---Sortiranje po letu izdaje filma---
filmi["leto"] = filmi["title"].str.extract(r'\((\d{4})\)').astype(float)
if 'shrani_min' not in st.session_state:
    st.session_state.shrani_min = int(filmi["leto"].min(skipna=True))
    st.session_state.shrani_max = int(filmi["leto"].max(skipna=True))

min_leto = st.session_state.shrani_min
max_leto = st.session_state.shrani_max

col1, col2 = st.columns([2, 3])
with col1:
    filter_leto = st.checkbox("Filtriraj po letu")

with col2:
    izbrana_leta = st.slider("Določi obdobje izdaje", min_value=min_leto, max_value=max_leto, value=(min_leto, max_leto))

if filter_leto:
    filmi = filmi[(filmi["leto"] >= izbrana_leta[0]) & (filmi["leto"] <= izbrana_leta[1])]

filmi = filmi.drop(columns=["genres", "movieId"])
filmi = filmi.set_index("title")

st.dataframe(filmi.drop(columns=["std"]).head(10), 
             column_config={
                 "title": st.column_config.TextColumn("Film", width="large"), 
                 "count": st.column_config.NumberColumn("Stevilo ocen"), 
                 "mean": st.column_config.NumberColumn("Povprečna ocen", format="%.2f")
             },
             use_container_width=True)

st.divider()

#2 Naloga
pogoj_1 = False
pogoj_2 = False

st.markdown("<h3 style='font-weight: bold;'>Naloga 2 (Primerjava dveh filmov)</h3>", unsafe_allow_html=True)
seznam_filmov = filmi.index.to_list()
meje_stolpcev = [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75, 5.25]

film_1 = st.selectbox("Izberi 1. film:", options=seznam_filmov, index=None)

if film_1 is not None:
    st.dataframe(filmi[filmi.index == film_1],
                column_config={
                    "title": st.column_config.TextColumn("Film", width="medium"), 
                    "count": st.column_config.NumberColumn("Stevilo ocen"), 
                    "mean": st.column_config.NumberColumn("Povprečna ocen", format="%.2f"),
                    "std": st.column_config.NumberColumn("Standardni odklon", format="%.2f")
                })

    #Histrogram
    id_filma_1 = movies[movies["title"] == film_1]["movieId"].values[0]
    ocene = ratings[ratings["movieId"] == id_filma_1]["rating"]

    fig, ax = plt.subplots()
    sns.histplot(ocene, color='skyblue', bins=meje_stolpcev, ax=ax)

    plt.xlabel("Ocena")
    plt.ylabel("Število ocen")
    ax.set_xticks([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])

    plt.title(f"Porazdelitev vseh ocen")

    st.pyplot(fig)
    seznam_filmov.remove(film_1)

    #število ocen na leto
    ocene = ratings[ratings["movieId"] == id_filma_1].copy()
    ocene["leto"] = pd.to_datetime(ocene["timestamp"], unit="s").dt.year
    backup = ocene

    ocene = ocene.groupby("leto")["rating"].count().reset_index()

    fig, ax = plt.subplots()
    plt.bar(ocene["leto"], ocene["rating"])

    plt.xlabel("Leto")
    plt.ylabel("Število ocen")
    plt.title(f"Število prejetih ocen po letih")

    plt.xticks(ocene["leto"].astype(int), rotation=90)
    
    if len(ocene) == 1:
        temp = int(ocene["rating"])
        st.write(f"Film je ocenjen samo v enem letu, ni smiseln graf zato je tukaj celotno število ocen {temp}")
        pogoj_1 = True
    else:
        st.pyplot(fig)
    
    #Graf povprečne letne ocene
    backup = backup.groupby("leto")["rating"].mean().reset_index()

    fig, ax = plt.subplots()

    plt.plot(backup["leto"], backup["rating"], marker='o', linestyle='-', linewidth=2)

    plt.xlabel("Leto")
    plt.ylabel("Povprečen rating")
    plt.title("Gibanje povprečne ocene skozi leta")
    
    plt.xticks(backup["leto"].astype(int), rotation=90) #Naredimo tako da bodo leta int števila ne pa double/float + rotation 90 če je film star
    plt.ylim(backup["rating"].min() - 0.1, backup["rating"].max() + 0.1) # Da se bo bolje videlo, nastavimo min.vrednost grafa na najnižjo povprečno oceno filma v letih - 0.1 in max.vrednost grafa na najvišjo povprečno oceno filma v letih + 0.1
    plt.grid(True, linestyle='--', alpha=0.7) #Grid za lepši izged

    if pogoj_1:
        ocene_mesec = ratings[ratings["movieId"] == id_filma_1].copy()
        ocene_mesec["mesec"] = pd.to_datetime(ocene_mesec["timestamp"], unit="s").dt.month

        ocene_mesec_povp = ocene_mesec.groupby("mesec")["rating"].mean().reset_index()

        fig2, ax2 = plt.subplots()
        ax2.plot(ocene_mesec_povp["mesec"], ocene_mesec_povp["rating"], marker='o', linestyle='-', linewidth=2)

        ax2.set_xlabel("Mesec")
        ax2.set_ylabel("Povprečen rating")
        ax2.set_title("Gibanje povprečne ocene skozi mesece v letu izida")
        
        ax2.set_xticks(ocene_mesec_povp["mesec"].astype(int))
        
        if ocene_mesec_povp["rating"].min() != ocene_mesec_povp["rating"].max():
            ax2.set_ylim(ocene_mesec_povp["rating"].min() - 0.1, ocene_mesec_povp["rating"].max() + 0.1)
        
        ax2.grid(True, linestyle='--', alpha=0.7)

        st.pyplot(fig2)
    
    else:
        st.pyplot(fig)

    film_2 = st.selectbox("Izberi 2. film:", options=seznam_filmov, index=None)

    if film_2 is not None:
        st.dataframe(filmi[filmi.index == film_2],
                    column_config={
                        "title": st.column_config.TextColumn("Film", width="medium"), 
                        "count": st.column_config.NumberColumn("Stevilo ocen"), 
                        "mean": st.column_config.NumberColumn("Povprečna ocen", format="%.2f"),
                        "std": st.column_config.NumberColumn("Standardni odklon", format="%.2f")
                    })

        id_filma_2 = movies[movies["title"] == film_2]["movieId"].values[0]
        ocene = ratings[ratings["movieId"] == id_filma_2]["rating"]


        #Historgram 
        fig, ax = plt.subplots()
        sns.histplot(ocene, color='skyblue', bins=meje_stolpcev, ax=ax)

        plt.xlabel("Ocena")
        plt.ylabel("Število ocen")
        ax.set_xticks([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])

        plt.title(f"Porazdelitev vseh ocen")

        st.pyplot(fig)

        #število ocen na leto
        ocene = ratings[ratings["movieId"] == id_filma_2].copy()
        ocene["leto"] = pd.to_datetime(ocene["timestamp"], unit="s").dt.year
        backup = ocene

        ocene = ocene.groupby("leto")["rating"].count().reset_index()

        fig, ax = plt.subplots()
        plt.bar(ocene["leto"], ocene["rating"])

        plt.xlabel("Leto")
        plt.ylabel("Število ocen")
        plt.title(f"Število prejetih ocen po letih")
        plt.xticks(ocene["leto"].astype(int), rotation=90)

        if len(ocene) == 1:
            temp = int(ocene["rating"])
            st.write(f"Film je ocenjen samo v enem letu, ni smiseln graf zato je tukaj celotno število ocen {temp}")
            pogoj_2 = True
        
        else:
            st.pyplot(fig)

        #Graf povprečne letne ocene
        backup = backup.groupby("leto")["rating"].mean().reset_index()

        fig, ax = plt.subplots()

        plt.plot(backup["leto"], backup["rating"], marker='o', linestyle='-', linewidth=2)

        plt.xlabel("Leto")
        plt.ylabel("Povprečen rating")
        plt.title("Gibanje povprečne ocene skozi leta")

        plt.xticks(backup["leto"].astype(int), rotation=90)
        plt.ylim(backup["rating"].min() - 0.1, backup["rating"].max() + 0.1)
        plt.grid(True, linestyle='--', alpha=0.7)


        if pogoj_2:
            ocene_mesec = ratings[ratings["movieId"] == id_filma_2].copy()
            ocene_mesec["mesec"] = pd.to_datetime(ocene_mesec["timestamp"], unit="s").dt.month

            ocene_mesec_povp = ocene_mesec.groupby("mesec")["rating"].mean().reset_index()

            fig2, ax2 = plt.subplots()
            ax2.plot(ocene_mesec_povp["mesec"], ocene_mesec_povp["rating"], marker='o', linestyle='-', linewidth=2)

            ax2.set_xlabel("Mesec")
            ax2.set_ylabel("Povprečen rating")
            ax2.set_title("Gibanje povprečne ocene skozi mesece v letu izida")
            
            ax2.set_xticks(ocene_mesec_povp["mesec"].astype(int))
            
            if ocene_mesec_povp["rating"].min() != ocene_mesec_povp["rating"].max():
                ax2.set_ylim(ocene_mesec_povp["rating"].min() - 0.1, ocene_mesec_povp["rating"].max() + 0.1)
            
            ax2.grid(True, linestyle='--', alpha=0.7)

            st.pyplot(fig2)
    
        else:
            st.pyplot(fig)

st.divider()

#3 Naloga
def naredi_datoteke():
    if not os.path.exists("uporabniki.csv"):
        pd.DataFrame(columns=["uporabnik", "geslo"]).to_csv("uporabniki.csv", index=False)

    if not os.path.exists("ocene_uporabnika.csv"):
        pd.DataFrame(columns=["uporabnik", "film", "ocena"]).to_csv("ocene_uporabnika.csv", index=False)

naredi_datoteke()


if "prijavljen" not in st.session_state:
    st.session_state["prijavljen"] = False

st.sidebar.title("Prijava")

if not st.session_state["prijavljen"]:
    izbira = st.sidebar.selectbox("Izberi:", ["Prijava", "Registracija"])
    uporabniki = pd.read_csv("uporabniki.csv")

    # Uporabimo formo v sidebar-u, da se stran ne osvežuje med tipkanjem imena in gesla
    with st.sidebar.form("forma_prijava"):
        reg_ime = st.text_input("Uporabniško ime")
        reg_geslo = st.text_input("Geslo", type="password")
        gumb_potrdi = st.form_submit_button("Potrdi")

    if gumb_potrdi:
        if izbira == "Registracija":
            if reg_ime in uporabniki["uporabnik"].astype(str).values:
                st.sidebar.error("Uporabnik že obstaja")

            elif reg_ime == "" or reg_geslo == "":
                st.sidebar.error("Izpolni vsa polja")

            else:
                nov_upoabnik = pd.DataFrame([[reg_ime, reg_geslo]], columns=["uporabnik", "geslo"])
                nov_upoabnik.to_csv("uporabniki.csv", mode='a', header=False, index=False)
                st.sidebar.success("Uspešno ustvarjen uporabnik! Zdaj preklopi na prijavo.")

        elif izbira == "Prijava":
            uspeh = ((uporabniki["uporabnik"].astype(str) == reg_ime) & 
                     (uporabniki["geslo"].astype(str) == reg_geslo)).any()
            
            if uspeh:
                st.session_state["prijavljen"] = True
                st.session_state["trenutni_u"] = reg_ime
                st.rerun()
                
            else:
                st.sidebar.error("Napačno ime ali geslo")

else:
    st.sidebar.write(f"Prijavljen kot: **{st.session_state.get('trenutni_u', 'Uporabnik')}**")
    if st.sidebar.button("Odjava"):
        st.session_state["prijavljen"] = False
        st.session_state["trenutni_u"] = None
        st.rerun()

st.markdown("<h3 style='font-weight: bold;'>Naloga 3 (Priporočilni sistem)</h3>", unsafe_allow_html=True)

if st.session_state["prijavljen"]:
    vse_ocene_iz_datoteke = pd.read_csv("ocene_uporabnika.csv")

    #DODAJANJE OCENE
    # Uporabimo formo tudi tukaj, da ne "laga" celotna stran ob vsaki izbiri v selectboxu
    with st.form("forma_dodaj_oceno"):
        col1, col2 = st.columns([2, 1])

        with col1:
            film = st.selectbox("Kateri film bi ocenil", options=seznam_filmov, index=None)

        with col2:
            izbrana_ocena = st.select_slider("Izberi svojo oceno", options=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], value=3.0)
        
        oddaj_oceno_gumb = st.form_submit_button("Oddaj oceno", use_container_width=True)
    
    prijavljen_uporabnik = st.session_state.get('trenutni_u', 'Uporabnik')
    ocene_uporabnika = pd.read_csv("ocene_uporabnika.csv")
    ocene_uporabnika = ocene_uporabnika[ocene_uporabnika["uporabnik"] == prijavljen_uporabnik]
    ze_ocenjeni_filmi = ocene_uporabnika["film"].to_list()

    if oddaj_oceno_gumb:
        if film == None:
            st.error("Prosim izberi film")

        else:
            if film in ze_ocenjeni_filmi:
                st.error("Ta film ste ze ocenili prosim izberite drugega")

            else:
                nova_ocena = pd.DataFrame([[prijavljen_uporabnik, film, izbrana_ocena]], columns=["uporabnik", "film", "ocena"])
                nova_ocena.to_csv("ocene_uporabnika.csv", mode='a', header=False, index=False)
                st.success("Uspešno ocenjen film.")
                st.rerun()

    st.write("")
    st.write("")
    
    #BRISANJE OCENE
    col3, col4 = st.columns([2, 1])
    with col3:
        brisi_film = st.selectbox("Izberi film za izbris", options=ze_ocenjeni_filmi, index=None, key="select_brisi")
    
    with col4:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        gumb_brisi = st.button("Briši oceno", type="primary", use_container_width=True)

    if gumb_brisi:
        if brisi_film is None:
            st.warning("Izberi film, ki ga želiš odstraniti.")
        
        else:
            # LOGIKA BRISANJA --> Obdržimo vse vrstice, razen tiste, ki ustreza uporabniku IN izbranemu filmu
            nova_tabela = vse_ocene_iz_datoteke[~((vse_ocene_iz_datoteke["uporabnik"] == prijavljen_uporabnik) & (vse_ocene_iz_datoteke["film"] == brisi_film))]
            nova_tabela.to_csv("ocene_uporabnika.csv", index=False)
            st.success(f"Ocena za {brisi_film} izbrisana.")
            st.rerun()
  
    st.write("")
    st.write("")

    st.markdown("<h4 style='font-weight: bold;'>Vaši ocenjni filmi</h4>", unsafe_allow_html=True)
    if not ocene_uporabnika.empty:
        st.dataframe(ocene_uporabnika[["film", "ocena"]], use_container_width=True, hide_index=True)
    else:
        st.info("Niste še ocenili nobenega filma.")

    st.write("")
    st.write("")

    st.markdown("<h4 style='font-weight: bold;'>Filmi ki vam bi mora bili všeč</h4>", unsafe_allow_html=True)
    #st.write(len(ocene_uporabnika))
    if len(ocene_uporabnika) < 10:
        st.markdown("Če želiš pridobiti priporočila za naslednje filme, <span style='color: red; font-size: 20px; font-weight: bold;'>moraš oceniti vsaj 10 filmov!</span>", unsafe_allow_html=True)
    
    else:
        # Dodamo gumb za dejanski izračun, da ne obremenjujemo strani ob vsakem premiku miške
        if st.button("Generiraj priporočila"):
            matrika_osnova = pripravi_matriko(ratings, movies)
            matrika = matrika_osnova.copy()
            
            model = Lasso(alpha=0.05)
            matrika["Moje_ocene"] = 0.0

            for _, vrsta in ocene_uporabnika.iterrows():
                film_naslov = vrsta['film']
                if film_naslov in matrika.index:
                    matrika.at[film_naslov, "Moje_ocene"] = vrsta['ocena']
            
            y_train = matrika["Moje_ocene"][matrika["Moje_ocene"] > 0] #Filmi ki sem jih ocenil
            x_train = matrika.drop(columns=["Moje_ocene"]).loc[y_train.index] #Ocene drugih uporabnikov za filme, ki si jih ti ocenil
            x_neocenjeni = matrika.drop(columns=["Moje_ocene"]).loc[matrika["Moje_ocene"] == 0] #Filmi ki jih nisem ocenil

            model.fit(x_train, y_train)
            napoved = model.predict(x_neocenjeni)

            priporocila = pd.DataFrame(napoved, index=x_neocenjeni.index, columns=['Predvidena ocena'])
            priporocila = priporocila.sort_values(by='Predvidena ocena', ascending=False).head(10)

            st.table(priporocila)
        
else:
    st.markdown("Če želiš oceniti filme, se moraš <span style='color: red; font-size: 20px; font-weight: bold;'>prijaviti!</span>", unsafe_allow_html=True)