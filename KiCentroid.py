'''
Created on 9 Feb 2021

@author: matt
'''

class KiCentroid(object):
  '''
  classdocs
  '''

  def __init__(self, pos_file_path):
    #Read and parse board csv file
    with open(pos_file_path, "r") as board_pos_file:
      board_pos_lines = board_pos_file.readlines()
          
    part_positions = []
    header_line = board_pos_lines[0].rstrip()    #pick header and remove newline
    headers = header_line.split(",")
    for board_pos_line in board_pos_lines[1:]:
      component_position = {}
      component_vals = board_pos_line.rstrip().split(",")   #remove newline and split
      for header, component_val in zip(headers,  component_vals):
        component_position[header] = component_val.replace('"', '')
      part_positions.append(component_position)

    self.headers = headers
    self.part_positions = part_positions

    
  def subPartAlias(self, part_aliases):
    partnumber_aliases = part_aliases.aliases
    
    #Change part numbers into aliases
    for comp_pos in self.part_positions:
      search_val = str(comp_pos["Val"])
      if search_val in partnumber_aliases.keys():
        new_partno = partnumber_aliases[search_val]
        print("Ref:", comp_pos["Ref"], " Val:", comp_pos["Val"], "changed to: ", new_partno)
        comp_pos["Val"] = new_partno
      else:
        print("Failed to find component:", search_val, " in part alias file")
        keys = list(partnumber_aliases)
        print(keys)
        return    
    
  def setPackagesToAliases(self, package_aliases):
    package_aliases = package_aliases.aliases
    
    #Change part numbers into aliases
    for part_pos in self.part_positions:
      search_package = str(part_pos["Package"])
      if search_package in package_aliases.keys():
        new_package = package_aliases[search_package]
        print("Ref:", part_pos["Ref"], " Val:", part_pos["Val"], " Package:", search_package , " changed package to: ", new_package)
        part_pos["Package"] = new_package
      else:
        print("No alias for package", search_package, " for part:" , part_pos["Ref"])
        
  def removeByValue(self, remove_val):
    while True:
      found = False
      for part_pos in self.part_positions:
        if part_pos["Val"] == remove_val:
          self.part_positions.remove(part_pos)
          found = True
      if not found:
        break
      
  def flipBottomToTop(self):
    for part_pos in self.part_positions:
      if part_pos["Side"] == "bottom":
#        part_pos["PosX"] = str(-float(part_pos["PosX"]))
        rotation = float(part_pos["Rot"])
        rotation = -rotation
        rotation += 180.0
        if rotation > 180.0:
          rotation -= 360.0
        part_pos["Rot"] = str(rotation)
#        part_pos["PosX"] = str(-float(part_pos["PosX"]))
        part_pos["Side"] = "top"

  def mirrorBottomYpos(self):
    for part_pos in self.part_positions:
      if part_pos["Side"] == "bottom":
        part_pos["PosY"] = str(-float(part_pos["PosY"]))

  def mirrorBottomXpos(self):
    for part_pos in self.part_positions:
      if part_pos["Side"] == "bottom":
        part_pos["PosX"] = str(-float(part_pos["PosX"]))

  def reverseBottomRotation(self):
    for part_pos in self.part_positions:
      if part_pos["Side"] == "bottom":
        rotation = float(part_pos["Rot"])
        rotation = -rotation
        rotation += 180.0
        if rotation > 180.0:
          rotation -= 360.0
        part_pos["Rot"] = str(rotation)
    
      
  def zeroPositionOffset(self):
    positions = np.empty([0,2])
    for part_pos in self.part_positions:
      xpos = float(part_pos["PosX"])
      ypos = float(part_pos["PosY"])
      positions = np.append(positions, [[xpos, ypos]], axis=0)
    xpos_min = np.min(positions[:,0])
    ypos_min = np.min(positions[:,1])
    new_positions = positions - np.array([xpos_min,ypos_min])
    for part_pos, new_pos in zip(self.part_positions, new_positions):
      part_pos["PosX"] = str(new_pos[0])
      part_pos["PosY"] = str(new_pos[1])
    
  def exportToCSV(self, new_pos_file_path):
    with open(new_pos_file_path, "w") as new_pos_fle:
      #write headers
      for header in self.headers[:-1]:
        new_pos_fle.write(header)
        new_pos_fle.write(",")
      new_pos_fle.write(self.headers[-1])
      new_pos_fle.write("\n")
      
      #Write data
      for comp_pos in self.part_positions:
        for hdr_idx, header in enumerate(self.headers[:-1]):
          #capture the quotes around the first three fields
          if hdr_idx < 3:
            valstr = '"%s",' % (comp_pos[header])
          else:
            valstr = '%s,' % (comp_pos[header])
          new_pos_fle.write(valstr)
        new_pos_fle.write(comp_pos[self.headers[-1]])
        new_pos_fle.write("\n")
        
  def make_outfile_path(self):    
    pos_file_path = Path(self.pos_file_path)
    pos_file_path_stem = pos_file_path.stem
    new_pos_file_path_name = pos_file_path_stem + "_openpnp.csv"
    new_pos_file_path = Path(pos_file_path)
    new_pos_file_path = new_pos_file_path.with_name(new_pos_file_path_name)   
    return new_pos_file_path 

  def process(self, part_aliases, package_aliases, flip_bottom, reverse_bottom, mirror_bottom_x, mirror_bottom_y, out_filepath):
    self.setPackagesToAliases(package_aliases)
    
    self.removeByValue("DNF")
    
    if flip_bottom:
      self.flipBottomToTop()

    if mirror_bottom_x:
      self.mirrorBottomXpos()

    if mirror_bottom_y:
      self.mirrorBottomYpos()
      
    if reverse_bottom:
      self.reverseBottomRotation()
      
    self.exportToCSV(out_filepath)