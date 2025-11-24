import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
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
# C'est ici qu'on empêche la carte de disparaître
if 'resultat' not in st.session_state:
    st.session_state.resultat = None
if 'coords_points' not in st.session_state:
    st.session_state.coords_points = None

# --- EN-TÊTE ---
col_logo, col_title = st.columns([1, 4])

with col_logo:
    try:
        # Assure-toi que le nom de l'image est exact sur GitHub (majuscules/minuscules)
        image = Image.open("image_0.png") 
        st.image(image, width=100)
    except FileNotFoundError:
        st.warning("Logo introuvable")

with col_title:
    st.title("Chope ton Bat")

st.markdown("### Système de Triangulation Tactique")

# --- FONCTIONS ---
def get_coords(address):
    geolocator = Nominatim(user_agent="triangulation_app_hades")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except:
        return None

def trilateration(p1, r1, p2, r2, p3, r3):
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

    weights = [1/r1, 1/r2, 1/r3]
    total_weight = sum(weights)
    
    x = (P1[0]*weights[0] + P2[0]*weights[1] + P3[0]*weights[2]) / total_weight
    y = (P1[1]*weights[0] + P2[1]*weights[1] + P3[1]*weights[2]) / total_weight
    z = (P1[2]*weights[0] + P2[2]*weights[1] + P3[2]*weights[2]) / total_weight

    return xyz_to_latlon(x, y, z)

# --- FORMULAIRE ---
col1, col2 = st.columns([3, 1])
addr1 = col1.text_input("Adresse 1", placeholder="Ex: Tour Eiffel, Paris")
dist1 = col2.number_input("Dist 1 (km)", min_value=0.0, format="%.2f")

col3, col4 = st.columns([3, 1])
addr2 = col3.text_input("Adresse 2")
dist2 = col4.number_input("Dist 2 (km)", min_value=0.0, format="%.2f")

col5, col6 = st.columns([3, 1])
addr3 = col5.text_input("Adresse 3")
dist3 = col6.number_input("Dist 3 (km)", min_value=0.0, format="%.2f")

# --- ACTION ---
if st.button("LANCER LA TRIANGULATION"):
    if addr1 and addr2 and addr3 and dist1 > 0 and dist2 > 0 and dist3 > 0:
        with st.spinner('Calcul des coordonnées...'):
            c1 = get_coords(addr1)
            c2 = get_coords(addr2)
            c3 = get_coords(addr3)

            if c1 and c2 and c3:
                # Calcul
                final_pos = trilateration(c1, dist1, c2, dist2, c3, dist3)
                
                # ON SAUVEGARDE TOUT DANS LA MÉMOIRE DE SESSION
                st.session_state.resultat = final_pos
                st.session_state.coords_points = [
                    (c1, dist1),
                    (c2, dist2),
                    (c3, dist3)
                ]
            else:
                st.error("Impossible de trouver une des adresses.")
    else:
        st.warning("Veuillez remplir tous les champs.")

# --- AFFICHAGE DU RÉSULTAT (En dehors du bouton !) ---
# Si un résultat existe en mémoire, on l'affiche, même si la page recharge.
if st.session_state.resultat is not None:
    res = st.session_state.resultat
    points = st.session_state.coords_points
    
    st.success(f"📍 Cible localisée : {res[0]:.5f}, {res[1]:.5f}")
    
    # Création de la carte
    m = folium.Map(location=res, zoom_start=13)
    
    # Ajout des éléments
    # Points et cercles
    for i, (pt, dist) in enumerate(points):
        folium.Circle(pt, radius=dist*1000, color="green", fill=True, fill_opacity=0.1).add_to(m)
        folium.Marker(pt, tooltip=f"Point {i+1}").add_to(m)
    
    # Cible
    folium.Marker(res, icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)

    # Affichage final stable
    st_folium(m, width=700)