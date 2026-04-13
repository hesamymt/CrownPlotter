import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Set the page to be wide for better plotting
st.set_page_config(page_title="Crown Plotter", layout="wide")

# --- DATA PARSING FUNCTIONS ---
# Adjusted to read a list of lines from memory instead of a file path

def probe_shape(lines):
    n_rows = 0
    n_cols = None
    for line in lines:
        line = line.strip()
        if not line: continue
        n_rows += 1
        if n_cols is None:
            parts = line.split(None, 2)
            if len(parts) < 3: continue
            nums = np.fromstring(parts[2], sep=" ")
            if nums.size == 0: continue
            n_cols = int(nums.size)
            
    if n_cols is None or n_rows == 0:
        return 0, None
    return n_rows, n_cols

def load_data(lines, n_rows, n_cols, dtype=np.float32):
    data = np.empty((n_rows, n_cols), dtype=dtype)
    ids, timestamps = [], []
    i = 0
    for raw in lines:
        line = raw.strip()
        if not line: continue
        parts = line.split(None, 2)
        if len(parts) < 3: continue

        ids.append(parts[0])
        timestamps.append(parts[1])
        nums = np.fromstring(parts[2], sep=" ")

        if nums.size == n_cols:
            data[i, :] = nums.astype(dtype, copy=False)
        elif nums.size < n_cols:
            y = np.empty(n_cols, dtype=dtype)
            y[:] = np.nan
            y[: nums.size] = nums.astype(dtype, copy=False)
            data[i, :] = y
        else:
            data[i, :] = nums[:n_cols].astype(dtype, copy=False)
        i += 1

    if i != n_rows:
        data = data[:i, :]
        ids = ids[:i]
        timestamps = timestamps[:i]
    return data, ids, timestamps


# --- WEB APP UI ---

st.title("Crown Plotter Over Roll Length")

# 1. Mode Selection (Replaces Tkinter Radiobuttons)
mode = st.radio("Plotting Mode:", options=["Overlay (One Plot)", "Stacked (Separate Plots)"])

# 2. Drag-and-Drop File Uploader (Replaces tkinterdnd2)
uploaded_files = st.file_uploader(
    "Drag and Drop .txt files here... (Load as many as you need)", 
    type=["txt"], 
    accept_multiple_files=True
)

# 3. Main Application Logic
if uploaded_files:
    data_list, ts_list, cols_list, names_list = [], [], [], []

    # Process each uploaded file
    for f in uploaded_files:
        # Read the file from memory into a list of strings
        lines = f.getvalue().decode("utf-8", errors="ignore").splitlines()
        
        n_rows, n_cols = probe_shape(lines)
        if n_cols is None:
            st.error(f"No valid data found in {f.name}.")
            continue
            
        data, ids, ts = load_data(lines, n_rows, n_cols)
        
        data_list.append(data)
        ts_list.append(ts)
        cols_list.append(n_cols)
        names_list.append(f.name) # Get original filename

    if data_list:
        n_rows_min = min(d.shape[0] for d in data_list)
        
        # 4. The Slider UI (Replaces matplotlib.widgets.Slider)
        st.write("### Data Explorer")
        initial_idx = st.slider("Select Row Index:", min_value=0, max_value=n_rows_min - 1, value=0, step=1)

        # 5. Plotting Logic
        colors = plt.cm.tab10.colors 
        n_files = len(data_list)

        if mode == "Overlay (One Plot)":
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for i in range(n_files):
                x = np.arange(cols_list[i])
                ax.plot(x, data_list[i][initial_idx], lw=1.5, color=colors[i % 10], label=names_list[i])

            ax.set_ylabel("Crown value")
            ax.set_xlabel("Position along cylinder length (index)")
            ax.grid(True, alpha=0.2)
            ax.legend()
            
            t = ts_list[0][initial_idx] if initial_idx < len(ts_list[0]) else "N/A"
            ax.set_title(f"Overlay View — row {initial_idx} | TS (File 1)={t}")

            # Send the plot to the web page
            st.pyplot(fig)

        else: # Stacked / Separate Plots
            fig_height = 4 * n_files
            fig, axes_raw = plt.subplots(n_files, 1, figsize=(12, fig_height), sharex=False)
            axes = axes_raw if n_files > 1 else [axes_raw]
            plt.subplots_adjust(bottom=0.15, hspace=0.35)

            for i in range(n_files):
                x = np.arange(cols_list[i])
                ax = axes[i]
                
                ax.plot(x, data_list[i][initial_idx], lw=1.5, color=colors[i % 10])
                
                t = ts_list[i][initial_idx] if initial_idx < len(ts_list[i]) else "N/A"
                ax.set_title(f"{names_list[i]} — row {initial_idx} | ts={t}")
                ax.set_ylabel("Crown value")
                ax.grid(True, alpha=0.2)
                
                if i == n_files - 1:
                    ax.set_xlabel("Position along cylinder length (index)")

            # Send the plot to the web page
            st.pyplot(fig)
else:
    st.info("Waiting for files to be uploaded...")