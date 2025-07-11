# 🔥 India Forest Fire Bivariate Hex Map (Live FIRMS Data)

Visualize forest fire activity in India (or any region) using live NASA FIRMS API.  
Displays a bivariate **hexagonal map** with interactive filters, legend, and CSV export.

---

## 🚀 Features

- **Live NASA FIRMS Data:** MODIS, VIIRS SNPP, or VIIRS NOAA-20
- **Hexagonal Grid Binning:** Uniform spatial statistics with H3 hexagons
- **Bivariate Map:** 
    - Color = Mean intensity (brightness)
    - Height = Frequency (fire days)
- **Filters:** Days, confidence, year, month, hex resolution, sensor, bounding box
- **Download:** Filtered fire CSV
- **Legend:** Bivariate grid for interpretation

---

## 🖥️ Usage

1. Save `app.py` and `requirements.txt` in a directory.
2. Install dependencies (best in a fresh virtual environment):
    ```bash
    pip install -r requirements.txt
    ```
3. **Get your NASA FIRMS API key:**  
   [https://firms.modaps.eosdis.nasa.gov/api/map_key/](https://firms.modaps.eosdis.nasa.gov/api/map_key/)
4. Place your API key in `app.py` (or use Streamlit secrets for production).
5. Start the app:
    ```bash
    streamlit run app.py
    ```
6. Use the sidebar for filters; click "Download filtered CSV" for results.

---

## 🧑‍💻 Troubleshooting

- If you get a geopandas/shapely error, update all geospatial libraries as shown above.
- For "No data available" errors, try a broader time range, lower confidence, or bigger bounding box.
- For production, **store your API key securely** (see [Streamlit secrets guide](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)).

---

## 📊 Bivariate Legend

|                | Low Intensity | High Intensity |
|----------------|--------------|---------------|
| **Low Freq**   | Pale         | Blue          |
| **High Freq**  | Purple       | Black         |

- **Hex height:** Frequency (fire days)
- **Hex color:** Mean brightness (intensity)

---

## 🙋‍♂️ Contact

Created for Mapathon/analytics projects.  
For help, open an issue or ask!

---

**Explore fire patterns, support science, and guide policy!**