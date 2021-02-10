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

import os
from pathlib import Path
import tkinter.filedialog as filedialog 
import configparser
from optparse import OptionParser
import glob
from Aliases import *
from KiCentroid import *

from OpenPnPParts import *

      
def main():
  config = configparser.ConfigParser()
  
  default_filepath = os.path.join(Path.home(), "Dropbox", "KiCAD", "pcb.csv")
  config['DEFAULT'] = {"filepath": default_filepath}
  
  config.read("config.ini")  

  pos_file_path = Path(config['DEFAULT']["filepath"])
  posfile_directory = pos_file_path.parent
  posfile_name = pos_file_path.name
  
  parser = OptionParser()
  parser.add_option("-a", "--alias", dest="package_alias_filepath", default=config['DEFAULT']["package_alias_file"])
  parser.add_option("-d", "--dir", dest="posfile", default="")
  parser.add_option("-o", "--out", dest="outfile", default="")
  parser.add_option("-f", "--flip_bottom", dest="flip_bottom", default=False, action="store_true")
  parser.add_option("-r", "--rev_bottom", dest="reverse_bottom", default=False, action="store_true")
  
  (options, args) = parser.parse_args()

  package_alias_filepath = Path(options.package_alias_filepath)
  
  if options.posfile != "":
    pos_file_path = options.posfile
  else:
    pos_file_path = filedialog.askopenfilename(filetypes=[("KiCAD position file", ".csv")] , initialdir=posfile_directory, initialfile=posfile_name)
  
    if not pos_file_path:
      return;

  if "alias" in pos_file_path:
    print("ERROR: attempting to open alias file as input")
    return
  
  if "openpnp" in pos_file_path:
    print("ERROR: attempting to open an output file as input")
    return

  
  config['DEFAULT']["filepath"] = pos_file_path

  pos_file_path = Path(pos_file_path)
  part_positions = PartPositions(pos_file_path)
  
  with open('config.ini', 'w') as configfile:
    config.write(configfile)
#       
#   part_alias_filepath = Path(pos_file_path)
#   part_alias_filepath = part_alias_filepath.with_name("openpnp_partname_alias.csv")
#   part_alises = Aliases(part_alias_filepath)
  
  package_aliases = Aliases(package_alias_filepath)
    
  #Export new csv file
  if options.outfile != "":
    new_pos_file_path = Path(options.outfile)
  else:
    new_pos_file_path = part_positions.make_outfile_path()
  print("new_pos_file_path:", new_pos_file_path)    
    
  part_positions.process(None, package_aliases, options.flip_bottom, options.reverse_bottom, new_pos_file_path)
  
  

if __name__ == '__main__':
    main()
    pass