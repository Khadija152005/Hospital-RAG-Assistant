"""
config.py
─────────────────────────────────────────────────────────────────────
Central configuration file for the RAG component.
All constants, mappings, and settings live here.
─────────────────────────────────────────────────────────────────────
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────────────────────────
GROQ_API_KEY          = os.getenv("GROQ_API_KEY")
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")
COLLECTION_NAME       = os.getenv("COLLECTION_NAME", "hospital_manuals")
EMBEDDING_MODEL       = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# ─────────────────────────────────────────────────────────────────
# LLM SETTINGS
# ─────────────────────────────────────────────────────────────────
GROQ_MODEL      = "llama-3.1-70b-versatile"   # Best free model on Groq
LLM_TEMPERATURE = 0                            # 0 = deterministic, no creativity
                                               # Good for technical answers


# ─────────────────────────────────────────────────────────────────
# CHUNKING SETTINGS
# ─────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 1000   # characters per chunk
CHUNK_OVERLAP = 150    # overlap between consecutive chunks
                       # prevents answers being split across chunks

# ─────────────────────────────────────────────────────────────────
# RETRIEVAL SETTINGS
# ─────────────────────────────────────────────────────────────────
TOP_K_RESULTS = 5      # number of chunks to retrieve per query


# ─────────────────────────────────────────────────────────────────
# MANUAL DEFINITIONS
# Each entry maps a manual identifier to its file and device info
# ─────────────────────────────────────────────────────────────────
MANUALS = {
    "BeneFusion_VP3": {
        "path":         "data/manuals/BeneFusion_VP3.pdf",
        "device_type":  "Infusion Pump",
        "manufacturer": "Mindray Scientific",
        "model":        "BeneFusion VP3 Vet",
        "source_file":  "BeneFusion_VP3.pdf",
    },
    "MAC_2000": {
        "path":         "data/manuals/MAC_2000.pdf",
        "device_type":  "ECG Machine",
        "manufacturer": "GE Healthcare",
        "model":        "MAC 2000",
        "source_file":  "MAC_2000.pdf",
    },
    "Fresenius_4008S": {
        "path":         "data/manuals/Fresenius_4008S.pdf",
        "device_type":  "Hemodialysis Machine",
        "manufacturer": "Fresenius Medical Care",
        "model":        "4008S",
        "source_file":  "Fresenius_4008S.pdf",
    },
}


# ─────────────────────────────────────────────────────────────────
# DEVICE → MANUAL MAPPING
# Links asset_type values from the ASSET table to manual identifiers
# Used for filtered search when asset_id is known
# ─────────────────────────────────────────────────────────────────
DEVICE_TO_MANUAL = {
    "Infusion Pump":          "BeneFusion_VP3",
    "ECG Machine":            "MAC_2000",
    "Hemodialysis Machine":   "Fresenius_4008S",
}


# ─────────────────────────────────────────────────────────────────
# KEYWORD → MANUAL MAPPING
# Used to auto-detect which manual to search from the query text
# ─────────────────────────────────────────────────────────────────
MANUAL_KEYWORDS = {
    "BeneFusion_VP3": [
        "infusion pump", "benefusion", "vp3", "infusion set",
        "occlusion", "bolus", "kvo", "vtbi", "drip", "air in line",
        "infusion rate", "mindray"
    ],
    "MAC_2000": [
        "ecg", "mac 2000", "mac2000", "electrocardiograph",
        "ekg", "ecg analysis", "ge healthcare", "resting ecg",
        "ecg data", "ecg noise", "rhythm", "arrhythmia"
    ],
    "Fresenius_4008S": [
        "dialysis", "hemodialysis", "fresenius", "4008", "4008s",
        "dialyzer", "heparin", "blood flow", "conductivity",
        "t1 test", "f01", "f02", "f95", "bicarbonate"
    ],
}


# ─────────────────────────────────────────────────────────────────
# SECTION TYPE KEYWORDS
# Used to auto-label each chunk with its content category
# ─────────────────────────────────────────────────────────────────
SECTION_TYPE_KEYWORDS = {
    "alarms": [
        "alarm", "error", "f01", "f02", "f95", "occlusion",
        "countermeasure", "alert", "warning", "fault", "failure",
        "air in line", "system error", "no battery"
    ],
    "maintenance": [
        "maintenance", "inspection", "preventive", "corrective",
        "tsc", "technical safety", "service", "overhaul", "pm ",
        "maintenance plan", "maintenance schedule"
    ],
    "calibration": [
        "calibration", "calibrate", "dip switch", "adjustment",
        "sensor calibration", "pressure calibration", "zero point"
    ],
    "installation": [
        "install", "mount", "clamp", "connect", "assembly",
        "setup", "pole clamp", "power cord", "ac power"
    ],
    "cleaning": [
        "clean", "disinfect", "disinfection", "sanitiz",
        "ethanol", "isopropanol", "hydrogen peroxide", "glutaraldehyde",
        "preservation", "sanitation"
    ],
    "battery": [
        "battery", "charging", "lithium", "power down",
        "battery life", "battery performance", "low battery"
    ],
    "troubleshooting": [
        "troubleshoot", "problem", "cause:", "solution:",
        "does not", "won't", "cannot", "not working", "fails"
    ],
    "specifications": [
        "specification", "range:", "parameter", "capacity",
        "voltage", "frequency", "accuracy", "weight", "dimension",
        "operating environment", "temperature"
    ],
    "configuration": [
        "configure", "configuration", "setting", "setup menu",
        "wlan", "network", "language", "date and time", "brightness"
    ],
}
