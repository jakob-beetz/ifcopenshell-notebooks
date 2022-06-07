import os
import random
from OCC.Display.WebGl.jupyter_renderer import JupyterRenderer, format_color, NORMAL, BoundingBox
from ipywidgets import interact, interactive, fixed, interact_manual, IntSlider, Layout, FloatSlider
import ipywidgets as widgets

import OCC.Core, OCC.Core.gp
import ifcopenshell, ifcopenshell.geom
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeSphere
from pythreejs import Plane


class JupyterIFCRenderer(JupyterRenderer):
    colors_dict = { "IfcWall": (50,50,50)}


    def __init__(self,
                model,
                display_ents = ["IfcProduct"], 
                hide_ents = ["IfcOpeningElement", "IfcSpace"],
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
        
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_PYTHON_OPENCASCADE, True)
        super().__init__(size=size,compute_normals_mode=compute_normals_mode)
        self.register_select_callback(self.ifc_element_click)
        
       
        to_display = [] 
        for ent in display_ents:
            to_display.extend(model.by_type(ent, True))
        # print(display_ents)
        self.shapedict = {}
        self.elementdict = {}
        self._meshdict = {}
        self.colorcache = {}
        self.highlight_color = "#EE2222"
        schema = model.wrapped_data.schema
        # print(to_display)
        
        for product in to_display:
            # some IfcProducts don't have any 3d representation
            if (product.Representation is not None ) :  

                pdct_shape = ifcopenshell.geom.create_shape(settings, inst=product)
                r,g,b,alpha = pdct_shape.styles[0] # the shape color
                # Styles come as floats 0 <= style <= 1
                if r == g == b == -1:
                    r = b = g = 0.7
                color = format_color(int(abs(r)*255),int(abs(g*255)),int(abs(b)*255))
               
                self.shapedict[pdct_shape.geometry]=product
                self.elementdict[product] = pdct_shape.geometry
                self.colorcache[pdct_shape.geometry] = color
                
                # any renderer (threejs, x3dom, jupyter, qt5 based etc.)
                self.DisplayShape(pdct_shape.geometry, shape_color = color, transparency=False, opacity=0.5)
#               
        for ent in hide_ents:
            to_hide = model.by_type(ent)
            for p in to_hide:
                self.setVisible(p, False)
        
        for meshid, shape in self._shapes.items():
            product = self.shapedict[shape] 
            #self._meshdict[product] = meshid
            self._meshdict[product] = list(filter(lambda mesh: mesh.name == meshid, self._displayed_pickable_objects.children))[0]
        
        if self._shapes:
            self._bb = BoundingBox([self._shapes.values()])
        else:  # if nothing registered yet, create a fake bb
            self._bb = BoundingBox([[BRepPrimAPI_MakeSphere(5.).Shape()]])
        
        self._sectionXSlider = FloatSlider(name = "section plane X", layout=Layout(width='200px'), min=self._bb.ymin-1, max=self._bb.ymax+1, value=self._bb.ymax+1,step=0.1)
        self._sectionXSlider.observe(self._sectionPlaneX, "value")
        self._sectionXSliderW = widgets.HBox([widgets.Label(value="X section"),self._sectionXSlider])
        self._controls.append(self._sectionXSliderW)

        self._sectionZSlider = FloatSlider(name = "section plane Z", layout=Layout(width='200px'), min=self._bb.zmin-1, max=self._bb.zmax+1, value=self._bb.zmax+1,step=0.1)
        self._sectionZSlider.observe(self._sectionPlaneZ, "value")
        self._sectionZSliderW = widgets.HBox([widgets.Label(value="Z section"), self._sectionZSlider])
        self._controls.append(self._sectionZSliderW)
    
        self._controls = (widgets.VBox(children=self._controls[:3]),widgets.VBox(children=self._controls[3:6]),widgets.VBox(children=self._controls[6:]))
        
    def ifc_element_click(self, value):
        # ("element click")
        # self.html.value(self, value)
        #print("click")
        product = self.shapedict[value]
        self.html.value += f"<b>{product.is_a()}</b><br>"
        self.html.value += "<table>"
        
        for key, value in  product.get_info().items():
            
            self.html.value += f"<tr><td><b>{str(key)}</b>:</td><td> {str(value)}</td></tr>"
    
        self.html.value += "</table>"
        
        
    def setColorSelected(self, color):
        # for key, val in self.shapedict.items():
            # if val == element:
        # TODO : multiple selection
        # for shp in self._current_shape_selection:
        shp = self._current_shape_selection
        # print(self._current_shape_selection.colors)
        #print(self._current_mesh_selection.material.color)
        self._current_mesh_selection.material.color = color
        # self.DisplayShape(shp, shape_color = format_color(*color), transparency=False, opacity=0.5)

    
    def setHighlighColor(self, color):
        self.hl = color
        
    def highlightShape(self, element):
        shape = list(self.shapedict.keys())[list(self.shapedict.values()).index(element)]
        color=format_color(166, 166, 166)
