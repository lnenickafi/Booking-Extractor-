import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Booking Review Downloader", page_icon="📥")

st.title("🏨 Booking.com Review Downloader")
st.markdown("Zadejte parametry níže a stáhněte si surová data recenzí v CSV.")

# --- Vstupy v postranním panelu ---
with st.sidebar:
    st.header("🔑 Přihlášení a ID")
    api_key = st.text_input("RapidAPI Key", type="password")
    hotel_id = st.text_input("Hotel ID (např. 318615)")
    
    st.header("⚙️ Rozsah")
    max_pages = st.number_input("Kolik stránek stáhnout? (1 str. ≈ 25 recenzí)", min_value=1, max_value=200, value=10)
    st.info("Ponecháním filtrů na 'Vše' získáte kompletní dataset.")

# --- Funkce pro stahování ---
if st.button("🚀 Spustit stahování dat"):
    if not api_key or not hotel_id:
        st.error("Musíte zadat API klíč a ID hotelu.")
    else:
        url = "https://booking-com.p.rapidapi.com/v1/hotels/reviews"
        headers = {
            "x-rapidapi-host": "booking-com.p.rapidapi.com",
            "x-rapidapi-key": api_key
        }
        
        all_reviews = []
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        for page in range(int(max_pages)):
            params = {
                "hotel_id": hotel_id,
                "locale": "en-gb",
                "page_number": str(page),
                "sort_type": "SORT_MOST_RELEVANT",
                # Vynechání language_filter a customer_type zajistí u tohoto API nejširší možný odběr
            }
            
            status_msg.info(f"Stahuji stránku {page + 1} z {max_pages}...")
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                
                if response.status_code == 429:
                    st.warning("🚨 Rate limit (429). Čekám 15 sekund na uvolnění...")
                    time.sleep(15)
                    # Zkusíme stejnou stránku znovu
                    page -= 1
                    continue
                
                if response.status_code != 200:
                    st.error(f"API vrátilo chybu {response.status_code}. Končím stahování.")
                    break
                
                data = response.json()
                # U Booking API jsou data v klíči 'result'
                batch = data.get('result', [])
                
                if not batch:
                    st.success("Dosáhli jsme konce dostupných recenzí.")
                    break
                
                all_reviews.extend(batch)
                
                # Update UI
                progress = (page + 1) / max_pages
                progress_bar.progress(progress)
                
                # Malá pauza, abychom nebyli moc agresivní
                time.sleep(1.2)
                
            except Exception as e:
                st.error(f"Nastala neočekávaná chyba: {e}")
                break
        
        if all_reviews:
            # Převod na DataFrame
            df = pd.json_normalize(all_reviews)
            
            st.write(f"### ✅ Hotovo! Staženo {len(df)} recenzí.")
            
            # Zobrazení náhledu surových dat
            st.dataframe(df.head(50))
            
            # Export do CSV s podporou Excelu (utf-8-sig)
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            
            st.download_button(
                label="📥 Stáhnout surová data (CSV)",
                data=csv,
                file_name=f"booking_reviews_{hotel_id}.csv",
                mime="text/csv",
            )
        else:
            st.warning("Nebyly nalezeny žádné recenze. Zkontrolujte ID hotelu.")
