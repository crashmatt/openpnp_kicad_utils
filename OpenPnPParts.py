'''
Created on Jun 27, 2020

@author: matt
'''

import xmltodict
from pathlib import Path
import os
from lxml import etree
import numpy as np
from posix import mkdir
import qrcode

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

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
    
  def makeQRCodes(self):
    for part in self.parts:
      part_id = part["@id"]
      
      qr = qrcode.QRCode(
          version=None,
          error_correction=qrcode.constants.ERROR_CORRECT_M,
          box_size=4,
          border=4,
      )
      
      qr.add_data(part_id)
      qr.make(fit=True)

      img = qr.make_image(fill_color="black", back_color="white")
      
      part["qrc_img"] = img
      
  def resizeQRCodes(self, scale):
    for part in self.parts:
      qrc_img = part["qrc_img"]
      width, height = qrc_img.size
      
      width = int(width * scale)
      height = int(height * scale)
      
      qrc_img = qrc_img.resize( (width, height) )
      part["qrc_img"] = qrc_img
      
  def addQRCodeTitle(self):
    for part in self.parts:
      part_id = part["@id"]
      qrc_img = part["qrc_img"]
      qrc_width, qrc_height = qrc_img.size
      
#       font = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 12)
#       font = ImageFont.load_default()
#       font = ImageFont(font, )
      font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", 16)
      textwidth, textheight = font.getsize(part_id)
      
      new_width = int(qrc_width + (textwidth * 1.2))
      
      newimg = Image.new(qrc_img.mode, (new_width, qrc_height), "white")
      
      newimg.paste(qrc_img, (0,0))
      
      text_hpos = int(qrc_width + (textwidth/10))
      text_vpos = int( (qrc_height-textheight)/2 )
      draw = ImageDraw.Draw(newimg)
      
      draw.text( (text_hpos, text_vpos), part_id, font=font)
      
      part["qrc_img"] = newimg

  def saveQRCodeIMages(self):
    qr_directory = os.path.join( os.getcwd(), "OpenPnpPartQRCodes")
    if not os.path.exists(qr_directory):
      os.mkdir(qr_directory)

    for part in self.parts:
      part_id = part["@id"]
      part_filename = part_id + ".png"
      #replace directory characters
      part_filename = part_filename.replace("/", "-")
      part_filename = part_filename.replace("\\", "-")
      part_path = os.path.join(qr_directory, part_filename)

      part["qrc_img"].save(part_path)

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
   
   
def main():
  open_pnp_parts = OpenPnPParts()
  open_pnp_parts.makeQRCodes()
  open_pnp_parts.resizeQRCodes(0.25)
  open_pnp_parts.addQRCodeTitle()
  open_pnp_parts.saveQRCodeIMages()
   
if __name__ == '__main__':
    main()
    
    