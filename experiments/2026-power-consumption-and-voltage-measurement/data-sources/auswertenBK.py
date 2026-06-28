import pandas as pd
import matplotlib.pyplot as plt

# CSV einlesen
df = pd.read_csv(
    "BKmoleNET-Data - data.csv",
    header=[0, 1],
    decimal=".",
#    sep=",",
#    quotechar='"'

)

# Spaltennamen direkt umbenennen
df.columns = [
    "time",
    "id",
    "bme_hum",
    "bme_pres",
    "bme_temp",
    "ds_temp",
    "teros_vwc",
    "teros_temp",
    "teros_perm",
    "teros_econ",
    "u",
    "raw"
]

# Zeitstempel umwandeln
df["time"] = pd.to_datetime(df["time"], utc=True)

# Optional: UTC -> deutsche Zeit
df["time"] = df["time"].dt.tz_convert("Europe/Berlin")

# Nach Device-ID filtern
df = df[
    df["id"] == "igc-2026-06-19-otaa"
]

# Ausgabe
# print(df.head())

# Zugriff auf einzelne Spalten
# print(df["u"])

# print(df["u"].mean())

# df["u"].plot()

# df[["time", "u"]]

# Spannung als Zahl interpretieren
df["u"] = pd.to_numeric(df["u"], errors="coerce")

# Plot
plt.figure(figsize=(12, 5))

# plt.plot(df["time"], df["u"])
# plt.scatter(df["time"], df["u"])
# plt.plot(df["time"], df["u"], marker=".")
plt.plot((df["time"].values-df["time"].values[0]).astype(float)/10**9/60/60/24, df["u"], ".")

plt.xlabel("Time (Days)")
plt.ylabel("Voltage U (V)")
plt.title("1st Run Active Energy AA non-fresh")

plt.grid(True)
plt.tight_layout()

plt.show()
