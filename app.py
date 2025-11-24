import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import math
# J'ajoute cette ligne pour gérer les images
from PIL import Image 

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Chope ton Bat", page_icon="🦇", layout="centered")

# Style CSS pour faire "App Mobile"
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

# --- EN-TÊTE AVEC LOGO ---
# Je crée deux colonnes : une petite pour le logo, une grande pour le titre
col_logo, col_title = st.columns([1, 4]) # Le [1, 4] définit la largeur relative

with col_logo:
   
    try:
        image = Image.open("hades.png") 
        st.image(image, width=500) # ajuster la taille ici
    except FileNotFoundError:
        st.error("Image non trouvée. Vérifie le nom du fichier.")

with col_title:
    # Le titre s'affiche à côté de l'image
    st.title("Chope ton Bat")

st.markdown("### Système de Triangulation Tactique")

# --- FONCTIONS ---
def get_coords(address):
    geolocator = Nominatim(user_agent="triangulation_app")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except:
        return None

def trilateration(p1, r1, p2, r2, p3, r3):
    # Conversion simple et robuste
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

# --- INTERFACE ---
col1, col2 = st.columns([3, 1])
addr1 = col1.text_input("Adresse 1", placeholder="Ex: Tour Eiffel, Paris")
dist1 = col2.number_input("Dist 1 (km)", min_value=0.0, format="%.2f")

col3, col4 = st.columns([3, 1])
addr2 = col3.text_input("Adresse 2")
dist2 = col4.number_input("Dist 2 (km)", min_value=0.0, format="%.2f")

col5, col6 = st.columns([3, 1])
addr3 = col5.text_input("Adresse 3")
dist3 = col6.number_input("Dist 3 (km)", min_value=0.0, format="%.2f")

if st.button("LANCER LA TRIANGULATION"):
    if addr1 and addr2 and addr3 and dist1 > 0 and dist2 > 0 and dist3 > 0:
        with st.spinner('Calcul des coordonnées...'):
            c1 = get_coords(addr1)
            c2 = get_coords(addr2)
            c3 = get_coords(addr3)

            if c1 and c2 and c3:
                result = trilateration(c1, dist1, c2, dist2, c3, dist3)
                
                st.success(f"📍 Cible localisée : {result[0]:.5f}, {result[1]:.5f}")
                
                # Affichage Carte
                m = folium.Map(location=result, zoom_start=13)
                
                # Cercles
                folium.Circle(c1, radius=dist1*1000, color="green", fill=True, fill_opacity=0.1).add_to(m)
                folium.Circle(c2, radius=dist2*1000, color="green", fill=True, fill_opacity=0.1).add_to(m)
                folium.Circle(c3, radius=dist3*1000, color="green", fill=True, fill_opacity=0.1).add_to(m)
                
                # Marqueurs
                folium.Marker(c1, tooltip="Point 1").add_to(m)
                folium.Marker(c2, tooltip="Point 2").add_to(m)
                folium.Marker(c3, tooltip="Point 3").add_to(m)
                folium.Marker(result, icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)

                st_folium(m, width=700)
            else:
                st.error("Impossible de trouver une des adresses.")
    else:

        st.warning("Veuillez remplir tous les champs.")

