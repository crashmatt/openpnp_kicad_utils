import os
import pygubu
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter import ttk

from pathlib import Path
import configparser
from optparse import OptionParser
from KiCentroid import *
from Aliases import Aliases
import Bom
from OpenPnPPackages import *
from OpenPnPParts import *

from pcb.kicad_mod import KicadMod

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = os.path.join(PROJECT_PATH, "Preprocessor.ui")

class PreprocessorApp:
    def __init__(self, root):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('frame_pnp_preprocess')
        builder.connect_callbacks(self)
        
        default_mod_filepath = os.path.join("library", "kicad_project.mod")
        #project items as [[name, default_value, type]]
        self.project_gui_items = [ ["centroid_filepath", "centroid.csv"], 
                               ["bom_filepath", "bom.csv" ], 
                               ["package_alias_filepath", "package_alias.csv" ],
                               ["part_alias_filepath", "part_alias.csv" ],
                               ["flip_bottom", True],
                               ["reverse_bottom", True],
                               ["auto_outfile_name", True],
                               ["part_alias", False],
                               ["openpnp_parts_filepath", OpenPnPParts.parts_filepath_default ],
                               ["openpnp_packages_filepath", OpenPnPPackages.packages_filepath_default ],
                               ["qrc_columns", 3],
                               ["qrc_scale", 0.5],
                               ["qrc_bom_only", False],
                               ["kifoot2opnp_xinv", False],
                               ["kifoot2opnp_yinv", False],
                               ["kifoot2opnp_overwrite", False],
                               ["marked_pins", "1,C,CATHODE,A1"],
                               ["extents_layer", ""],
                               ["overwrite_part_height", False],
                               ["ask_overwrite_part_height", True],
                               ["kifoot2opnp_backup", True],
                               ["backup_parts_file", True]]
        
        
        self.project_items = { "mod_filepath": "*.kicad_mod" }
        
        self.preprocessor_config_path = os.path.join(PROJECT_PATH, "preprocessor_config.ini")
        
        #Get the project filepath from preprocessor config
        self.preprocessor_config = configparser.ConfigParser()
        self.preprocessor_config['PROJECT'] = {"config_filepath": "config.ini"}
        self.preprocessor_config.read(self.preprocessor_config_path)
        
        self.reload_project(self.preprocessor_config['PROJECT']["config_filepath"])
        
        root.update()
        w = root.winfo_width()
        h = root.winfo_height()
        self.dimensions = str(w) + "x" + str(h)
        self.builder.tkvariables['status'].set(self.dimensions)

        
    def get_project_setting(self, setting_id, is_path=False):
        setting = self.builder.tkvariables[setting_id].get()
        if not is_path:
          return setting
        return self.make_project_abs_path(setting)
        
    def set_project_setting(self, setting_id, value, is_path=False, gui_var=True):
        setting_value = value
        if is_path:
          setting_value = self.project_relative_path(setting_value)

        self.project_config['SETTINGS'][setting_id] = setting_value
        if gui_var:
          self.builder.tkvariables[setting_id].set(setting_value)
        
        
    def reload_project(self, project_config_filepath):
        #Set project config defaults
        self.project_config = configparser.ConfigParser()
        self.project_config['SETTINGS'] = {}
         
        #set project defaults
        for project_gui_item in self.project_gui_items:
            setting_name = project_gui_item[0]
            setting_default = project_gui_item[1]
            self.project_config['SETTINGS'][setting_name] = str(setting_default)

        for project_item_key in self.project_items.keys():
            self.project_config['SETTINGS'][project_item_key] = str(self.project_items[project_item_key])
         
        #Read the project
        self.project_config.read(project_config_filepath)
                
        for project_gui_item in self.project_gui_items:
            setting_name = project_gui_item[0]
            setting_value = self.project_config['SETTINGS'][setting_name]
            gui_entry = self.builder.tkvariables[project_gui_item[0]]
            gui_entry.set(setting_value)

        for project_item_key in self.project_items.keys():
            self.project_items[project_item_key] = self.project_config['SETTINGS'][project_item_key]
 
        self.project_config_filepath = project_config_filepath
        self.builder.tkvariables['project_config_filepath'].set(project_config_filepath)

        self.show_parts()

    def load_openpnp_parts(self):
        openpnp_parts_filepath = self.make_project_abs_path(self.project_config['SETTINGS']["openpnp_parts_filepath"])  
        return OpenPnPParts(openpnp_parts_filepath)
        
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
        pos_file_path = self.get_project_setting("centroid_filepath", True)
          
        posfile_directory = pos_file_path.parent
        posfile_name = pos_file_path.name
        
        pos_file_path = filedialog.askopenfilename(filetypes=[("KiCAD centroid file", ".csv")] , initialdir=posfile_directory, initialfile=posfile_name)
      
        if not pos_file_path:
          return;
                
        if "openpnp" in pos_file_path:
            messagebox("ERROR: attempting to open an output file as input")
            return
          
        if "alias" in pos_file_path:
            messagebox("ERROR: attempting to open alias file as input")
            return          

        self.set_project_setting('centroid_filepath', pos_file_path, is_path=True, gui_var=True)


    def callback_select_BOM(self, event=None):
        bom_file_path = self.get_project_setting("bom_filepath", True)

        bom_directory = bom_file_path.parent
        bom_name = bom_file_path.name
        
        bom_file_path = filedialog.askopenfilename(filetypes=[("KiCAD bom file", ".csv")] , initialdir=bom_directory, initialfile=bom_name)
      
        if not bom_file_path:
          return;
        
        if not "bom" in bom_file_path:
            messagebox("ERROR: attempting to open a non bom file")
            return

        self.set_project_setting('bom_filepath', bom_file_path, is_path=True, gui_var=True)        
        self.show_parts()

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
        alias_file_path = self.get_project_setting('package_alias_filepath', is_path=True)
          
        aliasfile_directory = alias_file_path.parent
        aliasfile_name = alias_file_path.name
        
        alias_file_path = filedialog.askopenfilename(filetypes=[("kiCAD-OpenPnP package alias file", ".csv")] , initialdir=aliasfile_directory, initialfile=aliasfile_name)
      
        if not alias_file_path:
          return;
        
        self.set_project_setting('package_alias_filepath', alias_file_path, is_path=True, gui_var=True)
        
        self.show_parts()

    def callback_select_part_alias(self, event=None):
        alias_file_path = self.get_project_setting('part_alias_filepath', is_path=True)
          
        aliasfile_directory = alias_file_path.parent
        aliasfile_name = alias_file_path.name
        
        alias_file_path = filedialog.askopenfilename(filetypes=[("kiCAD-OpenPnP part alias file", ".csv")] , initialdir=aliasfile_directory, initialfile=aliasfile_name)
      
        if not alias_file_path:
          return;
        
        self.set_project_setting('part_alias_filepath', alias_file_path, is_path=True, gui_var=True)
        
        self.show_parts()
              

    def callback_save_project(self, event=None):        
        for project_gui_item in self.project_gui_items:
          var_name = project_gui_item[0]
          gui_value = self.builder.tkvariables[var_name].get()
          self.project_config["SETTINGS"][var_name] = str(gui_value)

        for project_item_key in self.project_items.keys():
          self.project_config["SETTINGS"][project_item_key] = str(self.project_items[project_item_key])
          
        project_filepath = self.preprocessor_config['PROJECT']["config_filepath"]
        with open(project_filepath, "w") as project_file:
          self.project_config.write(project_file)

    def make_outfile_path(self, infile_path):
        pos_file_path = Path(infile_path)
        pos_file_path_stem = pos_file_path.stem
        new_pos_file_path_name = pos_file_path_stem + "_openpnp.csv"
        new_pos_file_path = Path(pos_file_path)
        new_pos_file_path = new_pos_file_path.with_name(new_pos_file_path_name)   
        return new_pos_file_path 
      
    def load_project_part_aliases(self):
        part_alias_filepath = self.get_project_setting('part_alias_filepath', is_path=True)
        part_aliases = Aliases(part_alias_filepath)
        return part_aliases
                  
    def load_project_package_aliases(self):
        package_alias_filepath = self.get_project_setting('package_alias_filepath', is_path=True)
        package_aliases = Aliases(package_alias_filepath)
        return package_aliases
              
    def callback_generate(self, event=None):
        centroid_filepath = self.get_project_setting('centroid_filepath', is_path=True)

        if "openpnp" in str(centroid_filepath):
            messagebox("ERROR: attempting to use an output file as input")
            return
          
        if "alias" in str(centroid_filepath):
            messagebox("ERROR: attempting to use alias file as input")
            return         
          
        flip_bottom = self.get_project_setting('flip_bottom', is_path=False)
        reverse_bottom = self.get_project_setting('reverse_bottom', is_path=False)
        part_alias = self.get_project_setting('part_alias', is_path=False)

        part_aliases = None
        
        if part_alias:
          part_aliases = self.load_project_part_aliases() 

        package_aliases = self.load_project_package_aliases()
        
        part_positions = KiCentroid(centroid_filepath)
        
        auto_filename = self.get_project_setting('auto_outfile_name', is_path=False)
        new_pos_file_path = self.make_outfile_path(centroid_filepath)
        if not auto_filename:
          savefile_path = filedialog.asksaveasfilename(filetypes=[("OpenPnP centroid file", ".csv")] , 
                                                       initialdir=new_pos_file_path.parent, initialfile=new_pos_file_path.name)
          
          if not savefile_path:
            return
          
