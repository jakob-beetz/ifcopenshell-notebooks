


[![DOI](https://zenodo.org/badge/383424760.svg)](https://zenodo.org/badge/latestdoi/383424760)


[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jakob-beetz/ifcopenshell-binder/main?urlpath=git-pull%3Frepo%3Dhttps%253A%252F%252Fgithub.com%252Fjakob-beetz%252Fifcopenshell-notebooks%26urlpath%3Dlab%252Ftree%252Fifcopenshell-notebooks%252F00_introduction.ipynb%26branch%3Dmain)


![screenshot of jupyter=notebook](img/screenshot-ifc-notebook.png)


# ifcopenshell-notebooks
Interactive Jupyter Notebooks to teach working with IFC files using ifcopenshell with python.

These Notebooks are part of mandatory classes for Bachelor students of [Architecture at the RWTH Aachen University](https://arch.rwth-aachen.de/go/id/gfa/) and have advanced versions for MSc levels. The notebooks usually run on the [Jupyter Hub of the RWTH Aachen](https://jupyter.rwth-aachen.de) but can be run on other Jupyter Notebook VMs.
They are published as [Open Educational Resources](https://en.unesco.org/themes/building-knowledge-societies/oer) 

<img src="https://upload.wikimedia.org/wikipedia/commons/2/20/Global_Open_Educational_Resources_Logo.svg" width="200"/>



To run the notebooks interactively, click the binder link above, a few seconds patience and you will be able to enjoy:
- Integrated IFC Viewer with bidirectional ability to 
  - select from script, get selection from mouse to script
  - see attributes of building element instances 
  - set visibility, colors and transparancy from script
- display model structure using GraphViz Dot
![dot vizualization](img/ifc-graph-plot.png)
- Browse IFC 2x3 and IFC 4 documentation right in your notebook `IfcHelp.getHelp3("IfcDoor")` 
![documentation in browser](img/ifchelp-example-ifcdoor.png)
- use pandas, numpy etc. to do calculations on models
- reach through to the powerfull OpenCascadeKernel

If you like the work, please
- cite it, please use this DOI [![DOI](https://zenodo.org/badge/383424760.svg)](https://zenodo.org/badge/latestdoi/383424760)
- sponsor [aothms](https://github.com/aothms) and [tpaviot](https://github.com/tpaviot/) whose great work this is based upon
- write s.th. into the forum, add a pull request
- help improve it!
- come to RWTH to study with us!
- more ideas are welcome
