import os, subprocess, glob

# --- 路徑設定 ---
NAS_S2 = "/home/gisele/nas/02.Course/26S_BigData/KuroSiwo_STAC_V5/EMSR174_Flood_in_Skopje/S2"
S1_UNZIPPED = "/home/gisele/webgis_work/S1_unzipped"
OUT = "docs/data"
os.makedirs(OUT, exist_ok=True)

def run(cmd):
    print(f"執行指令: {' '.join(cmd)}")
    subprocess.run(cmd)

# 1. 處理 S2 衛星影像 (縮放色彩，解決灰色問題)
print(">>> 正在處理 S2 衛星底圖...")
for d in ["20150814", "20160805"]:
    tiles = glob.glob(f"{NAS_S2}/*{d}*.tif")
    vrt, temp, final = f"{d}.vrt", f"scaled_{d}.tif", f"{OUT}/S2_{d}_COG.tif"
    run(["gdalbuildvrt", vrt] + tiles)
    run(["gdal_translate", "-ot", "Byte", "-scale", "0", "3000", "0", "255", vrt, temp])
    if os.path.exists(final): os.remove(final)
    run(["rio", "cogeo", "create", temp, final])
    for f in [vrt, temp]: 
        if os.path.exists(f): os.remove(f)

# 2. 處理 S1 淹水標籤 (向量轉網格)
print(">>> 正在處理 S1 淹水標籤...")
jobs = [
    ("20150720", f"{S1_UNZIPPED}/S1A_IW_GRDH_1SDV_20150720T*/mask.shp"),
    ("20150813", f"{S1_UNZIPPED}/S1A_IW_GRDH_1SDV_20150813T*/mask.shp"),
    ("20160807", f"{S1_UNZIPPED}/S1A_IW_GRDH_1SDV_20160807T*/mask.shp")
]
for date, pattern in jobs:
    shp_list = glob.glob(pattern)
    if not shp_list: continue
    shp, temp, final = shp_list[0], f"temp_{date}.tif", f"{OUT}/Flood_{date}_COG.tif"
    run(["gdal_rasterize", "-at", "-burn", "1", "-tr", "0.0001", "0.0001", "-a_nodata", "0", "-ot", "Byte", shp, temp])
    if os.path.exists(final): os.remove(final)
    run(["rio", "cogeo", "create", temp, final])
    if os.path.exists(temp): os.remove(temp)

print("✨ 伺服器端資料洗好了！")