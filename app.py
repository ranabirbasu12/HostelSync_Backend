import streamlit as st
import threading
import time
import tinytuya

# ----------------------------
# Config
# ----------------------------
LOW_THRESHOLD = 30  # mA
CHECK_INTERVAL = 30  # seconds
DEVICE_ID = 'd71c1331098934b443tmn5'
DEVICE_IP = '192.168.1.58'
DEVICE_KEY = ">F5)^*gm@)s#a!r'"
DEVICE_VERSION = "3.3"

# ----------------------------
# Connect to device
# ----------------------------
device = tinytuya.OutletDevice(
    dev_id=DEVICE_ID,
    address=DEVICE_IP,
    local_key=DEVICE_KEY,
    version=DEVICE_VERSION
)

# ----------------------------
# State Initialization
# ----------------------------
if "device_data" not in st.session_state:
    st.session_state.device_data = {
        "current": 0,
        "power": False,
        "status_msg": "Initializing...",
        "low_flag": False,
        "last_update": time.time(),
        "log": []
    }

# ----------------------------
# Logging helper
# ----------------------------
def log(msg):
    now = time.strftime("%H:%M:%S")
    st.session_state.device_data["log"].append(f"[{now}] {msg}")
    st.session_state.device_data["log"] = st.session_state.device_data["log"][-100:]

# ----------------------------
# On-demand device status update
# ----------------------------
def update_device_status():
    try:
        data = device.status()
        dps = data.get('dps', {})
        current = dps.get('18', 0)
        power = dps.get('1', False)

        st.session_state.device_data["current"] = current
        st.session_state.device_data["power"] = power
        st.session_state.device_data["last_update"] = time.time()

        if not power:
            st.session_state.device_data["status_msg"] = "Device is OFF"
            st.session_state.device_data["low_flag"] = False
        elif current > LOW_THRESHOLD:
            st.session_state.device_data["status_msg"] = "Machine is in use"
            st.session_state.device_data["low_flag"] = False
        else:
            if not st.session_state.device_data["low_flag"]:
                st.session_state.device_data["status_msg"] = "Low current detected. Monitoring next cycle..."
                st.session_state.device_data["low_flag"] = True
            else:
                device.turn_off()
                st.session_state.device_data["status_msg"] = "Machine not in use, turned OFF"
                st.session_state.device_data["low_flag"] = False

        log(st.session_state.device_data["status_msg"])

    except Exception as e:
        log(f"Error during status update: {e}")

# ----------------------------
# API endpoints using query params
# ----------------------------
params = st.query_params
action = params.get("action", None)

if action == "status":
    update_device_status()
    st.json({
        "current": st.session_state.device_data["current"],
        "power": st.session_state.device_data["power"],
        "status": st.session_state.device_data["status_msg"],
        "last_updated": st.session_state.device_data["last_update"]
    })

elif action == "turn_on":
    try:
        device.turn_on()
        log("Manual turn ON")
        st.json({"result": "on"})
    except Exception as e:
        log(f"Failed ON: {e}")
        st.json({"error": str(e)})

elif action == "turn_off":
    try:
        device.turn_off()
        log("Manual turn OFF")
        st.json({"result": "off"})
    except Exception as e:
        log(f"Failed OFF: {e}")
        st.json({"error": str(e)})

elif action == "log":
    st.json({"log": st.session_state.device_data["log"]})

else:
    st.write("⚙️ Smart Plug Monitor Backend is Running")
    st.write("Available endpoints:")
    st.code("?action=status")
    st.code("?action=turn_on")
    st.code("?action=turn_off")
    st.code("?action=log")