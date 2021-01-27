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
        
#        default_filepath = os.path.join(Path.home(), "Dropbox", "KiCAD", "pcb.csv")
        self.project_items = [ ["centroid_filepath", "centroid.csv"], 
                               ["bom_filepath", "bom.csv" ], 
                               ["package_alias_filepath", "package_alias.csv" ] ]
        
        self.preprocessor_config_path = os.path.join(PROJECT_PATH, "preprocessor_config.ini")
        
        #Get the project filepath from preprocessor config
        self.preprocessor_config = configparser.ConfigParser()
        self.preprocessor_config['PROJECT'] = {"config_filepath": "config.ini"}
        self.preprocessor_config.read(self.preprocessor_config_path)
        
        self.reload_project(self.preprocessor_config['PROJECT']["config_filepath"])
        
        
    def reload_project(self, project_config_filepath):
        #Set project config defaults
        self.project_config = configparser.ConfigParser()

        self.project_config['SETTINGS'] = {}
         
        #set project defaults
        for project_item in self.project_items:
            setting_name = project_item[0]
            setting_default = project_item[1]
            self.project_config['SETTINGS'][setting_name] = setting_default
         
        #Read the project
        self.project_config.read(project_config_filepath)
                
        for project_item in self.project_items:
            setting_name = project_item[0]
            setting_value = self.project_config['SETTINGS'][setting_name]
            gui_entry = self.builder.tkvariables[project_item[0]]
            gui_entry.set(setting_value)

        flip_bottom_checkbox = self.builder.tkvariables['flip_bottom']        
        flip_bottom = flip_bottom_checkbox.set(True)          

        reverse_bottom_checkbox = self.builder.tkvariables['reverse_bottom']        
        reverse_bottom = reverse_bottom_checkbox.set(True)      

        self.project_config_filepath = project_config_filepath
        self.builder.tkvariables['project_config_filepath'].set(project_config_filepath)


    def project_directory(self):
      return str(Path(self.project_config_filepath).parent)

    #Check if path is a subdirectory of project.  If so return the relative path otherwise return abs path.
    def project_relative_path(self, path):
        project_directory = self.project_directory()
        
        if not project_directory in str(path):
          return path
      
        return os.path.relpath(str(path), project_directory)

    def make_project_abs_path(self, filepath):
        if(os.path.isabs(filepath)):
          return Path(filepath)
        
        project_directory = self.project_directory()
        return Path(os.path.join(project_directory, filepath))
      
                               
    def callback_select_centroid_file(self, event=None):
        pos_file_path = self.make_project_abs_path(self.builder.tkvariables['centroid_filepath'].get())
          
        posfile_directory = pos_file_path.parent
        posfile_name = pos_file_path.name
        
        pos_file_path = filedialog.askopenfilename(filetypes=[("KiCAD centroid file", ".csv")] , initialdir=posfile_directory, initialfile=posfile_name)
      
        if not pos_file_path:
          return;
        
        pos_file_path = self.project_relative_path(pos_file_path)
        
        if "openpnp" in pos_file_path:
            messagebox("ERROR: attempting to open an output file as input")
            return
          
        if "alias" in pos_file_path:
            messagebox("ERROR: attempting to open alias file as input")
            return          
        
        self.builder.tkvariables['centroid_filepath'].set(pos_file_path)
        
              
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
        bom_file_path = self.make_project_abs_path(self.builder.tkvariables['bom_filepath'].get())

        bom_directory = bom_file_path.parent
        bom_name = bom_file_path.name
        
        bom_file_path = filedialog.askopenfilename(filetypes=[("KiCAD bom file", ".csv")] , initialdir=bom_directory, initialfile=bom_name)
      
        if not bom_file_path:
          return;
        
        if not "bom" in bom_file_path:
            messagebox("ERROR: attempting to open a non bom file")
            return

        bom_file_path = self.project_relative_path(bom_file_path)
        
        self.builder.tkvariables['bom_filepath'].set(bom_file_path)

    def callback_set_project_filepath(self, event=None):
        project_path = Path(self.project_config_filepath)
        project_directory = project_path.parent
        project_name = project_path.name
        
        project_file_path = filedialog.askopenfilename(filetypes=[("PreProcessor Project", ".ini")] , initialdir=project_directory, initialfile=project_name)
      
        if not project_file_path:
          return;
        
        if "preprocessor_config.ini" in project_file_path:
            messagebox("ERROR: Attempt to use pre_processor_config.ini as project")
            return
        
        #Update project path in the gui
        self.builder.tkvariables['project_config_filepath'].set(project_file_path)
        
        #Write project path to the preprocessor config so it gets used next time
        self.preprocessor_config['PROJECT']["config_filepath"] = project_file_path        
        with open(self.preprocessor_config_path, 'w') as configfile:
          self.preprocessor_config.write(configfile)

        #Reload the new project and set project path
        self.reload_project(project_file_path)
        
    def callback_select_package_alias(self, event=None):
        alias_file_path = self.make_project_abs_path(self.builder.tkvariables['package_alias_filepath'].get())
          
        aliasfile_directory = alias_file_path.parent
        aliasfile_name = alias_file_path.name
        
        alias_file_path = filedialog.askopenfilename(filetypes=[("kiCAD-OpenPnP package alias file", ".csv")] , initialdir=aliasfile_directory, initialfile=aliasfile_name)
      
        if not alias_file_path:
          return;
        
        alias_file_path = self.project_relative_path(alias_file_path)
                
        self.builder.tkvariables['package_alias_filepath'].set(alias_file_path)
              

    def callback_save_project(self, event=None):        
        for project_item in self.project_items:
          var_name = project_item[0]
          gui_value = self.builder.tkvariables[var_name].get()
          self.project_config["SETTINGS"][var_name] = gui_value
          
        project_filepath = self.preprocessor_config['PROJECT']["config_filepath"]
        with open(project_filepath, "w") as project_file:
          self.project_config.write(project_file)
                
                
    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    app = PreprocessorApp(root)
    app.run()

