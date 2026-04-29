import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Booking.com Review Downloader", layout="wide")

st.title("🏨 Booking.com Review Extractor")
st.markdown("Stáhněte si všechny recenze z libovolného hotelu do CSV.")

# --- SIDEBAR: Vstupy od uživatele ---
with st.sidebar:
    st.header("Konfigurace")
    api_key = st.text_input("Vložte svůj RapidAPI Key", type="password")
    hotel_id = st.text_input("Vložte ID hotelu (např. 318615)")
    max_pages = st.number_input("Maximální počet stránek (1 str. = cca 25 recenzí)", min_value=1, max_value=100, value=20)
    
    st.info("Tip: API klíč najdete na rapidapi.com u Booking.com API.")

# --- HLAVNÍ LOGIKA ---
if st.button("🚀 Spustit stahování"):
    if not api_key or not hotel_id:
        st.error("Prosím vyplňte API klíč i ID hotelu.")
    else:
        url = "https://booking-com.p.rapidapi.com/v1/hotels/reviews"
        headers = {
            "x-rapidapi-host": "booking-com.p.rapidapi.com",
            "x-rapidapi-key": api_key
        }
        
        all_reviews = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for page in range(int(max_pages)):
            params = {
                "sort_type": "SORT_MOST_RELEVANT",
                "hotel_id": hotel_id,
                "locale": "en-gb",
                "language_filter": "en-gb,de,fr,cs,es,it,ru", # Přidejte další dle potřeby, nebo 'all'
                "page_number": str(page),
                "customer_type": "solo_traveller,review_category_group_of_friends,couple,family_with_children,business_traveller" # Všichni
            }
            
            status_text.text(f"Stahuji stránku {page + 1}...")
            
            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 429:
                    st.warning("🚨 Rate limit dosažen. Čekám 10 sekund...")
                    time.sleep(10)
                    continue
                
                if response.status_code != 200:
                    st.error(f"Chyba API: {response.status_code}")
                    break
                
                data = response.json()
                results = data.get('result', [])
                
                if not results:
                    st.success("Dosáhli jsme konce všech dostupných recenzí.")
                    break
                
                all_reviews.extend(results)
                
                # Aktualizace UI
                progress = (page + 1) / max_pages
                progress_bar.progress(progress)
                
                # Pauza proti blokaci
                time.sleep(1.5)
                
            except Exception as e:
                st.error(f"Nastala chyba: {e}")
                break
        
        if all_reviews:
            df = pd.json_normalize(all_reviews)
            
            # Základní čištění
            st.write(f"✅ Staženo celkem {len(df)} recenzí.")
            
            # Zobrazení náhledu
            st.dataframe(df.head(10))
            
            # Export do CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Stáhnout kompletní CSV",
                data=csv,
                file_name=f"reviews_hotel_{hotel_id}.csv",
                mime="text/csv",
            )
        else:
            st.warning("Nebyly nalezeny žádné recenze.")
