import os
import subprocess
import glob
import re
import json

# --- 路徑設定 ---
SHP_DIR = "/home/gisele/webgis_work/S1_unzipped"
DATA_DIR = "docs/data"
# 參考影像 (用妳剛才成功的 S2 影像當範本)
REF_IMAGE = f"{DATA_DIR}/S2_20150814_COG.tif"

os.makedirs(DATA_DIR, exist_ok=True)

def get_ref_info(path):
    # 獲取參考影像的範圍與解析度
    cmd = ["gdalinfo", "-json", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(res.stdout)
    coords = info['cornerCoordinates']
    res_x = abs(info['geoTransform'][1])
    res_y = abs(info['geoTransform'][5])
    # [xmin, ymin, xmax, ymax]
    extent = [coords['upperLeft'][0], coords['lowerRight'][1], coords['lowerRight'][0], coords['upperLeft'][1]]
    return extent, res_x, res_y

def run_rio(inp, outp):
    if os.path.exists(outp): os.remove(outp)
    print(f">>> 正在建立 COG: {outp}")
    subprocess.run(["rio", "cogeo", "create", inp, outp])

# 1. 取得參考資訊
print("--- 讀取衛星影像座標系統 ---")
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
    # 網格化：使用 -te (範圍) 和 -tr (解析度) 完美對齊 S2
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

print("✨ 資料對齊處理完成！")