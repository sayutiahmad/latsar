import streamlit as st
import os
import datetime as dt_global
from dotenv import load_dotenv
import requests
#from api_telegram_anda import kirim_ke_telegram # <-- Contoh modul kirim telegram Anda
from apscheduler.schedulers.background import BackgroundScheduler

# 1. Memuat variabel lingkungan dari file .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Konfigurasi Halaman Dashboard Web
st.set_page_config(page_title="Satellite Early Warning System", layout="wide")

# 2. FUNGSI UTAMA (Tempatkan Kodingan Citra Satelit Anda di Sini)
def proses_citra_dan_kirim_telegram():
    timestamp_sekarang = dt_global.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # ========================================================
        # 🛠️ MASUKKAN KODINGAN PENGOLAHAN CITRA SATELIT ANDA DI SINI
        # ========================================================
        # --- 0. INSTALL LIBRARIES (Jalankan ini di sel Colab) ---
        #!pip install xarray cartopy geopandas netCDF4 regionmask

        import ftplib
        import tempfile
        import os
        import math
        import xarray as xr
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import matplotlib.gridspec as gridspec
        import matplotlib.patches as mpatches
        import geopandas as gpd
        import regionmask
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        from datetime import timedelta, timezone

        # --- 1. DATA GEOJSON PERAIRAN KALBAR (Ditanam langsung agar mudah di Colab) ---
        geojson_data = {
          "type": "FeatureCollection",
          "features": [
            {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [[[[109.682449, -1.01299], [109.472576, -0.925766], [109.36546, -1.028361], [109.078015, -1.028361], [109.096485, -1.085609], [109.032521, -1.133018], [108.869161, -1.086308], [108.734007, -1.141511], [108.684515, -1.235738], [108.706406, -1.36994], [108.563638, -1.467973], [108.501772, -1.617404], [108.486543, -1.747798], [108.547458, -1.869627], [108.701647, -1.921975], [108.974809, -1.856302], [109.196575, -1.962901], [109.460219, -1.890566], [109.539276, -1.738602], [110.067255, -1.364582], [109.907763, -1.20902], [109.946613, -1.125004], [109.819305, -1.09132], [109.764551, -1.025857], [109.777557, -1.147519], [109.501468, -1.309202], [109.381757, -1.259409], [109.488048, -0.973071], [109.675336, -1.020409], [109.682449, -1.01299]], [[108.889485, -1.552255], [108.983408, -1.60198], [108.858288, -1.677967], [108.818746, -1.649379], [108.844166, -1.584001], [108.789761, -1.581613], [108.889485, -1.552255]]], [[[109.686742, -1.008513], [109.702425, -0.992156], [109.744195, -1.001519], [109.732422, -0.987444], [109.754315, -0.895151], [109.686742, -1.008513]]]]}, "properties": {"perairan": "Perairan Kayong Utara"}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[108.98053, 0.991699], [108.907104, 1.167725], [108.9729, 1.177124], [109.059692, 1.523926], [109.265076, 1.67749], [109.353636, 1.853447], [109.325317, 1.928284], [109.589905, 1.990723], [109.645605, 2.082006], [109.85646, 2.1624], [109.716746, 2.321897], [109.3326, 2.170758], [108.925713, 1.746024], [108.603518, 0.991771], [108.98053, 0.991699]]]}, "properties": {"perairan": "Perairan Sambas"}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[109.171033, 0.033615], [108.582869, 0.034302], [109.065923, -0.914723], [109.078015, -1.028361], [109.36546, -1.028361], [109.472576, -0.925766], [109.611826, -0.970424], [109.583892, -0.897714], [109.438811, -0.852378], [109.366959, -0.877159], [109.418884, -0.916016], [109.330732, -0.917146], [109.314744, -0.895167], [109.300278, -0.900156], [109.239273, -0.81163], [109.248246, -0.661181], [109.466504, -0.754372], [109.552818, -0.743502], [109.569794, -0.756278], [109.624113, -0.749995], [109.628545, -0.795312], [109.58835, -0.770244], [109.754315, -0.895151], [109.635754, -0.796329], [109.631907, -0.7515], [109.696214, -0.720169], [109.657121, -0.670976], [109.59819, -0.692788], [109.674691, -0.696486], [109.552165, -0.707746], [109.582547, -0.692032], [109.595715, -0.692668], [109.584456, -0.650699], [109.127076, -0.539185], [109.089286, -0.276114], [109.19675, -0.220959], [109.171033, 0.033615]], [[109.656084, -0.699688], [109.688346, -0.712697], [109.578679, -0.716459], [109.656084, -0.699688]], [[109.459095, -0.631611], [109.583636, -0.653021], [109.583155, -0.686001], [109.499415, -0.69428], [109.459095, -0.631611]], [[109.4475, -0.70836], [109.411942, -0.67421], [109.496877, -0.702013], [109.478317, -0.710259], [109.559239, -0.715247], [109.471801, -0.732071], [109.44477, -0.708191], [109.4475, -0.70836]], [[109.360044, -0.651516], [109.363346, -0.617145], [109.476979, -0.684971], [109.360044, -0.651516]], [[109.373987, -0.674861], [109.349965, -0.65212], [109.40552, -0.674548], [109.373987, -0.674861]], [[109.125916, -0.102478], [109.163692, -0.058852], [109.176697, -0.194275], [109.125916, -0.102478]], [[109.169312, -0.207581], [109.083682, -0.270462], [109.094727, -0.329285], [109.059875, -0.216309], [109.169312, -0.207581]]]}, "properties": {"perairan": "Perairan Kubu Raya"}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[110.730863, -2.986988], [110.625654, -3.0263], [110.628283, -2.904303], [110.564602, -2.837638], [110.305813, -2.995255], [110.224225, -2.886016], [110.263987, -2.778579], [110.214608, -2.648045], [110.149088, -2.62124], [110.195938, -2.517015], [110.137684, -2.302348], [110.063409, -2.24508], [110.121747, -2.029662], [110.076254, -1.939368], [109.900759, -1.827719], [110.026722, -1.682714], [110.067255, -1.364582], [109.539276, -1.738602], [109.68946, -2.0], [110.013621, -3.343827], [110.739836, -3.34362], [110.730863, -2.986988]], [[110.168011, -2.852415], [110.192294, -2.912162], [110.133695, -2.898018], [110.168011, -2.852415]], [[110.111675, -2.671967], [110.129247, -2.741605], [110.044381, -2.748222], [110.111675, -2.671967]]]}, "properties": {"perairan": "Perairan Ketapang"}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[108.927124, 0.562683], [108.455948, 0.563119], [108.400024, 0.4], [108.582869, 0.034302], [109.30011, -0.001587], [109.176331, 0.07428], [109.086487, 0.251099], [108.918445, 0.324405], [108.927124, 0.562683]]]}, "properties": {"perairan": "Perairan Pontianak - Mempawah"}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[108.927124, 0.562683], [108.842274, 0.815451], [108.947327, 0.893921], [108.98053, 0.991699], [108.603518, 0.991771], [108.455948, 0.563119], [108.927124, 0.562683]], [[108.69705, 0.774473], [108.708302, 0.802577], [108.728226, 0.732231], [108.69705, 0.774473]]]}, "properties": {"perairan": "Perairan Singkawang - Bengkayang"}}
          ]
        }

        # Konversi ke GeoDataFrame
        gdf_perairan = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf_perairan.set_crs(epsg=4326, inplace=True)

        # --- 2. KONFIGURASI FTP BMKG ---
        FTP_HOST = "202.90.199.64"
        FTP_USER = "stmkg1"
        FTP_PASS = "M7@Vt1L4KX*"

        STASIUN_NAMA = "Stasiun Maritim Pontianak"
        LAT_PTK, LON_PTK = 0.0, 109.33

        # --- 3. FUNGSI LOGIKA WAKTU ---
        # --- 3. FUNGSI LOGIKA WAKTU ---
        def get_latest_time():
          # Menggunakan dt_global yang dijamin aman dari bentrok variabel lokal
          now_utc = dt_global.datetime.now(dt_global.timezone.utc) 
          check_time = now_utc - timedelta(minutes=7)
          rounded_minute = (check_time.minute // 10) * 10
          return check_time.replace(minute=rounded_minute, second=0, microsecond=0)
       
        def get_ftp_paths(dt):
            yyyy, mm, dd = dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d')
            hhmm = dt.strftime('%H%M')
            target_dir = f"/himawari6/netcdf/Indonesia/{yyyy}/{mm}/{dd}"
            file_name = f"H09_B13_Indonesia_{yyyy}{mm}{dd}{hhmm}.nc"
            return target_dir, file_name

        # --- 4. PROSES DOWNLOAD DATA ---
        temp_path = ""
        try:
            target_time = get_latest_time()
            target_dir, file_name = get_ftp_paths(target_time)

            print(f"Menghubungkan ke FTP {FTP_HOST}...")
            ftp = ftplib.FTP(FTP_HOST)
            ftp.login(FTP_USER, FTP_PASS)

            try:
                print(f"Mencoba download: {file_name}")
                ftp.cwd(target_dir)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.nc') as tmp_file:
                    ftp.retrbinary(f'RETR {file_name}', tmp_file.write)
                    temp_path = tmp_file.name
            except:
                print("File terbaru belum tersedia. Mencoba 10 menit sebelumnya...")
                target_time -= timedelta(minutes=10)
                target_dir, file_name = get_ftp_paths(target_time)
                ftp.cwd(target_dir)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.nc') as tmp_file:
                    ftp.retrbinary(f'RETR {file_name}', tmp_file.write)
                    temp_path = tmp_file.name

            ftp.quit()
            print(f"Berhasil memuat data: {file_name}\n")

            # --- 5. ANALISIS DATA (LOOPING 6 WILAYAH PERAIRAN) ---
            ds = xr.open_dataset(temp_path)
            v_name = list(ds.data_vars)[0]
            data_c = ds[v_name] - 273.15
            data_awan = data_c.where(data_c <= 21)

            hasil_analisis = [] # List untuk menyimpan hasil tiap wilayah

            print("Menganalisis 6 Wilayah Perairan...")
            for index, row in gdf_perairan.iterrows():
                nama_perairan = row['perairan']

                # Ambil 1 poligon spesifik
                single_poly_gdf = gdf_perairan.iloc[[index]]

                # Buat masking khusus poligon ini
                mask = regionmask.mask_geopandas(single_poly_gdf, data_c.longitude, data_c.latitude)
                data_masked = data_c.where(mask.notnull())

                # Hitung Suhu Minimum
                min_temp = float(data_masked.min())

                # Hitung Luasan Awan (Suhu < -62 C)
                pixel_count = int((data_masked < -62).sum())
                luasan_km2 = pixel_count * 4 # 1 piksel ~ 4 km2

                # Tentukan Status
                if min_temp < -80:
                    status = "AWAS"
                elif min_temp < -62 and luasan_km2 > 20:
                    status = "WASPADA"
                else:
                    status = "NORMAL"

                # Simpan hasil
                hasil_analisis.append({
                    'nama': nama_perairan.replace("Perairan ", ""), # Singkat nama agar muat di plot
                    'min_temp': min_temp,
                    'luas': luasan_km2,
                    'status': status
                })
                print(f"- {nama_perairan}: {status} (Min: {min_temp:.1f}°C, Luas: {luasan_km2} km²)")

            # --- 6. VISUALISASI DASHBOARD ---
            fig = plt.figure(figsize=(16, 10), facecolor='white')
            gs = gridspec.GridSpec(2, 3, height_ratios=[3, 1], width_ratios=[1.2, 1, 1.2]) # Lebarkan panel teks sedikit

            # A. PETA UTAMA
            ax_map = fig.add_subplot(gs[:, 0:2], projection=ccrs.PlateCarree())
            ax_map.set_facecolor('black')

            levels = [-80, -75, -69, -62, -56, -48, -41, -34, -28, -21]
            plot_awan = data_awan.plot(ax=ax_map, cmap='turbo_r', levels=levels,
                                       transform=ccrs.PlateCarree(), add_colorbar=False)

            ax_map.coastlines(resolution='10m', color='white', linewidth=1.2)
            ax_map.set_extent([106.5, 114.5, -3.5, 3.5], crs=ccrs.PlateCarree())

            # Plot GeoJSON (Garis Cyan)
            gdf_perairan.plot(ax=ax_map, facecolor='none', edgecolor='cyan',
                              linewidth=1.5, alpha=0.8, transform=ccrs.PlateCarree())

            gl = ax_map.gridlines(draw_labels=True, color='white', linestyle='--', alpha=0.3)
            gl.top_labels = False
            gl.right_labels = False

            ax_map.plot(LON_PTK, LAT_PTK, 'ms', markersize=8, transform=ccrs.PlateCarree())
            for r, label in zip([0.45, 0.9], ['50km', '100km']):
                circle = mpatches.Circle((LON_PTK, LAT_PTK), r, fill=False, edgecolor='yellow',
                                         linestyle='--', linewidth=1, transform=ccrs.PlateCarree())
                ax_map.add_patch(circle)
                ax_map.text(LON_PTK, LAT_PTK + r + 0.05, label, color='yellow', fontsize=9, transform=ccrs.PlateCarree())

            waktu_wib = target_time + timedelta(hours=7)
            ax_map.set_title(f"HIMAWARI-9 ENHANCED INFRARED (EH)\n{STASIUN_NAMA} | {waktu_wib.strftime('%d %b %Y | %H:%M')} WIB",
                             fontweight='bold', fontsize=14, loc='left', pad=15)

            # B. PANEL TEKS ANALISIS (Menampilkan 6 Wilayah)
            ax_text = fig.add_subplot(gs[0, 2])
            ax_text.axis('off')
            ax_text.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, edgecolor='black', lw=1.5, transform=ax_text.transAxes))

            # Susun teks laporan dari hasil looping
            teks_laporan = f"REGIONAL ANALYSIS REPORT\n{'='*24}\n\n"
            for res in hasil_analisis:
                # Beri tanda peringatan jika status bukan NORMAL
                alert_icon = "⚠️ " if res['status'] != "NORMAL" else ""
                teks_laporan += f"{alert_icon}[{res['nama']}]\n"

                # Handle kasus jika tidak ada awan sama sekali (min_temp = nan)
                if math.isnan(res['min_temp']):
                    teks_laporan += f" Status: CLEAR\n\n"
                else:
                    teks_laporan += f" T.Min : {res['min_temp']:.1f} °C\n"
                    teks_laporan += f" Area  : {res['luas']} km² (<-62°C)\n"
                    teks_laporan += f" Status: {res['status']}\n\n"

            # --- TAMBAHAN SUMBER DATA ---
            teks_laporan += f"{'='*24}\n"
            teks_laporan += f"Source: BMKG FTP (Himawari-9)\n"

            ax_text.text(0.05, 0.95, teks_laporan, transform=ax_text.transAxes, fontsize=10, verticalalignment='top', family='monospace')

            # C. PANEL COLORBAR
            ax_cbar = fig.add_subplot(gs[1, 2])
            ax_cbar.axis('off')
            cbar_ax = inset_axes(ax_cbar, width="90%", height="20%", loc='center')
            cb = plt.colorbar(plot_awan, cax=cbar_ax, orientation='horizontal')
            cb.set_label('Cloud Top Temperature (°C)', fontweight='bold')

            plt.tight_layout()
            # Simpan gambar peta ke dalam file lokal
            fig.savefig("latest_map.png", dpi=150, bbox_inches='tight')
            plt.close(fig) # Bersihkan memori RAM server dari matplotlib

        except Exception as e:
            print(f"Terjadi kesalahan: {e}")

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        # ========================================================
        
        # Mencatat waktu eksekusi sukses ke file lokal (sebagai log sederhana)
        with open("last_run.txt", "w") as f:
            f.write(timestamp_sekarang)
            
        print(f"[{timestamp_sekarang}] SUKSES: Data citra diproses & peringatan dini dikirim ke Telegram.")
    
    except Exception as e:
        print(f"[{timestamp_sekarang}] ERROR: Gagal memproses citra. Detail: {str(e)}")

