import os
import pygubu
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path
import configparser
from optparse import OptionParser
from pnp_preprocessor import PartPositions
from OpenPnPParts import *

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = os.path.join(PROJECT_PATH, "Preprocessor.ui")


class PreprocessorApp:
    def __init__(self, root):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('frame_pnp_preprocess')
        builder.connect_callbacks(self)
        
        #Get the project filepath from preprocessor config
        preprocessor_config = configparser.ConfigParser()
        preprocessor_config['PROJECT'] = {"config_filepath": "config.ini"}
        preprocessor_config.read("preprocessor_config.ini")
        config_filepath = preprocessor_config['PROJECT']["config_filepath"]
        
        #Set project config defaults
        config = configparser.ConfigParser()
        default_filepath = os.path.join(Path.home(), "Dropbox", "KiCAD", "pcb.csv")
        config['DEFAULT'] = {"filepath": default_filepath}
         
        #Read the project
        config.read(config_filepath)
        
        #Set the project filepath text
        project_config_filepath_entry = self.builder.tkvariables['project_config_filepath']        
        project_config_filepath_entry.set(config_filepath)

        pos_file_path = Path(config['DEFAULT']["filepath"])
        centroid_filepath_entry = self.builder.tkvariables['centroid_filepath']        
        centroid_filepath_entry.set(str(pos_file_path))

        package_alias_file_path = Path(config['DEFAULT']["package_alias_file"])
        package_alias_filepath_entry = self.builder.tkvariables['package_alias_filepath']        
        package_alias_filepath_entry.set(str(package_alias_file_path))


        flip_bottom_checkbox = self.builder.tkvariables['flip_bottom']        
        flip_bottom = flip_bottom_checkbox.set(True)          

        reverse_bottom_checkbox = self.builder.tkvariables['reverse_bottom']        
        reverse_bottom = reverse_bottom_checkbox.set(True)            

    
    def callback_select_centroid_file(self, event=None):      
        centroid_filepath_entry = self.builder.tkvariables['centroid_filepath']        
        filepath = centroid_filepath_entry.get()
        
        pos_file_path = Path(filepath)
        posfile_directory = pos_file_path.parent
        posfile_name = pos_file_path.name
        
        pos_file_path = filedialog.askopenfilename(filetypes=[("KiCAD position file", ".csv")] , initialdir=posfile_directory, initialfile=posfile_name)
      
        if not pos_file_path:
          return;

        if "openpnp" in pos_file_path:
            messagebox("ERROR: attempting to open an output file as input")
            return
          
        if "alias" in pos_file_path:
            messagebox("ERROR: attempting to open alias file as input")
            return          
        
        centroid_filepath_entry.set(pos_file_path)
              
    def callback_generate(self, event=None):
        centroid_filepath_entry = self.builder.tkvariables['centroid_filepath']        
        filepath = centroid_filepath_entry.get()
        pos_file_path = Path(filepath)      

        if "openpnp" in pos_file_path:
            messagebox("ERROR: attempting to use an output file as input")
            return
          
        if "alias" in pos_file_path:
            messagebox("ERROR: attempting to use alias file as input")
            return      
          
        flip_bottom_checkbox = self.builder.tkvariables['flip_bottom']        
        flip_bottom = flip_bottom_checkbox.get()          

        reverse_bottom_checkbox = self.builder.tkvariables['reverse_bottom']        
        reverse_bottom = reverse_bottom_checkbox.get()         

        package_alias_filepath_entry = self.builder.tkvariables['package_alias_filepath']        
        package_alias_filepath = package_alias_filepath_entry.get()
        package_alias_filepath = Path(package_alias_filepath)      
        package_aliases = Aliases(package_alias_filepath)
        
        part_positions = PartPositions(pos_file_path)
        
        new_pos_file_path = part_positions.make_outfile_path()
        
        part_positions.process(None, package_aliases, flip_bottom, reverse_bottom, new_pos_file_path)
          
        pass
            

    def callback_select_BOM(self, event=None):
        pass

    def callback_select_package_alias(self, event=None):
        pass

    def callback_select_part_alias(self, event=None):
        pass

    def callback_set_project_filepath(self, event=None):
        pass      

    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    app = PreprocessorApp(root)
    app.run()

