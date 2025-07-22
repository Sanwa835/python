import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="領料系統", layout="centered")

# 讀取 materials.xlsx
try:
    df = pd.read_excel("materials.xlsx")
except Exception as e:
    st.error(f"讀取 Excel 失敗: {e}")
    st.stop()

required_cols = ["站別", "料號", "物料名稱", "可領數量"]
if not all(col in df.columns for col in required_cols):
    st.error(f"Excel 欄位錯誤，請確認包含：{required_cols}")
    st.stop()

# 動態取得存在的站別（避免使用不存在的 D、E）
stations = sorted(df["站別"].unique())
station_index = stations.index(st.session_state.get("current_station", stations[0])) if "current_station" in st.session_state else 0
current_station = stations[station_index]

st.title("🏭 領料系統")
st.subheader(f"目前：{current_station} 站")

# 初始化剩餘可領數量（只存在 session_state，不會改到 Excel）
if "remaining" not in st.session_state:
    st.session_state["remaining"] = {}
    station_df = df[df["站別"] == current_station]
    for _, row in station_df.iterrows():
        st.session_state["remaining"][row["料號"]] = row["可領數量"]

# 初始化 log 檔案
log_file = "log.xlsx"
if not os.path.exists(log_file):
    log_df = pd.DataFrame(columns=["時間", "站別", "料號", "數量", "狀態", "訊息"])
    log_df.to_excel(log_file, index=False)
else:
    log_df = pd.read_excel(log_file)

# 使用者輸入
material_id = st.text_input("請輸入料號：", key="input_id")
amount = st.number_input("請輸入數量：", min_value=1, step=1)
submit = st.button("送出")

if submit:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if material_id not in st.session_state["remaining"]:
        msg = "料號錯誤或不屬於當前站別"
        st.error(msg)
        status = "錯誤"

    elif amount > st.session_state["remaining"][material_id]:
        max_qty = st.session_state["remaining"][material_id]
        msg = f"可領數量不足（最多 {max_qty}）"
        st.error(msg)
        status = "錯誤"

    else:
        row = df[(df["站別"] == current_station) & (df["料號"] == material_id)].iloc[0]
        msg = f"成功領取 {amount} 個【{row['物料名稱']}】"
        st.success(msg)
        status = "成功"
        st.session_state["remaining"][material_id] -= amount

    # 建立 log 紀錄
    new_log = pd.DataFrame([{
        "時間": now,
        "站別": current_station,
        "料號": material_id,
        "數量": amount,
        "狀態": status,
        "訊息": msg
    }])

    # 更新 log 檔案
    log_df = pd.concat([log_df, new_log], ignore_index=True)
    log_df.to_excel(log_file, index=False)

    # 如果全部領完，自動換站
    if all(qty <= 0 for qty in st.session_state["remaining"].values()):
        st.success(f"✅ {current_station} 站所有物料已領完，切換到下一站。")
        next_index = (station_index + 1) % len(stations)
        st.session_state["current_station"] = stations[next_index]
        next_station_df = df[df["站別"] == stations[next_index]]
        st.session_state["remaining"] = {row["料號"]: row["可領數量"] for _, row in next_station_df.iterrows()}
        st.experimental_rerun()

# 顯示剩餘物料
st.markdown(f"### {current_station} 站 剩餘可領物料")
remaining_data = []
for material, qty in st.session_state["remaining"].items():
    row = df[(df["站別"] == current_station) & (df["料號"] == material)].iloc[0]
    remaining_data.append([material, row["物料名稱"], qty])
st.table(pd.DataFrame(remaining_data, columns=["料號", "物料名稱", "剩餘可領數量"]))

# 顯示輸入紀錄
st.divider()
st.markdown("### 📋 已輸入紀錄")
current_logs = log_df[log_df["站別"] == current_station].sort_values(by="時間", ascending=False)
st.dataframe(current_logs, use_container_width=True)