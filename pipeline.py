import os, subprocess, glob, json

# --- 路徑設定 ---
S2_REF = "docs/data/S2_20150814_COG.tif" # 用這張圖當範本
S1_DIR = "/home/gisele/webgis_work/S1_unzipped"
OUT_DIR = "docs/data"
os.makedirs(OUT_DIR, exist_ok=True)

def run(cmd):
    print(f"執行: {' '.join(cmd)}")
    subprocess.run(cmd)

# 1. 取得參考影像的邊界與座標系統 (避免負二十一億的報錯)
def get_info(path):
    res = subprocess.run(["gdalinfo", "-json", path], capture_output=True, text=True)
    info = json.loads(res.stdout)
    c = info['cornerCoordinates']
    ext = [c['upperLeft'][0], c['lowerRight'][1], c['lowerRight'][0], c['upperLeft'][1]]
    gt = info['geoTransform']
    return ext, abs(gt[1]), abs(gt[5])

print(">>> 正在對齊座標系統...")
ext, rx, ry = get_info(S2_REF)

# 2. 處理 S1 淹水向量 (SHP -> COG)
print(">>> 正在生成淹水時序圖...")
jobs = [
    ("20150720", f"{S1_DIR}/S1A_IW_GRDH_1SDV_20150720T*/mask.shp"),
    ("20150813", f"{S1_DIR}/S1A_IW_GRDH_1SDV_20150813T*/mask.shp"),
    ("20160807", f"{S1_DIR}/S1A_IW_GRDH_1SDV_20160807T*/mask.shp")
]

for date, pat in jobs:
    shp = glob.glob(pat)[0]
    temp, final = f"temp_{date}.tif", f"{OUT_DIR}/Flood_{date}_COG.tif"
    # 使用 -te 和 -tr 強制對齊 S2 影像
    run(["gdal_rasterize", "-at", "-burn", "1", "-te", str(ext[0]), str(ext[1]), str(ext[2]), str(ext[3]),
         "-tr", str(rx), str(ry), "-a_nodata", "0", "-ot", "Byte", shp, temp])
    if os.path.exists(final): os.remove(final)
    run(["rio", "cogeo", "create", temp, final])
    if os.path.exists(temp): os.remove(temp)

print("✨ 資料洗好了！")