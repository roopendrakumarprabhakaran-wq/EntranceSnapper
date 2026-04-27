# Entrance Snapper (QGIS Plugin)

A professional-grade spatial analysis tool to identify and refine building entrances by snapping footprints to logical road infrastructure using architectural logic. 

**Developed under the Manchester Metropolitan University (MMU) Research Accelerator Grant, Project ID 5121135 (PI: Kristen Zhao).**

## Overview
Traditional urban accessibility models rely on building centroids, which skews pedestrian network calculations in dense urban environments. The Entrance Snapper solves this by procedurally generating true architectural entrance points from raw building footprints. 

Unlike standard geometric proximity tools, this plugin utilizes:
* **Cubed Road-Hierarchy Weighting:** Prioritizes primary roads over service paths `(7 - r_rank)^3`.
* **Shared-Wall Filtering:** Uses spatial indexing (`QgsSpatialIndex`) to prevent entrance placement on internal/party walls.
* **Local Tangency Rectification:** Allows researchers to identify specific vertex-to-vertex road segments to solve complex curved road geometries.

## Installation
This plugin is self-contained and requires no external Python dependencies. 

1. Download the latest `Entrance_Snapper.zip` release.
2. Open QGIS 3.x.
3. Go to **Plugins > Manage and Install Plugins > Install from ZIP**.
4. Select the downloaded `.zip` file and click **Install**.

## Usage
* **Automated Plotting:** Designed for city-scale datasets (e.g., Manchester City Dataset). Select your Building Footprint and Road Network layers. Processes features in highly optimized batches of 5,000, ensuring 100% building coverage via a tiered search radius (12m to 150m).
Entrance Snapper Tool
General:

**Automated Plotting (Inputs):**
The batch processing algorithm requires the following parameters to execute the "Full Coverage" logic:

Building Layer: A polygon vector layer containing building footprints.
Road Layer: A line vector layer representing the transport network, utilized for hierarchy weighting.
Minimum Area [in Square Meters] (Optional): A numerical filter to exclude minor structures (sheds, outbuildings) from the snapping process.
Attribute Mapping (Optional): Three dropdowns allow you to map existing Building IDs, Road Names, and Road Hierarchy classifications directly to the newly generated points.

**How to use Automated Plotting:**

1. Select your Building Layer (polygon footprints) and Road Layer (line network) from the dropdown menus.
2. (Optional) Enter a Minimum Area (sq meters) to automatically exclude minor structures like garden sheds or detached garages from the snapping process.
3. (Optional) Map your Building ID, Road Name, and Road Hierarchy fields. Note: If the Hierarchy field is left blank, the tool will disable the cubed-weighting math and run a pure shortest-distance proximity snap.
4. Click Generate. The tool will process the features in batches using architectural logic (Cubed Hierarchy Weighting and Shared-Wall Filtering).

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

**Output:**

A new Point Layer will be added to your QGIS project containing the generated entrances, complete with the relational attributes entrance_id, bldg_ref (mapped Building ID), and, optionally, road_ref and road_rank.
* **Manual Rectifier:** A "human-in-the-loop" tool for complex architectural layouts. Select specific curved road segments and the tool automatically aligns the nearest building entrances to that exact local tangency.

## License
This project is licensed under the GNU General Public License v3.0 - see the `LICENSE` file for details.
