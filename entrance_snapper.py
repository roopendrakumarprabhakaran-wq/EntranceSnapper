import os.path
import math
import time
from qgis.PyQt.QtCore import QCoreApplication, QVariant, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import (QgsProject, QgsGeometry, QgsSpatialIndex, 
                       QgsFeatureRequest, QgsVectorLayer, QgsFeature, 
                       QgsPointXY, QgsField)

from .resources import *
from .entrance_snapper_dialog import EntranceSnapperDialog

class EntranceSnapper:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&Entrance Snapper Tool')
        self.first_start = True

    def tr(self, message):
        return QCoreApplication.translate('EntranceSnapper', message)

    def initGui(self):
        icon_path = ':/plugins/entrance_snapper/icon.png'
        self.add_action(icon_path, text=self.tr(u'Urban Entrance Snapper'), 
                        callback=self.run, parent=self.iface.mainWindow())

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def add_action(self, icon_path, text, callback, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        self.iface.addToolBarIcon(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def log_message(self, message):
        """Appends a timestamped message to the UI log console."""
        timestamp = time.strftime("%H:%M:%S")
        if hasattr(self.dlg, 'log_console'):
            self.dlg.log_console.appendPlainText(f"[{timestamp}] {message}")
        QCoreApplication.processEvents()

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dlg = EntranceSnapperDialog()
            
            # Core UI Connections
            self.dlg.btn_run_auto.clicked.connect(self.trigger_automated)
            self.dlg.btn_run_rect1.clicked.connect(self.trigger_rectifier)
            
            # Close and Save logic
            if hasattr(self.dlg, 'btn_close'):
                self.dlg.btn_close.clicked.connect(self.close_and_save)

            # Optional Field Mapping Connections
            if hasattr(self.dlg, 'field_cb_build_id'):
                self.dlg.build_selector_auto.layerChanged.connect(self.dlg.field_cb_build_id.setLayer)
                self.dlg.road_selector_auto.layerChanged.connect(self.dlg.field_cb_road_name.setLayer)
                self.dlg.road_selector_auto.layerChanged.connect(self.dlg.field_cb_road_rank.setLayer)
                
                self.dlg.field_cb_build_id.setLayer(self.dlg.build_selector_auto.currentLayer())
                self.dlg.field_cb_road_name.setLayer(self.dlg.road_selector_auto.currentLayer())
                self.dlg.field_cb_road_rank.setLayer(self.dlg.road_selector_auto.currentLayer())
            
        self.dlg.show()

    def close_and_save(self):
        """Handles closing the UI and prompting the user to save QGIS layer edits."""
        if hasattr(self.dlg, 'point_selector_rect'):
            p_layer = self.dlg.point_selector_rect.currentLayer()
            
            if p_layer and p_layer.isEditable():
                reply = QMessageBox.question(
                    self.dlg, 
                    "Save Changes?", 
                    "You have modified entrance points. Do you want to save these changes to the layer?", 
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    p_layer.commitChanges() 
                    self.dlg.hide()
                    self.dlg.reject()
                elif reply == QMessageBox.Discard:
                    p_layer.rollBack() 
                    self.dlg.hide()
                    self.dlg.reject()
                # If Cancel is clicked, it does nothing and stays open
            else:
                self.dlg.hide()
                self.dlg.reject()
        else:
            self.dlg.hide()
            self.dlg.reject()

    def get_angle(self, p1, p2):
        return math.degrees(math.atan2(p2.y() - p1.y(), p2.x() - p1.x())) % 180

    def trigger_automated(self):
        """Tiered Snapping Strategy with Optional Attribute Mapping & Proximity Fallback"""
        b_layer = self.dlg.build_selector_auto.currentLayer()
        r_layer = self.dlg.road_selector_auto.currentLayer()
        min_area = self.dlg.area_input.value()

        if not b_layer or not r_layer:
            QMessageBox.warning(self.dlg, "Input Error", "Select Building and Road layers.")
            return

        if hasattr(self.dlg, 'log_console'):
            self.dlg.log_console.clear()
            
        self.log_message("--- STARTING COMPREHENSIVE ANALYSIS ---")
        start_time = time.time()
        
        # Determine mapping fields if UI elements exist, else default to empty strings
        b_id_fld = self.dlg.field_cb_build_id.currentField() if hasattr(self.dlg, 'field_cb_build_id') else ""
        r_name_fld = self.dlg.field_cb_road_name.currentField() if hasattr(self.dlg, 'field_cb_road_name') else ""
        r_rank_fld = self.dlg.field_cb_road_rank.currentField() if hasattr(self.dlg, 'field_cb_road_rank') else ""

        if not r_rank_fld:
            self.log_message("No hierarchy field mapped. Defaulting to Pure Proximity snapping...")

        BATCH_SIZE = 10000  
        road_hierarchy = {"primary": 1, "secondary": 2, "tertiary": 3, "residential": 4, "unclassified": 5}
        is_metric = b_layer.crs().mapUnits() == 0 
        tiers = [30, 150] if is_metric else [0.0003, 0.0015]
        block_dist = 0.05 if is_metric else 0.0000005

        out_layer = QgsVectorLayer("Point?crs=" + b_layer.crs().toWkt(), "Comprehensive_Entrances", "memory")
        out_dp = out_layer.dataProvider()
        
        # Build dynamic fields based on user selection
        fields_to_add = [QgsField("entrance_id", QVariant.Int)]
        # Always output a building ID (either mapped or auto-generated)
        fields_to_add.append(QgsField("bldg_ref", QVariant.String) if b_id_fld else QgsField("building_id", QVariant.Int))
        
        # Only add road attribute columns if the user explicitly mapped them
        if r_name_fld: fields_to_add.append(QgsField("road_ref", QVariant.String))
        if r_rank_fld: fields_to_add.append(QgsField("road_rank", QVariant.String))
        
        out_dp.addAttributes(fields_to_add)
        out_layer.updateFields()

        self.log_message("Building Spatial Indices...")
        all_buildings_index = QgsSpatialIndex(b_layer.getFeatures())
        road_index = QgsSpatialIndex(r_layer.getFeatures())
        road_cache = {f.id(): f for f in r_layer.getFeatures()}

        final_features = []
        processed = 0
        entrance_counter = 1

        for b_feat in b_layer.getFeatures():
            processed += 1
            b_geom = b_feat.geometry()
            if b_geom.area() < min_area: continue

            found_point = None
            best_score = -1
            best_road_feat = None

            for radius in tiers:
                intersecting_roads = road_index.intersects(b_geom.boundingBox().buffered(radius))
                if not intersecting_roads: continue
                
                polygons = b_geom.asMultiPolygon()[0] if b_geom.isMultipart() else b_geom.asPolygon()
                outer_ring = polygons[0]

                for j in range(len(outer_ring) - 1):
                    p1, p2 = outer_ring[j], outer_ring[j+1]
                    seg_geom = QgsGeometry.fromPolylineXY([p1, p2])
                    midpoint = seg_geom.interpolate(seg_geom.length() / 2).asPoint()
                    
                    if len(all_buildings_index.intersects(QgsGeometry.fromPointXY(midpoint).boundingBox().buffered(block_dist))) > 1:
                        continue 

                    for r_id in intersecting_roads:
                        r_feat = road_cache[r_id]
                        r_geom = r_feat.geometry()
                        dist = seg_geom.distance(r_geom)
                        
                        # Apply hierarchy weight ONLY if a field was mapped
                        if r_rank_fld:
                            try:
                                r_type = str(r_feat[r_rank_fld]).lower()
                            except KeyError:
                                r_type = "unclassified"
                            r_rank = road_hierarchy.get(r_type, 10)
                            rank_weight = math.pow((7 - r_rank), 3.0 if b_geom.area() > 1000 else 1.0)
                        else:
                            # Pure Proximity Fallback: Weight is neutralized to 1.0
                            rank_weight = 1.0
                            
                        # Score is now either weighted or strictly dependent on distance
                        total_score = rank_weight * (1.0 / (dist + 0.1))
                        
                        if total_score > best_score:
                            best_score = total_score
                            found_point = midpoint
                            best_road_feat = r_feat
                            
                if found_point: break 

            if not found_point: 
                polygons = b_geom.asMultiPolygon()[0] if b_geom.isMultipart() else b_geom.asPolygon()
                found_point = polygons[0][0]

            # Construct attributes dynamically based on what was mapped
            f = QgsFeature(out_layer.fields())
            f.setGeometry(QgsGeometry.fromPointXY(found_point))
            
            attrs = [entrance_counter]
            
            # Map Building ID or fallback to QGIS feature ID
            if b_id_fld:
                raw_val = b_feat[b_id_fld]
                # If QGIS reads it as a float (e.g., 334.0), convert it to a clean integer string (334)
                if isinstance(raw_val, float) and raw_val.is_integer():
                    attrs.append(str(int(raw_val)))
                else:
                    attrs.append(str(raw_val))
            else:
                attrs.append(b_feat.id())
            
            # Append optional fields if they were added to the schema
            if r_name_fld: attrs.append(str(best_road_feat[r_name_fld]) if best_road_feat else "None")
            if r_rank_fld: attrs.append(str(best_road_feat[r_rank_fld]) if best_road_feat else "None")
            
            f.setAttributes(attrs)
            final_features.append(f)
            entrance_counter += 1

            if processed % BATCH_SIZE == 0:
                out_dp.addFeatures(final_features)
                final_features = []
                self.log_message(f"Processed {processed} buildings...")

        out_dp.addFeatures(final_features)
        
        # --- ENSURES POINTS RENDER IMMEDIATELY ---
        out_layer.updateExtents()
        QgsProject.instance().addMapLayer(out_layer)
        self.iface.mapCanvas().refresh()
        
        self.log_message(f"COMPLETE! Total Time: {round(time.time() - start_time, 2)}s")

    def trigger_rectifier(self):
        """Segment-Specific Manual Refinement"""
        p_layer = self.dlg.point_selector_rect.currentLayer()
        b_layer = self.dlg.build_selector_rect.currentLayer()
        r_layer = self.dlg.road_selector_rect.currentLayer()

        if not p_layer or not b_layer or not r_layer:
            self.iface.messageBar().pushMessage("Error", "Check layer selections.", level=3)
            return

        sel_buildings = list(b_layer.selectedFeatures())
        sel_roads = list(r_layer.selectedFeatures())

        if not sel_buildings or not sel_roads:
            self.iface.messageBar().pushMessage("Selection Error", "Select building AND road on map.", level=3)
            return

        target_road = sel_roads[0]
        b_center = sel_buildings[0].geometry().centroid().asPoint()
        
        analysis = target_road.geometry().closestSegmentWithContext(b_center)
        next_v_idx = analysis[2]
        line = target_road.geometry().asPolyline() if not target_road.geometry().isMultipart() else target_road.geometry().asMultiPolyline()[0]
        p_start, p_end = line[next_v_idx - 1], line[next_v_idx]
        
        chosen_seg_geom = QgsGeometry.fromPolylineXY([p_start, p_end])
        chosen_seg_angle = self.get_angle(p_start, p_end)

        if not p_layer.isEditable(): p_layer.startEditing()
        
        for b_feat in sel_buildings:
            outer_ring = (b_feat.geometry().asMultiPolygon()[0] if b_feat.geometry().isMultipart() else b_feat.geometry().asPolygon())[0]
            best_midpoint = None
            min_dist = float('inf')

            for i in range(len(outer_ring) - 1):
                p1, p2 = outer_ring[i], outer_ring[i+1]
                wall_geom = QgsGeometry.fromPolylineXY([p1, p2])
                wall_angle = self.get_angle(p1, p2)
                
                angle_diff = abs(wall_angle - chosen_seg_angle)
                if angle_diff > 90: angle_diff = 180 - angle_diff
                
                if angle_diff < 35:
                    dist = wall_geom.distance(chosen_seg_geom)
                    if dist < min_dist:
                        min_dist = dist
                        best_midpoint = wall_geom.interpolate(wall_geom.length() / 2).asPoint()

            if best_midpoint:
                for f in p_layer.getFeatures():
                    if f.geometry().distance(b_feat.geometry()) < 0.5:
                        p_layer.changeGeometry(f.id(), QgsGeometry.fromPointXY(best_midpoint))
                        break
        
        self.iface.mapCanvas().refresh()
        self.iface.messageBar().pushMessage("Success", "Point aligned to specific road segment.", level=0)
