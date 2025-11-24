import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import math
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Chope ton Bat", page_icon="🦇", layout="centered")

# Style CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        height: 3em;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTION DE LA MÉMOIRE (SESSION STATE) ---
if 'resultat' not in st.session_state:
    st.session_state.resultat = None
if 'coords_points' not in st.session_state:
    st.session_state.coords_points = None
if 'marge_erreur' not in st.session_state:
    st.session_state.marge_erreur = 1.0

# --- EN-TÊTE ---
col_logo, col_title = st.columns([1, 4])

with col_logo:
    try:
        image = Image.open("hades.png") 
        st.image(image, width=100)
    except FileNotFoundError:
        st.warning("Logo?")

with col_title:
    st.title("Chope ton Bat")

st.markdown("### Système de Triangulation Tactique")

# --- FONCTIONS ---
def get_coords(address):
    geolocator = Nominatim(user_agent="triangulation_app_hades_v2")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except:
        return None

def trilateration(p1, r1, p2, r2, p3, r3):
    # Conversion degrés -> radians / XYZ
    def latlon_to_xyz(lat, lon):
        lat, lon = math.radians(lat), math.radians(lon)
        R = 6371
        x = R * math.cos(lat) * math.cos(lon)
        y = R * math.cos(lat) * math.sin(lon)
        z = R * math.sin(lat)
        return x, y, z

    def xyz_to_latlon(x, y, z):
        R = math.sqrt(x**2 + y**2 + z**2)
        lat = math.asin(z / R)
        lon = math.atan2(y, x)
        return math.degrees(lat), math.degrees(lon)

    P1 = latlon_to_xyz(*p1)
    P2 = latlon_to_xyz(*p2)
    P3 = latlon_to_xyz(*p3)

    # Pondération simple : plus le cercle est petit, plus il est précis (?)
    # Ici on garde une pondération équilibrée inverse à la distance
    weights = [1/r1, 1/r2, 1/r3]
    total_weight = sum(weights)
    
    x = (P1[0]*weights[0] + P2[0]*weights[1] + P3[0]*weights[2]) / total_weight
    y = (P1[1]*weights[0] + P2[1]*weights[1] + P3[1]*weights[2]) / total_weight
    z = (P1[2]*weights[0] + P2[2]*weights[1] + P3[2]*weights[2]) / total_weight

    return xyz_to_latlon(x, y, z)

# --- FORMULAIRE ---
# Ajout du slider pour la marge d'erreur
st.markdown("#### Paramètres")
marge = st.slider("Marge d'erreur / Précision (km)", 0.1, 5.0, 1.0, 0.1, help="Définit la largeur de la zone de recherche autour de la distance indiquée.")

col1, col2 = st.columns([3, 1])
addr1 = col1.text_input("Adresse 1", placeholder="Ex: Tour Eiffel, Paris")
dist1 = col2.number_input("Dist 1 (km)", min_value=0.1, format="%.2f")

col3, col4 = st.columns([3, 1])
addr2 = col3.text_input("Adresse 2")
dist2 = col4.number_input("Dist 2 (km)", min_value=0.1, format="%.2f")

col5, col6 = st.columns([3, 1])
addr3 = col5.text_input("Adresse 3")
dist3 = col6.number_input("Dist 3 (km)", min_value=0.1, format="%.2f")

# --- ACTION ---
if st.button("LANCER LA TRIANGULATION"):
    if addr1 and addr2 and addr3 and dist1 > 0 and dist2 > 0 and dist3 > 0:
        with st.spinner('Calcul des coordonnées...'):
            c1 = get_coords(addr1)
            c2 = get_coords(addr2)
            c3 = get_coords(addr3)

            if c1 and c2 and c3:
                final_pos = trilateration(c1, dist1, c2, dist2, c3, dist3)
                
                # Mise à jour session
                st.session_state.resultat = final_pos
                st.session_state.marge_erreur = marge
                st.session_state.coords_points = [
                    (c1, dist1),
                    (c2, dist2),
                    (c3, dist3)
                ]
            else:
                st.error("Une adresse est introuvable.")
    else:
        st.warning("Remplissez tout.")

# --- AFFICHAGE CARTE ---
if st.session_state.resultat is not None:
    res = st.session_state.resultat
    points = st.session_state.coords_points
    marge_actuelle = st.session_state.marge_erreur
    
    st.success(f"📍 Zone estimée centrée sur : {res[0]:.5f}, {res[1]:.5f}")
    
    m = folium.Map(location=res, zoom_start=12)
    
    # Affichage des "Bandes" de recherche
    for i, (pt, dist) in enumerate(points):
        # Cercle MIN (Distance - marge)
        r_min = max(0, dist - marge_actuelle) * 1000
        folium.Circle(pt, radius=r_min, color="green", weight=1, fill=False, opacity=0.5, dash_array='5, 5').add_to(m)
        
        # Cercle MAX (Distance + marge)
        r_max = (dist + marge_actuelle) * 1000
        folium.Circle(pt, radius=r_max, color="green", weight=1, fill=False, opacity=0.5, dash_array='5, 5').add_to(m)

        # Cercle EXACT (Ligne pleine)
        folium.Circle(pt, radius=dist*1000, color="blue", weight=2, fill=False).add_to(m)
        
        folium.Marker(pt, tooltip=f"Point {i+1}", icon=folium.Icon(color="blue", icon="map-marker")).add_to(m)
    
    # CIBLE ESTIMÉE (Zone rouge)
    # On dessine un cercle rouge de la taille de la marge d'erreur autour du point calculé
    folium.Circle(
        res, 
        radius=marge_actuelle*1000, 
        color="red", 
        fill=True, 
        fill_opacity=0.3, 
        popup="Zone Probable"
    ).add_to(m)
    
    folium.Marker(res, icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)

    st_folium(m, width=700)