#         self.DisplayShape(shape, shape_color = color, transparency=False, opacity=0.5)
        
        
#     def changeColor(self, element, color):
#         for self.elementdict.values
    
    def resetHighlight(self):
        for p, c in self.colorcache.items():
            self.DisplayShape(p, shape_color = c)
            
    def setColorProduct(self, product, color):
        
        mesh = self._meshdict.get(product, None)
        if mesh:
            mesh.material.color = color
        
#         for shp in self._displayed_pickable_objects.children:
            # if self.elementdict[product]
            # print (f"Shape: {shp} \t\t\t\t {product}" )
            # if self._shapedict 
            

    def setAllTransparent(self):
        for shp in self._displayed_pickable_objects.children:
            shp.material.opacity = 0.0001
            shp.material.transparent = True
            shp.material.alpha = 0.1
    
    def setTransparentTrue(self, product):
        mesh = self._meshdict.get(product, None)
        if mesh:    
            #print(mesh)
            mesh.material.opacity = 0.1
            mesh.transparent = True
            mesh.material.alpha = 0.1
            
    def setTransparentFalse(self, product):
        mesh = self._meshdict.get(product, None)
        if mesh:    
            #print(mesh)
            mesh.material.opacity = 1
            mesh.transparent = False
            mesh.material.alpha = 1

        

    def resetTransparency (self, product):
        mesh = self._meshdict.get(product, None)
        if mesh:
            mesh.material.opacity = 1
            mesh.transparent = False
            mesh.material.alpha = 1
    
    def setColor(self, product, color):
        mesh = self._meshdict.get(product, None)
        if mesh:    
            #print(mesh)
            mesh.material.color = color
            
    
    def setVisible(self, product, visible):
        mesh = self._meshdict.get(product, None)
        if mesh:    
            #print(mesh)
            mesh.visible = visible 
    
    
    def highlight(self, product):
        mesh = self._meshdict.get(product, None)
        if mesh:    
            #print(mesh)
            mesh.material.color = self.highlight_color
    
    def __repr__(self):
        self.Display()
        return ""
    
    def _sectionPlaneX(self, x):
            self._renderer.localClippingEnabled = True;
            self._renderer.clippingPlanes = [Plane((0,-1,0), x['new'])]
            
    def _sectionPlaneZ(self, z):
            self._renderer.localClippingEnabled = True;
            self._renderer.clippingPlanes = [Plane((0,0,-1), z['new'])]
                
                
    def getSelectedProduct(self):
        shp = self._current_shape_selection
        product = self.shapedict.get(shp, None)
        return product
    
    
    def setDefaultColors(self):
        for p,m  in self._meshdict.items():
            if p.is_a() in self._COLOR_MAPPINGS.keys():
                #print(f"{p.Name}, {p.is_a()} \t\t\t  {self.DEFAULT_COLORS.get(self.COLOR_MAPPINGS.get(p.is_a()))}")
                m.material.color = self._DEFAULT_COLORS.get(self._COLOR_MAPPINGS.get(p.is_a()),"#333333")
            else:
                m.material.color = "#AAAAAA"
                                                    
    def colorPicker(self):
        return widgets.ColorPicker(
            concise=False,
            description='Pick a color',
            value='blue',
            disabled=False
        )
        
        
    _DEFAULT_COLORS = {
        'dark-electric-blue': '#527589',
        'little-boy-blue' : '#64a1ec',
        'black-coral' : '#525e71',
        'space-cadet' : '#272d3f',
        'brown-sugar' : '#be7752',
        'pale-silver' : '#c0bab1',
        'imperial-red' : '#e63946',
        'honeydew' : '#f1faee',
        'powder-blue' : '#a8dadc',
        'celadon-blue' : '#457b9d',
        'prussian-blue' : '#1d3557',
        'Khaki Web' : '#C6AC8F'
    }
    _COLOR_MAPPINGS = {
        'IfcWall' : 'pale-silver',
        'IfcWallStandardCase' : 'pale-silver',
        'IfcWindow' : 'celdon-blue',
        'IfcFloor' : 'brown-sugar',
        'IfcSlab' : 'Khaki Web',
        'IfcDoor' : 'honeydew'
        
    }
