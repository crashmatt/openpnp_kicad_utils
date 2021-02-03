'''
Copyright (c) 2021, Matthew Coleman

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of openpnp_kicad_utils nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import xmltodict
from pathlib import Path
import os

from lxml import etree
import numpy as np

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
  
    

class OpenPnPPackages():
  packages_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "packages.xml"))
  
  '''
  classdocs
  '''  
  def __init__(self, packages_filepath=packages_filepath_default):
    '''
    Constructor
    '''
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
  def __init__(self, packages_filepath=OpenPnPPackages.packages_filepath_default ):
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
    
  def insertKiCadModPads(self, kicad_mod, 
                         package_alias=None, 
                         extents_layer="", 
                         overwrite=False, 
                         invert_ypos=False, 
                         invert_xpos=False, 
                         marked_pin_names=[]):
    
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

          pos_x = float(kicad_pad["pos"]["x"])
          pos_y = float(kicad_pad["pos"]["y"])
          
          if invert_xpos:
            pos_x = -pos_x
          if invert_ypos:
            pos_y = -pos_y
            
          pad_attribs["x"] = str(pos_x)
          pad_attribs["y"] = str(pos_y)
          pad_attribs["width"] = str(kicad_pad["size"]["x"])
          pad_attribs["height"] = str(kicad_pad["size"]["y"])
          pad_attribs["rotation"] = str(kicad_pad["pos"]["orientation"])
          pad_attribs["roundness"] = str(0.0)
          pad_element = etree.SubElement(footprint_element, "pad", pad_attribs)
          
          if pad_attribs["name"] in marked_pin_names:
            pin1_mark_attribs =  dict(pad_attribs)
            pin1_mark_attribs["name"] == "0"
            pin1_mark_attribs["width"] = str(float(pin1_mark_attribs["width"])*0.5)
            pin1_mark_attribs["height"] = str(float(pin1_mark_attribs["height"])*0.5)
            pad_element = etree.SubElement(footprint_element, "pad", pin1_mark_attribs)
            
            
          
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