#         bom = None
#         bom_part_heights = self.builder.tkvariables['bom_part_heights'].get()
#         if bom_part_heights:
#             bom_filepath = self.builder.tkvariables['bom_filepath'].get()
#             bom_filepath = self.make_project_abs_path(bom_filepath)            
#             bom = Bom()
#             if not bom.loadCSV(bom_filepath):
#               bom = None
        
        part_positions.process(part_aliases, package_aliases, flip_bottom, reverse_bottom, new_pos_file_path)
        
    def load_project_bom(self):
        bom = Bom()
        bom_filepath = self.get_project_setting('bom_filepath', is_path=True)
        bom.loadCsv(bom_filepath)
        return bom
       
    def callback_generate_qr_codes(self, event=None):
      open_pnp_parts = OpenPnPParts()
      open_pnp_parts.makeQRCodes()
      qrc_scale = self.get_project_setting('qrc_scale', is_path=False)
      open_pnp_parts.resizeQRCodes(qrc_scale)
      open_pnp_parts.addQRCodeTitle()
      if self.builder.tkvariables['qrc_individual_images'].get():
        open_pnp_parts.saveQRCodeImages()
        
      qrc_bom_only = self.get_project_setting('qrc_bom_only', is_path=False)
      if qrc_bom_only:
        package_aliases = self.load_project_package_aliases()
             
        bom = self.load_project_bom()
        bom.alias_packages(package_aliases.aliases)
        open_pnp_parts.filter_by_bom(bom)
      
      qrc_columns = self.get_project_setting('qrc_columns', is_path=False)
      open_pnp_parts.saveConcatenatedQRImage(qrc_columns, self.project_directory());


    def callback_kifoot2openpnp(self, event=None):
        mod_file_path = self.get_project_setting('mod_filepath', is_path=True)

        mod_directory = mod_file_path.parent
        mod_name = mod_file_path.name
        
        mod_file_paths = filedialog.askopenfilenames(filetypes=[("KiCAD mod file", ".mod")] , initialdir=mod_directory, initialfile=mod_name)
      
        if len(mod_file_paths) == 0:
          return;
        
        #Remember the first selection as the default in the project
        self.set_project_setting('mod_filepath', mod_file_paths[0], is_path=True, gui_var=True)

        packages = OpenPnPPackagesXML()
        
        invert_xpos = self.get_project_setting('kifoot2opnp_xinv')
        invert_ypos = self.get_project_setting('kifoot2opnp_yinv')
        backup = self.get_project_setting('kifoot2opnp_backup')
        overwrite = self.get_project_setting('kifoot2opnp_overwrite')
                
        marked_pins = self.get_project_setting('marked_pins')
        marked_pin_names = marked_pins.split(",")
              
        for kicadmod_file_path in mod_file_paths: 
            rel_mod_file_path = self.project_relative_path(mod_file_path)        
            
            kicadmod = KicadMod(kicadmod_file_path)
            packages.insertKiCadModPads(kicadmod, 
                                      invert_xpos=invert_xpos ,
                                      invert_ypos=invert_ypos ,
                                      overwrite = overwrite,
                                      package_alias=self.package_aliases.aliases,
                                      marked_pin_names=marked_pin_names)
            
    def show_parts(self):              
        bom = self.load_project_bom()
        package_aliases = self.load_project_package_aliases()
        bom.alias_packages(package_aliases.aliases)
        
        opnp_parts = self.load_openpnp_parts()

        treeview_data = self.builder.get_object("treeview_data")
        for i in treeview_data.get_children():
            treeview_data.delete(i)
        
        treeview_data["columns"]=("old","new", "action")
        
        treeview_data.column("#0", width=450, minwidth=450, stretch=tk.NO)
        treeview_data.column("old", width=50, minwidth=40, stretch=tk.NO)
        treeview_data.column("new", width=50, minwidth=40, stretch=tk.NO)
        treeview_data.column("action", width=60, minwidth=60, stretch=tk.NO)

        treeview_data.heading("#0",text="Part",anchor=tk.CENTER)
        treeview_data.heading("old", text="Old",anchor=tk.CENTER)
        treeview_data.heading("new", text="New",anchor=tk.CENTER)
        treeview_data.heading("action", text="Action",anchor=tk.CENTER)
        
        for part_idx, part_id in enumerate(opnp_parts.part_id_dict.keys()):
          part = opnp_parts.part_id_dict[part_id]
          part_height = part["@height"]
          bom_part_height = "0.0"
          replace = "Keep"
          for bom_item in bom.parts:
            bom_part_id = bom_item.package + "-" + bom_item.value
            if bom_part_id == part_id:
              bom_part_height = bom_item.height
              if bom_part_height != "0.0" and part_height == "0.0":
                replace = "Replace"
              
          treeview_data.insert("", part_idx+1, text=part_id, values=(part_height, bom_part_height, replace))
        

#     def callback_set_part_heights(self, event=None):                      
#         opnp_parts.bomToPartHeights(bom, False)
        
                
    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    root.title("KiTOP")
    app = PreprocessorApp(root)
    app.run()

