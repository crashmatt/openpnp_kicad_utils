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

        self.preprocessor_config_path = os.path.join(PROJECT_PATH, "preprocessor_config.ini")
        
        #Get the project filepath from preprocessor config
        self.preprocessor_config = configparser.ConfigParser()
        self.preprocessor_config['PROJECT'] = {"config_filepath": "config.ini"}
        self.preprocessor_config.read(self.preprocessor_config_path)
        config_filepath = self.preprocessor_config['PROJECT']["config_filepath"]
        
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


    def project_relative_path(self, path):
        project_path = Path(self.preprocessor_config['PROJECT']["config_filepath"])
        project_directory = str(project_path.parent)
        
        if not project_directory in str(path):
          return None
      
        return os.path.relpath(str(path), project_directory)

    
    def callback_select_centroid_file(self, event=None):
        centroid_filepath_entry = self.builder.tkvariables['centroid_filepath']        
        filepath = centroid_filepath_entry.get()
        
        pos_file_path = Path(filepath)
        posfile_directory = pos_file_path.parent
        posfile_name = pos_file_path.name
        
        pos_file_path = filedialog.askopenfilename(filetypes=[("KiCAD position file", ".csv")] , initialdir=posfile_directory, initialfile=posfile_name)
      
        if not pos_file_path:
          return;
        
        pos_rel_path = self.project_relative_path(pos_file_path)
        if pos_rel_path:
          pos_file_path = pos_rel_path
        
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


    def callback_select_BOM(self, event=None):
        bom_filepath_entry = self.builder.tkvariables['bom_filepath']        
        filepath = bom_filepath_entry.get()
        
        bom_file = Path(filepath)
        bom_directory = bom_file.parent
        bom_name = bom_file.name
        
        bom_file_path = filedialog.askopenfilename(filetypes=[("KiCAD bom file", ".csv")] , initialdir=bom_directory, initialfile=bom_name)
      
        if not bom_file_path:
          return;

        if not "bom" in bom_file_path:
            messagebox("ERROR: attempting to open a non bom file")
            return
        
        bom_filepath_entry.set(bom_file_path)

    def callback_select_package_alias(self, event=None):
        pass

    def callback_select_part_alias(self, event=None):
        pass

    def callback_set_project_filepath(self, event=None):
        project_path = Path(self.preprocessor_config_path)
        project_directory = project_path.parent
        project_name = project_path.name
        
        project_file_path = filedialog.askopenfilename(filetypes=[("PreProcessor Project", ".ini")] , initialdir=project_directory, initialfile=project_name)
      
        if not project_file_path:
          return;
        
        if "preprocessor_config.ini" in project_file_path:
            messagebox("ERROR: Attempt to use pre_processor_config.ini as project")
            return
        
        #Set the project path
        self.preprocessor_config_path = project_file_path

        #Update project path in the gui
        project_filepath_entry = self.builder.tkvariables['project_config_filepath']        
        project_filepath_entry.set(project_file_path)
        
        #Write project path to the 
        self.preprocessor_config['PROJECT']["config_filepath"] = project_file_path        
        with open(self.preprocessor_config_path, 'w') as configfile:
          self.preprocessor_config.write(configfile)
                
    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    app = PreprocessorApp(root)
    app.run()

