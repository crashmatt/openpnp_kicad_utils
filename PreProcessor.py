import os
import sys
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

print("sys.path[0]", sys.path[0])

print("os.getcwd()", os.getcwd())

dir_path = os.path.dirname(os.path.realpath(__file__))
print("dir_path", dir_path)

# Path to kicad-library-utils directory
kicad_lib_dir = os.path.abspath(os.path.join(dir_path, 'kicad-library-utils'))

if not kicad_lib_dir in sys.path:
    sys.path.append(kicad_lib_dir)

# Path to kicad-library-utils directory
kicad_pcb_dir = os.path.abspath(os.path.join(dir_path, 'kicad-library-utils', 'pcb'))

if not kicad_pcb_dir in sys.path:
    sys.path.append(kicad_pcb_dir)

# Path to kicad-library-utils directory
kicad_common_dir = os.path.abspath(os.path.join(dir_path, 'kicad-library-utils', 'common'))

if not kicad_common_dir in sys.path:
    sys.path.append(kicad_common_dir)


#from pcb.kicad_mod import KicadMod
#KicadMod = __import__('pcb.kicad_mod.KicadMod')
#from kicad_library_utils.pcb.kicad_mod import KicadMod


PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = os.path.join(PROJECT_PATH, "Preprocessor.ui")

class PreprocessorApp:

    def __init__(self, root):
        self.root = root
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
                               ["mirror_bottom_x", False],
                               ["mirror_bottom_y", False],
                               ["auto_outfile_name", True],
                               ["part_alias", False],
                               ["openpnp_parts_filepath", OpenPnPParts.parts_filepath_default ],
                               ["openpnp_packages_filepath", OpenPnPPackagesXML.packages_filepath_default ],
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
                               ["backup_parts_file", True],
                               ["ki2opnp_merge_pads", True]]


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
            messagebox.showerror(message="ERROR: attempting to use an output file as input")
            return

        if "alias" in str(centroid_filepath):
            messagebox.showerror(message="ERROR: attempting to use alias file as input")
            return

        flip_bottom = self.get_project_setting('flip_bottom', is_path=False)
        reverse_bottom = self.get_project_setting('reverse_bottom', is_path=False)
        mirror_bottom_x = self.get_project_setting('mirror_bottom_x', is_path=False)
        mirror_bottom_y = self.get_project_setting('mirror_bottom_y', is_path=False)
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

        part_positions.process(part_aliases, package_aliases, flip_bottom, reverse_bottom, mirror_bottom_x, mirror_bottom_y, new_pos_file_path)

    def load_project_bom(self):
        bom = Bom()
        bom_filepath = self.get_project_setting('bom_filepath', is_path=True)
        bom.loadCsv(bom_filepath)
        return bom

    def callback_generate_qr_codes(self, event=None):
      open_pnp_parts = OpenPnPParts()

      qrc_bom_only = self.get_project_setting('qrc_bom_only', is_path=False)
      if qrc_bom_only:
        package_aliases = self.load_project_package_aliases()

        bom = self.load_project_bom()
        bom.alias_packages(package_aliases.aliases)
        id_list = []
        for bom_item in bom.parts:
          id_list.append(bom_item.get_openpnp_name())
        open_pnp_parts.filter_by_id_list(id_list)

      open_pnp_parts.makeQRCodes()
      qrc_scale = self.get_project_setting('qrc_scale', is_path=False)
      open_pnp_parts.resizeQRCodes(qrc_scale)
      open_pnp_parts.addQRCodeTitle()
      if self.builder.tkvariables['qrc_individual_images'].get():
        open_pnp_parts.saveQRCodeImages()

      qrc_columns = self.get_project_setting('qrc_columns', is_path=False)

      bom_filepath = self.get_project_setting("bom_filepath")
      stem = Path(bom_filepath).stem
      open_pnp_parts.saveConcatenatedQRImage(qrc_columns, self.project_directory(), stem);


    def callback_kifoot2openpnp(self, event=None):
        try:
          import pcb.kicad_mod as kicad_mod