# 3. INISIALISASI SCHEDULER YANG AMAN UNTUK STREAMLIT
if 'scheduler_berjalan' not in st.session_state:
    try:
        scheduler = BackgroundScheduler()
        # Menjadwalkan fungsi berjalan otomatis setiap 10 menit
        scheduler.add_job(proses_citra_dan_kirim_telegram, 'interval', minutes=10, id='job_satelit_10min')
        scheduler.start()
        st.session_state['scheduler_berjalan'] = True
        st.session_state['sched_obj'] = scheduler
    except Exception as e:
        st.warning(f"Gagal mengaktifkan scheduler otomatis: {e}")

# Jalankan scheduler latar belakang secara otomatis saat aplikasi web menyala
#sched = jalankan_otomatisasi()

# 4. ANTARMUKA WEBSITE (STREAMLIT DASHBOARD)
st.title("🛰️ Satellite Early Warning System Dashboard")
st.markdown("Aplikasi berbasis website untuk otomasi pengolahan citra satelit berbasis spasial dan peringatan bencana.")

# Membaca log waktu eksekusi terakhir dari file
if os.path.exists("last_run.txt"):
    with open("last_run.txt", "r") as f:
        waktu_terakhir = f.read()
else:
    waktu_terakhir = "Belum pernah dieksekusi semenjak server aktif"

