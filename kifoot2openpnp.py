'''Created on Jun 27, 2020

@author: matt
'''

from pathlib import Path
import os
from pcb.kicad_mod import KicadMod
from tkinter import filedialog
import configparser
from OpenPnPParts import *
from _struct import pack


# class KiCadMod2OpenbPnPConverter():
#   def __init__(self, kicadmod):
#     self.max_x = 0
#     self.min_x = 0
#     self.max_y = 0
#     self.min_y = 0
#       
#     for mod_line in kicadmod.lines:
#       self._check_pt_extents(mod_line["start"]["x"], mod_line["start"]["y"])
#       self._check_pt_extents(mod_line["end"]["x"], mod_line["end"]["y"])
#       
#     print("max_x", self.max_x)  
#     print("min_x", self.min_x)  
#     print("max_y", self.max_y)  
#     print("min_y", self.min_y)  
#     
#   def _check_pt_extents(self, x, y):
#     if x > self.max_x:
#       self.max_x = x
#     if x < self.min_x:
#       self.mn_x = x
#     if y > self.max_x:
#       self.max_x = x
#     if y < self.min_y:
#       self.min_y = y

      
      
def main():
    config = configparser.ConfigParser()
    
    default_directory = os.getcwd()
    config['DEFAULT'] = {"kicad_mod_directory": default_directory}
    config['DEFAULT']["package_alias_file"] = os.path.join(os.getcwd(), "openpnp_package_alias.csv")
    config['DEFAULT']["size_extents_layer"] = "F.Fab"
    
    config.read("config.ini")    
    initial_directory = config['DEFAULT']["kicad_mod_directory"]
    package_alias_file = config['DEFAULT']["package_alias_file"]
    size_extents_layer = config['DEFAULT']["size_extents_layer"]

#     kicadmod_file_path = filedialog.askopenfilename(filetypes=[("KiCAD mod file", ".kicad_mod")], initialdir=initial_directory)
    kicadmod_file_paths = filedialog.askopenfilenames(filetypes=[("KiCAD mod file", ".kicad_mod")], initialdir=initial_directory)

    if len(kicadmod_file_paths) == 0:
      print("No file selected")
      return


    package_aliases = Aliases(package_alias_file).aliases
        
    packages = OpenPnPPackagesXML()
    
    for kicadmod_file_path in kicadmod_file_paths:
          
      kicadmod_file_path = Path(kicadmod_file_path)
      new_directory = kicadmod_file_path.parent
      
      config['DEFAULT']["kicad_mod_directory"] = str(new_directory)

      kicadmod = KicadMod(kicadmod_file_path)        
      packages.insertKiCadModPads(kicadmod, package_alias=package_aliases)

              
    export_packages_path = Path(packages_filepath_default)
    export_packages_path = export_packages_path.with_name("kicad_export_packages.xml")
    packages.exportPackages(export_packages_path)

    with open('config.ini', 'w') as configfile:
      config.write(configfile)


if __name__ == '__main__':
    main()
    
    pass