#           from importlib import import_module
#           kicad_mod = import_module('pcb.kicad_mod')
        except ImportError as e:
          print(e)
          messagebox.showwarning(message="Failed to import kicad_mod: os.getcwd()=" + os.getcwd())
          messagebox.showerror(message=e)
          return


        mod_file_path = self.project_items["mod_filepath"]
        mod_file_path = self.make_project_abs_path(mod_file_path)

        mod_directory = mod_file_path.parent
        mod_name = mod_file_path.name

        mod_file_paths = filedialog.askopenfilenames(filetypes=[("KiCAD mod file", ".kicad_mod")] , initialdir=mod_directory)

        if len(mod_file_paths) == 0:
          return;

        packages = OpenPnPPackagesXML()

        package_aliases = self.load_project_package_aliases().aliases

        invert_xpos = self.get_project_setting('kifoot2opnp_xinv')
        invert_ypos = self.get_project_setting('kifoot2opnp_yinv')
        backup = self.get_project_setting('kifoot2opnp_backup')
        overwrite = self.get_project_setting('kifoot2opnp_overwrite')
        merge_pads = self.get_project_setting('ki2opnp_merge_pads')

        marked_pins = self.get_project_setting('marked_pins')
        marked_pin_names = marked_pins.split(",")

        for kicadmod_file_path in mod_file_paths:
            rel_mod_file_path = self.project_relative_path(mod_file_path)

            kicadmod = kicad_mod.KicadMod(kicadmod_file_path)
            if (not packages.insertKiCadModPads(kicadmod,
                                      invert_xpos=invert_xpos ,
                                      invert_ypos=invert_ypos ,
                                      overwrite = overwrite,
                                      package_alias=package_aliases,
                                      marked_pin_names=marked_pin_names,
                                      merge_pad_ids=merge_pads)):
              messagebox.showerror("Failed to import package from:" + kicadmod_file_path)

        packages.exportPackages()

        #Remember the first selection as the default in the project
        self.project_items["mod_filepath"] = self.project_relative_path(mod_file_paths[0])


    def callback_part_height_setting(self, event=None):
        self.root.after(100, self.show_parts)

    def update_parts(self):
        self.bom = self.load_project_bom()
        package_aliases = self.load_project_package_aliases()
        self.bom.alias_packages(package_aliases.aliases)

        self.opnp_parts = self.load_openpnp_parts()
        self.bom_to_opnp_dict = {}

        opnp_part_ids = self.opnp_parts.part_id_dict.keys()
        for bom_item in self.bom.parts:
          part_opnp_name = bom_item.get_openpnp_name()
          opnp_part = None
          if part_opnp_name in opnp_part_ids:
            opnp_part =  self.opnp_parts.part_id_dict[part_opnp_name]
          bom2opnp = BomItemToOPnPPart(bom_item, opnp_part)
          self.bom_to_opnp_dict[part_opnp_name] = bom2opnp

    PART_HEIGHT_NOT_IN_BOM = 0
    PART_HEIGHT_KEEP = 1
    PART_HEIGHT_OVERWRITE = 2

    def get_part_height_overwrite(self, bom_height, opnp_height, overwrite=False):
        if bom_height == "0.0" or bom_height == "":
          return self.PART_HEIGHT_NOT_IN_BOM
        if opnp_height == "0.0" or opnp_height == "":
          return self.PART_HEIGHT_OVERWRITE
        if overwrite:
          return self.PART_HEIGHT_OVERWRITE
        return self.PART_HEIGHT_KEEP


    def show_parts(self):
        self.update_parts()

        overwrite_part_height = self.get_project_setting('overwrite_part_height', is_path=False)
        ask_overwrite_part_height = self.get_project_setting('ask_overwrite_part_height', is_path=False)

        treeview_data = self.builder.get_object("treeview_data")
        #Clear treeview
        for i in treeview_data.get_children():
            treeview_data.delete(i)

        treeview_data["columns"]=("opnp", "bom", "new", "action")

        treeview_data.column("#0", width=450, minwidth=350, stretch=tk.NO)
        treeview_data.column("opnp", width=50, minwidth=40, stretch=tk.NO)
        treeview_data.column("bom", width=50, minwidth=40, stretch=tk.NO)
        treeview_data.column("new", width=50, minwidth=40, stretch=tk.NO)
        treeview_data.column("action", width=80, minwidth=80, stretch=tk.NO)

        treeview_data.heading("#0",text="Part",anchor=tk.CENTER)
        treeview_data.heading("opnp", text="oPnP",anchor=tk.CENTER)
        treeview_data.heading("bom", text="Bom",anchor=tk.CENTER)
        treeview_data.heading("new", text="New",anchor=tk.CENTER)
        treeview_data.heading("action", text="Action",anchor=tk.CENTER)

        for bom2opnp_name in self.bom_to_opnp_dict.keys():
          bom2opnp = self.bom_to_opnp_dict[bom2opnp_name]

          action = ""
          bom_item_height = bom2opnp.bom_item.height
          opnp_part =  bom2opnp.opnp_part

          if opnp_part == None:
            action = "No match"
            opnp_part_height = ""
            new_height = ""
          else:
            opnp_part_height = opnp_part.get("height")
            overwrite_type = self.get_part_height_overwrite(bom_item_height, opnp_part_height, overwrite_part_height)
            if overwrite_type == self.PART_HEIGHT_NOT_IN_BOM:
                new_height = ""
                action = "Missing"
            if overwrite_type == self.PART_HEIGHT_KEEP:
                new_height = ""
                action = "Keep"
            if overwrite_type == self.PART_HEIGHT_OVERWRITE:
                action = "Set"
                new_height = bom_item_height

          treeview_data.insert("", 'end', text=bom2opnp_name, values=(opnp_part_height, bom_item_height, new_height, action))

    def callback_set_part_heights(self, event=None):
        for opnp_id in self.bom_to_opnp_dict.keys():
            bom2opnp = self.bom_to_opnp_dict[opnp_id]

            if bom2opnp.opnp_part != None:
                bom_item_height = bom2opnp.bom_item.height
                opnp_part =  bom2opnp.opnp_part
                opnp_part_height = opnp_part.get("height")

                overwrite_part_height = self.get_project_setting('overwrite_part_height', is_path=False)
                overwrite_type = self.get_part_height_overwrite(bom_item_height, opnp_part_height, overwrite_part_height)
                if overwrite_type == self.PART_HEIGHT_OVERWRITE:

                  opnp_part.set("height", str(bom_item_height) )

        openpnp_parts_filepath = self.get_project_setting("openpnp_parts_filepath", is_path=True)
        self.opnp_parts.exportParts(openpnp_parts_filepath, backup=True)



    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    root.title("KiTOP")
    app = PreprocessorApp(root)
    app.run()

