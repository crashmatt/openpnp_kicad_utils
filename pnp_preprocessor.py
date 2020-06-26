'''
Created on Jun 23, 2020

@author: matt
'''

import xmltodict
import os
from pathlib import Path
from tkinter import filedialog
import configparser

parts_filepath = os.path.join(Path.home(), ".openpnp2", "parts.xml")
packages_filepath = os.path.join(Path.home(), ".openpnp2", "packages.xml")


def main():
  config = configparser.ConfigParser()
  
  default_filepath = os.path.join(Path.home(), "Dropbox", "KiCAD", "pcb.csv")
  config['DEFAULT'] = {"filepath": default_filepath}
  
  config.read("config.ini")
  
  with open(parts_filepath, "rb") as parts_file:
    parts_filedata = parts_file.read()

  with open(packages_filepath, "rb") as packages_file:
    packages_filedata = packages_file.read()
    
  parts = xmltodict.parse(parts_filedata)
  packages = xmltodict.parse(packages_filedata)
  
  packages = packages["openpnp-packages"]["package"]
  parts = parts["openpnp-parts"]["part"]
  
  print(parts)
  print(packages)
  
  part_id_dict = {}
  
  for part in parts:
    part_id = part["@id"]
    part_id_dict[part_id] = part
    
  package_id_dict = {}
  
  for package in packages:
    package_id_dict[package["@id"]] = package

#   #Add pacakge object to part dictionary   
#   for part in parts:
#     part_package_id = part["@package-id"]
#     part_package = package_id_dict[part_package_id]
#     part["package_obj"] = part_package

  pos_file_path = Path(config['DEFAULT']["filepath"])
  posfile_directory = pos_file_path.parent
  posfile_name = pos_file_path.name    

  pos_file_path = filedialog.askopenfilename(filetypes=[("KiCAD position file", ".csv")] , initialdir=posfile_directory, initialfile=posfile_name)
  
  if pos_file_path == "":
    return;

  if "alias" in pos_file_path:
    print("ERROR: attempting to open alias file as input")
    return
  
  if "openpnp" in pos_file_path:
    print("ERROR: attempting to open an output file as input")
    return

  
  config['DEFAULT']["filepath"] = pos_file_path

  pos_file_path = Path(pos_file_path)

  with open('config.ini', 'w') as configfile:
    config.write(configfile)
#       
  alias_filepath = Path(pos_file_path)
  alias_filepath = alias_filepath.with_name("openpnp_partname_alias.csv")
   
  #Read and parse board csv file
  with open(pos_file_path, "r") as board_pos_file:
    board_pos_lines = board_pos_file.readlines()
  
  component_positions = []
  headers = board_pos_lines[0].split(",")
  for board_pos_line in board_pos_lines[1:]:
    component_position = {}
    component_vals = board_pos_line.split(",")
    for header, component_val in zip(headers,  component_vals):
      component_position[header] = component_val.replace('"', '')
    component_positions.append(component_position)


  #Read and parse alias file
  with open(alias_filepath, "r") as alias_file:
    alias_lines = alias_file.readlines()
  
  partnumber_aliases = {}
  for alias_line in alias_lines:
    alias_splits = alias_line.split(",")
    partno = str(alias_splits[0])
    alias = str(alias_splits[1][:-1])
    partnumber_aliases[partno] = alias
    
  print(partnumber_aliases)
        
  #Change part numbers into aliases
  for comp_pos in component_positions:
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
    
  #Modify packages
  for comp_pos in component_positions:
    component_val = comp_pos["Val"]
    part = part_id_dict[component_val]
    package_id = part["@package-id"]
    comp_pos["Package"] = package_id

  #Export new csv file
  pos_file_path_stem = pos_file_path.stem
  new_pos_file_path_name = pos_file_path_stem + "_openpnp.csv"
  new_pos_file_path = Path(pos_file_path)
  new_pos_file_path = new_pos_file_path.with_name(new_pos_file_path_name)
  
  print("new_pos_file_path:", new_pos_file_path)
  
  
  with open(new_pos_file_path, "w") as new_pos_fle:
    #write headers
    for header in headers[:-1]:
      if header != "Package":
        new_pos_fle.write(header)
        new_pos_fle.write(",")
    new_pos_fle.write(headers[-1])
    
    #Write data
    for comp_pos in component_positions:
      for hdr_idx, header in enumerate(headers[:-1]):
        if header != "Package":
          if hdr_idx < 3:
            valstr = '"%s",' % (comp_pos[header])
          else:
            valstr = '%s,' % (comp_pos[header])
          new_pos_fle.write(valstr)
      new_pos_fle.write(comp_pos[headers[-1]])
    
 
  print(part_id_dict)
  print(package_id_dict)

if __name__ == '__main__':
    main()
    pass