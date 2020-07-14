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

from pathlib import Path
import os
from tkinter import filedialog
import configparser
import glob
from OpenPnPParts import *

from optparse import OptionParser

from pcb.kicad_mod import KicadMod




      
      
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
    parser.add_option("-x", "--xinv", dest="invert_xpos", default=False, action="store_true", help="Invert the x position of elements")
    parser.add_option("-y", "--yinv", dest="invert_ypos", default=False, action="store_true", help="Invert the y position of elements")
    parser.add_option("-m", "--mark", dest="marked_pin_names", type="string", action="append", help="Mark this pin name to identify it")
    
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
      packages.insertKiCadModPads(kicadmod, 
                                  invert_xpos=options.invert_xpos ,
                                  invert_ypos=options.invert_ypos ,
                                  package_alias=package_aliases,
                                  marked_pin_names=options.marked_pin_names)

    if options.output_file != "":
      export_packages_path  = options.output_file
    else:
      export_packages_path = Path(packages_filepath_default)
#      export_packages_path = export_packages_path.with_name("kicad_export_packages.xml")
    
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