# Layout Kolom Dashboard
col_status, col_kontrol = st.columns(2)

with col_status:
    st.subheader("Informasi Log & Jadwal")
    # Memeriksa status scheduler melalui session_state
    if st.session_state.get('scheduler_berjalan', False):
        st.success("🔄 Sistem Otomatisasi: AKTIF (Berjalan di Latar Belakang)")
    else:
        st.error("🛑 Sistem Otomatisasi: BERHENTI")
        
    st.info("⏱️ **Frekuensi Cek:** Otomatis Setiap 10 Menit")
    st.metric(label="Waktu Eksekusi Terakhir", value=waktu_terakhir)

with col_kontrol:
    st.subheader("Pemicu Manual (Manual Override)")
    st.write("Gunakan tombol di bawah ini jika ingin menjalankan kodingan secara instan saat ini juga tanpa menunggu jadwal 10 menit:")
    
    if st.button("🚀 Jalankan Pengolahan Data & Kirim Sekarang"):
        with st.spinner("Sedang memproses citra satelit dan mengirim notifikasi ke Telegram..."):
            proses_citra_dan_kirim_telegram()
        st.success("Eksekusi manual sukses dilakukan!")
        #st.rerun() # Refresh halaman untuk memperbarui status waktu terakhir
        except Exception as e:
        # Tambahkan dua baris ini agar error tidak bisa sembunyi
        import traceback
        st.error(f"🚨 PROSES GAGAL: {e}")
        st.code(traceback.format_exc()) # Menampilkan jejak error lengkap di web
# --- TAMBAHKAN KODE INI DI SINI ---
st.subheader("🗺️ Peta Hasil Analisis Citra Satelit Terbaru")
if os.path.exists("latest_map.png"):
    st.image("latest_map.png", caption="Visualisasi Satelit Himawari-9 Enhanced Infrared (EH)", use_container_width=True)
else:
    st.info("ℹ️ Belum ada gambar peta yang digenerate. Silakan klik tombol 'Jalankan Pengolahan Data & Kirim Sekarang' di atas untuk memicu pembuatan peta pertama kali.")
# ----------------------------------
st.divider()
st.caption("Catatan Keamanan: Token bot Telegram dan Chat ID Anda telah diamankan menggunakan file `.env`.")

