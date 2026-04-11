import os, subprocess, glob, json

# --- 設定路徑 ---
NAS_S2 = "/home/gisele/nas/02.Course/26S_BigData/KuroSiwo_STAC_V5/EMSR174_Flood_in_Skopje/S2"
S1_UNZIPPED = "/home/gisele/webgis_work/S1_unzipped" # 妳剛才解壓好的地方
DATA_OUT = "docs/data"
os.makedirs(DATA_OUT, exist_ok=True)

def run(cmd):
    subprocess.run(cmd)

# 1. 處理靜態底圖 (只做一次)
# 請手動確保妳原本的 LULC_174_COG.tif 和 Precip_174_COG.tif 已經在 docs/data 裡

# 2. 處理 S2 衛星底圖 (縫合並轉 COG)
print(">>> 處理 S2 衛星影像...")
dates = ["20150814", "20160805"]
for d in dates:
    tiles = glob.glob(f"{NAS_S2}/*{d}*.tif")
    vrt = f"{d}.vrt"
    out = f"{DATA_OUT}/S2_{d}.tif"
    run(["gdalbuildvrt", vrt] + tiles)
    if os.path.exists(out): os.remove(out)
    run(["rio", "cogeo", "create", vrt, out])
    os.remove(vrt)

# 3. 處理 S1 淹水向量 (SHP 轉 COG) - 解決座標報錯的核心
print(">>> 處理 S1 淹水標籤...")
# 我們直接指定那三個日期的 SHP 路徑
s1_jobs = [
    ("20150720", f"{S1_UNZIPPED}/S1A_IW_GRDH_1SDV_20150720T*/mask.shp"),
    ("20150813", f"{S1_UNZIPPED}/S1A_IW_GRDH_1SDV_20150813T*/mask.shp"),
    ("20160807", f"{S1_UNZIPPED}/S1A_IW_GRDH_1SDV_20160807T*/mask.shp")
]

for date, pattern in s1_jobs:
    shp = glob.glob(pattern)[0]
    out = f"{DATA_OUT}/Flood_{date}.tif"
    temp = f"temp_{date}.tif"
    
    # 使用 -extents 讓它自動計算範圍，不再手動輸入解析度避免報錯
    run(["gdal_rasterize", "-burn", "1", "-at", "-tr", "0.0001", "0.0001", 
         "-a_nodata", "0", "-ot", "Byte", shp, temp])
    if os.path.exists(out): os.remove(out)
    run(["rio", "cogeo", "create", temp, out])
    os.remove(temp)

print("✨ 所有資料已就緒！")