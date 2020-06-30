'''
Created on Jun 27, 2020

@author: matt
'''

import xmltodict
from pathlib import Path
import os
from lxml import etree
import numpy as np

parts_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "parts.xml"))
packages_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "packages.xml"))


class Aliases():
  def __init__(self, alias_filepath):
    #Read and parse alias file
    with open(alias_filepath, "r") as alias_file:
      alias_lines = alias_file.readlines()
    
    aliases = {}
    for alias_line in alias_lines:
      alias_splits = alias_line.rstrip().split(",")
      original = str(alias_splits[0])
      alias = str(alias_splits[1])
      
      aliases[original] = alias
          
    self.aliases = aliases
    

class PackageAdjustments(): 
  def __init__(self, adjustment_filepath):
    #Read and parse adjustment file
    with open(adjustment_filepath, "r") as adjustment_file:
      adjustment_lines = adjustment_file.readlines()
    
    adjustments = {}
    for adjustment_line in adjustment_lines:
      alias_splits = adjustment_line.rstrip().split(",")
      if len(alias_splits) >= 3:
        package_id = str(alias_splits[0])
        x_offset = float(alias_splits[1])
        y_offset = float(alias_splits[2])
        
        adjustment = {}
        adjustment["x_offset"] = x_offset
        adjustment["y_offset"] = y_offset
        adjustments[package_id] = adjustment
          
    self.adjustments = adjustments
  
    

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
    
    
class OpenPnPPackagesXML():    
  def __init__(self, packages_filepath=packages_filepath_default ):
    self.packages_tree = etree.parse(str(packages_filepath))
    
    header_element = self.packages_tree.xpath("/openpnp-packages")
    if len(header_element) == 0:
      print("openpnp xml does not contain expected header")

  def exportPackages(self, export_path):
    xml = etree.tostring(self.packages_tree, pretty_print=True)
    
    with open(export_path, "wb") as export_file:
      export_file.write(xml)
      
  def getPackageIDs(self):
    pacakge_ids = []
    for package_element in self.packages_tree.iter("package"):
      pacakge_ids.append(package_element.get("id"))
    return pacakge_ids
    
  def insertKiCadModPads(self, kicad_mod, package_alias=None, extents_layer="", overwrite=False):
    
    kicad_package_id = kicad_mod.name
    if package_alias:
      if kicad_package_id in package_alias:
        kicad_package_id = package_alias[kicad_package_id]
        print("Changed package id to alias:" , kicad_package_id)
        
    
    for package_element in self.packages_tree.iter("package"):
      package_element_id = package_element.get("id")
      if package_element_id == kicad_package_id:
        print("Found package element: ", package_element_id)
           
        pad_elements = package_element.xpath("./footprint/pad")
        if len(pad_elements) > 0:
          print("openpnp package has pas definition already.  Will not overwrite.  Do manual pad definition removal")
          return False

        print("openpnp package %s has no previous pad definition" % kicad_package_id)
 
#         footprint_element = package_element.xpath("./footprint")
        footprint_element = package_element.find("footprint")
    
        for kicad_pad in kicad_mod.pads:
          pad_attribs =  {}
          pad_attribs["name"] = str(kicad_pad["number"])
          pad_attribs["x"] = str(kicad_pad["pos"]["x"])
          pad_attribs["y"] = str(kicad_pad["pos"]["y"])
          pad_attribs["width"] = str(kicad_pad["size"]["x"])
          pad_attribs["height"] = str(kicad_pad["size"]["y"])
          pad_attribs["rotation"] = str(kicad_pad["pos"]["orientation"])
          pad_attribs["roundness"] = str(0.0)
          pad_element = etree.SubElement(footprint_element, "pad", pad_attribs)
          
        line_pts = np.zeros([0,2])
        for kicad_line in kicad_mod.lines:
          if extents_layer == ""  or kicad_line["layer"] == extents_layer:
            new_pt = np.array([[kicad_line["start"]["x"], kicad_line["start"]["y"]],]) 
            line_pts = np.append(line_pts, new_pt, axis = 0)
            new_pt = np.array([[kicad_line["end"]["x"], kicad_line["end"]["y"]],])
            line_pts = np.append(line_pts, new_pt, axis = 0)
            
        if line_pts.shape[0] > 4:
          max_x = np.max(line_pts[:,0])
          max_y = np.max(line_pts[:,1])
          min_x = np.min(line_pts[:,0])
          min_y = np.min(line_pts[:,1])          
        
          print("Got package extents")
          print("min_x:", max_x)
          print("max_x:", max_x)
          print("min_y:", min_y)
          print("max_y:", max_y)
          
          body_width = max_x - min_x
          body_height = max_y - min_y
          
          footprint_atttribs = footprint_element.attrib
          footprint_atttribs["body-width"] = str(body_width)
          footprint_atttribs["body-height"] = str(body_height)
          print(footprint_atttribs)
                
        else:
          print("Not enough line information, can't set package extents")
          return False

        return True

#       else:
#         print("kicad package:%s did not match openpnp package:%s" %(kicad_package_id, package_element_id))
      
    print("Package_id: %s not found" % kicad_package_id)
    return False
        
  def _check_pt_extents(self, x, y):
    if x > self.kicadmod_max_x:
      self.kicadmod_max_x = x
    if x < self.kicadmod_min_x:
      self.kicadmod_min_x = x
    if y > self.kicadmod_max_x:
      self.kicadmod_max_x = x
    if y < self.kicadmod_min_y:
      self.kicadmod_min_y = y
   
     
    