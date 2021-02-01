'''
Copyright (c) 2020, Matthew Coleman

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
from posix import mkdir
import qrcode
from math import ceil

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

parts_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "parts.xml"))
packages_filepath_default = Path(os.path.join(Path.home(), ".openpnp2", "packages.xml"))
    

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
      
  def addQRCodeTitle(self, left=True, ttf_path="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"):
    text_margin = 0.05
    for part in self.parts:
      part_id = part["@id"]
      qrc_img = part["qrc_img"]
      qrc_width, qrc_height = qrc_img.size
      
      font = ImageFont.truetype(ttf_path, 16)
      textwidth, textheight = font.getsize(part_id)
      
      adj_text_width = int(textwidth * (1+2*text_margin))
      new_width = int(qrc_width + adj_text_width)
      
      newimg = Image.new(qrc_img.mode, (new_width, qrc_height), "white")
      
      text_vpos = int( (qrc_height-textheight)/2 )

      if left==True:
        text_hpos = int(textwidth*text_margin)
        draw = ImageDraw.Draw(newimg)
        draw.text( (text_hpos, text_vpos), part_id, font=font)
        newimg.paste(qrc_img, (adj_text_width,0))
        
      else:  
        newimg.paste(qrc_img, (0,0))
      
        text_hpos = int(qrc_width + (textwidth*text_margin))
        draw = ImageDraw.Draw(newimg)
        draw.text( (text_hpos, text_vpos), part_id, font=font)
      
      part["qrc_img"] = newimg
      
  def makeConcatenatedQRImage(self, columns=3):
    max_width = 0
    max_height = 0
    part_ids = []

    for part in self.parts:
      part_ids.append(part["@id"])
      qrc_img = part["qrc_img"]
      qrc_width, qrc_height = qrc_img.size
      if qrc_width > max_width:
        max_width = qrc_width
      if qrc_height > max_height:
        max_height = qrc_height
      
    part_rows = int(ceil(len(self.parts) / columns))
    
    total_height = part_rows * max_height

    newimg = Image.new(qrc_img.mode, (max_width*columns, total_height), "white")
    column = 0
    row = 0

    sorted_part_ids = sorted(part_ids)
    
    for sorted_id in sorted_part_ids:
      for part in self.parts:
        if part["@id"] == sorted_id:
          qrc_img = part["qrc_img"]
          newimg.paste(qrc_img, (column * max_width, row * max_height))
          column += 1
          if column >= columns:
            row += 1
            column = 0
      
    return newimg
    
      
  def saveConcatenatedQRImage(self, columns):
    img = self.makeConcatenatedQRImage(columns)
    qr_directory = os.path.join( os.getcwd(), "OpenPnpPartQRCodes")
    if not os.path.exists(qr_directory):
      os.mkdir(qr_directory)
    part_path = os.path.join(qr_directory, "concatenated.png")
    img.save(part_path)

  def saveQRCodeImages(self):
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


   
   
def main():
  open_pnp_parts = OpenPnPParts()
  open_pnp_parts.makeQRCodes()
  open_pnp_parts.resizeQRCodes(0.5)
  open_pnp_parts.addQRCodeTitle()
  open_pnp_parts.saveQRCodeImages()
  open_pnp_parts.saveConcatenatedQRImage(3)
   
if __name__ == '__main__':
    main()
    
    