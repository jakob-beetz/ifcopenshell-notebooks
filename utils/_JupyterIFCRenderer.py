import os
import random
from OCC.Display.WebGl.jupyter_renderer import JupyterRenderer, format_color, NORMAL
import OCC.Core, OCC.Core.gp
import ifcopenshell, ifcopenshell.geom


class JupyterIFCRenderer(JupyterRenderer):
    colors_dict = { "IfcWall": (50,50,50)}


    def __init__(self,
                model,
                display_ents = ["IfcProduct", "IfcWall"], 
                hide_ents = ["IfcOpening", "IfcFurnitureElement"],
                size=(640, 480),
                compute_normals_mode=NORMAL.CLIENT_SIDE,
                default_shape_color=format_color(166, 166, 166), # light grey
                default_edge_color=format_color(32, 32, 32), # dark grey
                default_vertex_color=format_color(8, 8, 8), # darker grey
                pick_color=format_color(232, 176, 36), # orange
                background_color='white'):
        """ Creates a jupyter renderer for IFCFiles.
        model: the ifcopenshell model to be displayed
        size: a tuple (width, height). Must be a square, or shapes will look like deformed
        compute_normals_mode: optional, set to SERVER_SIDE by default. This flag lets you choose the
        way normals are computed. If SERVER_SIDE is selected (default value), then normals
        will be computed by the Tesselator, packed as a python tuple, and send as a json structure
        to the client. If, on the other hand, CLIENT_SIDE is chose, then the computer only compute vertex
        indices, and let the normals be computed by the client (the web js machine embedded in the webrowser).
        * SERVER_SIDE: higher server load, loading time increased, lower client load. Poor performance client will
            choose this option (mobile terminals for instance)
        * CLIENT_SIDE: lower server load, loading time decreased, higher client load. Higher performance clients will
                            choose this option (laptops, desktop machines).
        * default_shape_color
        * default_e1dge_color:
        * default_pick_color:
        * background_color:
        """
        print("fresh init")
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_PYTHON_OPENCASCADE, True)
        super().__init__(size=size,compute_normals_mode=compute_normals_mode)
        self.register_select_callback(self.ifc_element_click)
        
        # to_display = list(map(m.by_type for p in display_ents)) 
        to_display = [] 
        # print(display_ents)
        for ent in display_ents:
            to_display.extend(model.by_type(ent))
        self.shapedict = {}
        # print(to_display)
        for product in to_display:
            if (product.Representation is not None and 
                product.is_a() not in hide_ents) :  # some IfcProducts don't have any 3d representation

        
                pdct_shape = ifcopenshell.geom.create_shape(settings, inst=product)
                r,g,b,alpha = pdct_shape.styles[0] # the shape color
                
                color = format_color(int(abs(random.random())*255), int(abs(random.random())*255), int(abs(random.random())*255))
                # color = format_color(int(r),int(g),int(b))
                
                # self.shapedict[pdct_shape.geometry]=product
                # any renderer (threejs, x3dom, jupyter, qt5 based etc.)
                self.DisplayShape(pdct_shape.geometry, shape_color = color, transparency=False, opacity=0.5)
        


    def ifc_element_click(self, value):
        # ("element click")
        # self.html.value(self, value)

        self.html.value += f"<b>Nested Relative: The Element id:</b>{self.shapedict}<br> {value}"
    #     self.html.value += f"<br>{str(self.shapedict[self._current_shape_selection])}<br/>"
    
    def setColorSelected(self, color):
        # for key, val in self.shapedict.items():
            # if val == element:
        # TODO : multiple selection
        # for shp in self._current_shape_selection:
        shp = self._current_shape_selection
        # print(self._current_shape_selection.colors)
        print(self._current_mesh_selection.material.color)
        self._current_mesh_selection.material.color = color
        # self.DisplayShape(shp, shape_color = format_color(*color), transparency=False, opacity=0.5)


    def __repr__(self):
        self.Display()
        return ""



