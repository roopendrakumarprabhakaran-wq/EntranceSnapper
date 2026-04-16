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
* **Manual Rectifier:** A "human-in-the-loop" tool for complex architectural layouts. Select specific curved road segments and the tool automatically aligns the nearest building entrances to that exact local tangency.

## License
This project is licensed under the GNU General Public License v3.0 - see the `LICENSE` file for details.
