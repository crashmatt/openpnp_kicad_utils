'''
Created on Jun 27, 2020

@author: matt
'''

import xmltodict
import dicttoxml
from pathlib import Path
import os

parts_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "parts.xml"))
packages_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "packages.xml"))


class OpenPnPParts():
  def __init__(self, parts_filepath=parts_filepath_default):
    with open(parts_filepath, "rb") as parts_file:
      parts_filedata = parts_file.read()
      
    self.openpnp_parts = xmltodict.parse(parts_filedata)
    
    self.parts = self.openpnp_parts["openpnp-parts"]["part"]    
    print(self.parts)
    
    part_id_dict = {}
    for part in self.parts :
      part_id = part["@id"]
      part_id_dict[part_id] = part
    self.part_id_dict = part_id_dict
      

class OpenPnPPackages():
  def __init__(self, packages_filepath=packages_filepath_default):
    with open(packages_filepath, "rb") as packages_file:
      packages_filedata = packages_file.read()

    self.openpn_packages = xmltodict.parse(packages_filedata)
    self.packages = self.openpn_packages["openpnp-packages"]["package"]
    print(self.packages)

    package_id_dict = {}
    for package in self.packages:
      package_id_dict[package["@id"]] = package
    self.package_id_dict = package_id_dict
    
  def insertKiCadModPads(self, kicad_mod, overwrite=False):
    package_id = kicad_mod.name
    if package_id not in self.packages:
      print("kicad module name not in openpnp packages")
      return False
    
    package = self.packages[package_id]

#     if "pad" in package["footprint"]:
#       if overwrite == False:
#         return False

    if "pad" in package["footprint"]:
      print("No overwriting existing openpnp part pads")
      
    for kicad_pad in kicad_mod.pads:
      openpnp_pad = {}
      openpnp_pad["name"] = kicad_pad["number"]
      openpnp_pad["x"] = kicad_pad["pos"]["x"]
      openpnp_pad["y"] = kicad_pad["pos"]["y"]
      openpnp_pad["rotation"] = kicad_pad["pos"]["orientation"]
      

      
  def __check_pt_extents(self, x, y):
    if x > self.kicadmod_max_x:
      self.kicadmod_max_x = x
    if x < self.kicadmod_min_x:
      self.kicadmod_min_x = x
    if y > self.kicadmod_max_x:
      self.kicadmod_max_x = x
    if y < self.kicadmod_min_y:
      self.kicadmod_min_y = y
  
    
  def exportPackages(self, export_path):
    xml = dicttoxml.dicttoxml(self.packages)
    with open(export_path, "wb") as export_file:
      export_file.write(xml)
    