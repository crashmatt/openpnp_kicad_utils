'''Created on Jun 27, 2020

@author: matt
'''

from pathlib import Path
import os
from pcb.kicad_mod import KicadMod
from tkinter import filedialog
import configparser
import glob
from OpenPnPParts import *

from optparse import OptionParser


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
    config['DEFAULT']["package_adjustment_file"] = os.path.join(os.getcwd(), "openpnp_package_adjustments.csv")
    config['DEFAULT']["size_extents_layer"] = "F.Fab"
    
    config.read("config.ini")    
    initial_directory = config['DEFAULT']["kicad_mod_directory"]
    package_alias_file = config['DEFAULT']["package_alias_file"]
    package_adjustment_file = config['DEFAULT']["package_adjustment_file"]
    size_extents_layer = config['DEFAULT']["size_extents_layer"]
    
    parser = OptionParser()
    parser.add_option("-a", "--alias", dest="package_alias_file", default=package_alias_file)
    parser.add_option("-d", "--dir", dest="modfile_directory", default="")
    parser.add_option("-o", "--out", dest="output_file", default="")
    parser.add_option("-n", "--no_backup", dest="no_backup", default=False, action="store_true")
    parser.add_option("-y", "--norm_ypos", dest="normal_ypos", default=False, action="store_true", help="Don't invert the y position of elements")
    
    (options, args) = parser.parse_args()


    if options.modfile_directory != "":
      modfile_directory = options.modfile_directory
    else:
      modfile_directory = filedialog.askdirectory(initialdir=initial_directory, mustexist=True)
#       kicadmod_file_paths = filedialog.askopenfilenames(filetypes=[("KiCAD mod file", ".kicad_mod")], initialdir=initial_directory)

      if modfile_directory is None:
        print("No directory selected")
        return

    globsearch = os.path.join(modfile_directory, "*.kicad_mod")
    kicadmod_file_paths = glob.glob(globsearch)
      
    package_aliases = Aliases(options.package_alias_file).aliases
#     package_adjustments = PackageAdjustments(package_adjustment_file)
        
    packages = OpenPnPPackagesXML()
    print(packages.getPackageIDs())
#     return
         
    for kicadmod_file_path in kicadmod_file_paths:
          
      kicadmod_file_path = Path(kicadmod_file_path)
      new_directory = kicadmod_file_path.parent
      
      config['DEFAULT']["kicad_mod_directory"] = str(new_directory)

      kicadmod = KicadMod(kicadmod_file_path)
      packages.insertKiCadModPads(kicadmod, invert_ypos=not options.normal_ypos ,package_alias=package_aliases)

    if options.output_file != "":
      export_packages_path  = options.output_file
    else:
      export_packages_path = Path(packages_filepath_default)
      export_packages_path = export_packages_path.with_name("kicad_export_packages.xml")
    
    if os.path.isfile(export_packages_path):
      if not options.no_backup:
        #Find next available backup increment
        backup_increment = 0
        while os.path.exists(Path(export_packages_path).with_suffix(".bak%s.xml" % backup_increment)):
          backup_increment += 1
        #Move existing file to new backup increment
        backup_path = Path(export_packages_path).with_suffix(".bak%s.xml" % backup_increment)
        backup = Path(export_packages_path)
        backup.rename(backup_path)
      
    packages.exportPackages(export_packages_path)

    with open('config.ini', 'w') as configfile:
      config.write(configfile)


if __name__ == '__main__':
    main()
    
    pass