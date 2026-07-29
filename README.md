# Entrance Snapper (QGIS Plugin)

A professional-grade spatial analysis tool to identify and refine building entrances by snapping footprints to logical road infrastructure using architectural logic. 

## Overview
Traditional urban accessibility models rely on building centroids, which skews pedestrian network calculations in dense urban environments. The Entrance Snapper solves this by procedurally generating true architectural entrance points from raw building footprints. 

Unlike standard geometric proximity tools, this plugin utilizes:

* **Cubed Road-Hierarchy Weighting:** Rather than just choosing the closest street, the tool uses a smart mathematical formula that strongly prefers placing entrances on major streets (like main roads) rather than tiny back alleys or service lanes, mirroring how real buildings are designed to face important roads.(Designed natively using the OpenStreetMap (OSM) highway hierarchy dictionary to ensure seamless, out-of-the-box compatibility worldwide).

* **Shared-Wall Filtering:**  Uses a spatial check to make sure entrance points are never accidentally placed on shared party walls between connected houses (a common issue in terraced streets), ensuring doors always face the outside street.

* **Local Tangency Rectification:** A manual fine-tuning tool that helps researchers lock onto tricky, curved street layouts (like crescents or cul-de-sacs) to make sure building entrances line up perfectly with the curve of the road.

* **Important Note on Road Hierarchy Data:**

While the tool is built around the OSM highway classification dictionary for global compatibility, users working with alternative local or national transport datasets (e.g., Ordnance Survey MasterMap / Digimap) must ensure their road network attribute tables are mapped or reclassified to match standard hierarchy rankings (or equivalent numeric scales). Aligning your local dataset columns to match the OSM dictionary logic is essential for the cubed-hierarchy weighting formula to compute accurate, high-fidelity frontages.

## Installation
This plugin is self-contained and requires no external Python dependencies. 

1. Open QGIS 3.x.
2. Go to **Plugins > Manage and Install Plugins > All > Entrance Snapper**.
3. Select the option and proceed by clicking the **Install Plugin** button and its done, check for the dot icon appearing on the toolbar dashboard and you are all set!.

## Usage

* **Automated Plotting:** Designed for city-scale datasets (e.g., Manchester City Dataset). Select your Building Footprint and Road Network layers. Processes features in highly optimized batches of 5,000, ensuring 100% building coverage via a tiered search radius (12m to 150m).

**ENTRANCE SNAPPER TOOL**

General:

**Automated Plotting (Inputs):**

The batch processing algorithm requires the following parameters to execute the "Full Coverage" logic:

Building Layer: A polygon vector layer containing building footprints.
Road Layer: A line vector layer representing the transport network, utilized for hierarchy weighting. **(OSM Road network layer preferred since the tool is designed on OSM's Road network Hierarchy logic since its extensively available globally)**
Minimum Area [in Square Meters] (Optional): A numerical filter to exclude minor structures (sheds, outbuildings) from the snapping process.
Attribute Mapping (Optional): Three dropdowns allow you to map existing Building IDs, Road Names, and Road Hierarchy classifications directly to the newly generated points.

<p align="center">
  <img src="images/Screenshot 2026-06-16 094652.png" width="700" alt="Automated Plotting Interface Inputs">
</p>

**How to use Automated Plotting:**

1. Select your Building Layer (polygon footprints) and Road Layer (line network) from the dropdown menus.
2. (Optional) Enter a Minimum Area (sq meters) to automatically exclude minor structures like garden sheds or detached garages from the snapping process.
3. (Optional) Map your Building ID, Road Name, and Road Hierarchy fields. Note: If the Hierarchy field is left blank, the tool will disable the cubed-weighting math and run a pure shortest-distance proximity snap.
4. Click Generate. The tool will process the features in batches using architectural logic (Cubed Hierarchy Weighting and Shared-Wall Filtering).

<p align="center">
  <img src="images/Screenshot 2026-06-16 094831.png" width="700" alt="Automated Plotting Interface In Process">
</p>

<p align="center">
  <img src="images/Screenshot 2026-06-16 095348.png" width="700" alt="Automated Plotting Interface Output">
</p>

**Manual Rectifier (Inputs):**

The "Human-in-the-loop" tool for precision refinement of automated outputs:
Entrance Layer: The point layer generated during the automated phase that requires refinement.
Building Layer: The reference footprint layer used to identify parallel wall segments.
Road Layer: The target infrastructure used to calculate the "longest parallel face" for entrance alignment.

**How to use the Manual Rectifier:**

1. Select the specific Entrance Point layer, Building layer, and Road layer from the dropdowns.
2. Using the QGIS 'Select Features' tool, highlight ONE building and ONE adjacent curved road segment on the map canvas.
3. Click Run. The tool will calculate the local curve of the selected road and perfectly align the building's entrance point to face it.
4. When finished, click Close to save or discard your changes to the map.

<p align="center">
  <img src="images/Screenshot 2026-06-16 095500.png" width="700" alt="Manual Rectification Interface Input">
</p>

**Output:**

A new Point Layer will be added to your QGIS project containing the generated entrances, complete with the relational attributes entrance_id, bldg_ref (mapped Building ID), and, optionally, road_ref and road_rank.
* **Manual Rectifier:** A "human-in-the-loop" tool for complex architectural layouts. Select specific curved road segments and the tool automatically aligns the nearest building entrances to that exact local tangency.

<p align="center">
  <img src="images/Screenshot 2026-06-16 095650.png" width="700" alt="Manual Rectification Interface Input">
</p>

**Known Limitations (Edge Cases Requiring Manual Rectification)**

While the Automated Plotting algorithm achieves a high success rate using Cubed Road-Hierarchy Weighting and Shared-Wall Consensus, certain complex architectural geometries will always require human-in-the-loop intervention via the Manual Rectifier. Users should visually review datasets for the following known architectural restrictions:

Deep Architectural Indents & Courtyards: If a primary entrance is recessed deeply into a building's footprint (e.g., an alcove or U-shaped courtyard), the algorithm will naturally snap to the protruding front-facing walls, as they are mathematically closer to the road vector.

Large Corner Chamfers: On junction plots, buildings often feature large angled corner walls (chamfers). If this chamfer wall is wide enough, the algorithm may favor it over the primary address street, incorrectly placing the entrance on the corner vertex rather than the main facade.

Multi-Frontage Ambiguity: For large commercial or residential blocks bordered by equally ranked roads (e.g., bordered by two 'residential' roads), the algorithm cannot deduce the "true" postal address. It will snap to the facade with the shortest geometric distance, which may occasionally be the rear of the property.

Sweeping Curves & Crescents: On heavily curved roads (cul-de-sacs, crescents), straight-line polygon generalizations of building footprints may cause automated points to drift. The Manual Rectifier is required here to calculate the exact Local Tangency and force perpendicular alignment.

## License
This project is licensed under the GNU General Public License v3.0 - see the `LICENSE` file for details.

**Developed under the Manchester Metropolitan University (MMU) Research Accelerator Grant, Project ID 5121135 (PI: Kristen Zhao).**
