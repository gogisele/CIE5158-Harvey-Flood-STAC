import os
import subprocess
import glob
import re
import json

# --- 路徑設定 ---
SHP_DIR = "/home/gisele/webgis_work/S1_unzipped"
DATA_DIR = "docs/data"
# 使用這張成功的影像作為座標與解析度的「模版」
REF_IMAGE = f"{DATA_DIR}/S2_20150814_COG.tif"

os.makedirs(DATA_DIR, exist_ok=True)

def get_ref_info(path):
    """取得參考影像的邊界(Extent)與解析度(Resolution)"""
    cmd = ["gdalinfo", "-json", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(res.stdout)
    coords = info['cornerCoordinates']
    # [xmin, ymin, xmax, ymax]
    extent = [coords['upperLeft'][0], coords['lowerRight'][1], coords['lowerRight'][0], coords['upperLeft'][1]]
    res_x = abs(info['geoTransform'][1])
    res_y = abs(info['geoTransform'][5])
    return extent, res_x, res_y

def run_rio(inp, outp):
    if os.path.exists(outp): os.remove(outp)
    print(f">>> 正在建立 COG: {outp}")
    subprocess.run(["rio", "cogeo", "create", inp, outp])

# 1. 取得參考影像的座標資訊
print("--- 讀取衛星影像空間資訊 ---")
ext, rx, ry = get_ref_info(REF_IMAGE)

# 2. 處理 S1 向量轉圖片
shp_files = glob.glob(f"{SHP_DIR}/**/mask.shp", recursive=True)
print(f"找到 {len(shp_files)} 個淹水範圍向量檔")

for shp in shp_files:
    match = re.search(r"(\d{8})T", shp)
    if not match: continue
    date_str = match.group(1)
    
    temp_tif = f"temp_{date_str}.tif"
    out_cog = f"{DATA_DIR}/Flood_{date_str}_COG.tif"
    
    print(f"--- 正在處理日期: {date_str} ---")
    # 使用 -te (target extent) 和 -tr (target resolution) 完美對齊 S2 影像
    subprocess.run([
        "gdal_rasterize", "-at", "-burn", "1", 
        "-te", str(ext[0]), str(ext[1]), str(ext[2]), str(ext[3]),
        "-tr", str(rx), str(ry),
        "-a_nodata", "0", "-ot", "Byte",
        shp, temp_tif
    ])
    
    if os.path.exists(temp_tif):
        run_rio(temp_tif, out_cog)
        os.remove(temp_tif)

print("✨ 萬事具備！資料已精準對齊。")