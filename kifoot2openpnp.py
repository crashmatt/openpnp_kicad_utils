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


class KiCadMod2OpenbPnPConverter():
  def __init__(self, kicadmod):
    self.max_x = 0
    self.min_x = 0
    self.max_y = 0
    self.min_y = 0
      
    for mod_line in kicadmod.lines:
      self._check_pt_extents(mod_line["start"]["x"], mod_line["start"]["y"])
      self._check_pt_extents(mod_line["end"]["x"], mod_line["end"]["y"])
      
    print("max_x", self.max_x)  
    print("min_x", self.min_x)  
    print("max_y", self.max_y)  
    print("min_y", self.min_y)  
    
  def _check_pt_extents(self, x, y):
    if x > self.max_x:
      self.max_x = x
    if x < self.min_x:
      self.mn_x = x
    if y > self.max_x:
      self.max_x = x
    if y < self.min_y:
      self.min_y = y

      
      
def main():
    config = configparser.ConfigParser()
    
    default_directory = os.getcwd()
    config['DEFAULT'] = {"directory": default_directory}
    
    config.read("config.ini")    
    
    initial_directory = config['DEFAULT']["directory"]

    kicadmod_file_path = filedialog.askopenfilename(filetypes=[("KiCAD mod file", ".kicad_mod")], initialdir=initial_directory)

    if not kicadmod_file_path:
      return
    
    kicadmod_file_path = Path(kicadmod_file_path)
    new_directory = kicadmod_file_path.parent
    
    config['DEFAULT']["directory"] = str(new_directory)
    
    with open('config.ini', 'w') as configfile:
      config.write(configfile)
      
    kicadmod = KicadMod(kicadmod_file_path)
        
    packages = OpenPnPPackages()
    
#     packages.insertKiCadMod(kicadmod)
    
    export_packages_path = Path(packages_filepath_default)
    export_packages_path = export_packages_path.with_name("kicad_export_packages.xml")
    packages.exportPackages(export_packages_path)

if __name__ == '__main__':
    main()
    
    pass