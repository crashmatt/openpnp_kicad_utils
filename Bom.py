'''
Created on Jan 23, 2021

@author: matt
'''

import csv

class BomItem():
  def __init__(self, value, package, height):
    self.value = value
    self.package = package
    self.height = height
    
    self.package_alias = ""
    self.part_alias = ""
  
  def get_openpnp_name(self):
    package = self.package
    part = self.value
    
    if self.package_alias != "":
      package = self.package_alias

    if self.part_alias != "":
      part = self.part_alias

    return package + "-" + part


class Bom(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.parts = []
        self.references = {}
        self.fields = []
        
    def loadCsv(self, filepath):
      with open(filepath, "r", newline='') as csvFile:
        bomreader = csv.reader(csvFile, delimiter=",", quotechar='"')

        #Scan through csv lines
        for line_idx, line_values in enumerate(bomreader):
      
          if line_idx == 0:
            self.fields = line_values
            fields_cnt = len(self.fields)
            
            refs_field_idx = -1
            footprint_field_idx = -1
            value_field_idx = -1
            height_field_idx = -1
            
            for idx, field in enumerate(self.fields):
              if field == "References":
                refs_field_idx = idx
              if field == "Footprint":
                footprint_field_idx = idx
              if field == "Value":
                value_field_idx = idx
              if field == "Height":
                height_field_idx = idx
            
            #Check all header references are found
            if refs_field_idx == -1:
              return
            if footprint_field_idx == -1:
              return
            if value_field_idx == -1:
              return
                
          print(', '.join(line_values))
          if len(line_values) == fields_cnt:
            footprint = line_values[footprint_field_idx]
            value = line_values[value_field_idx]
            height = 0.0
            if height_field_idx != -1:
              height = line_values[height_field_idx]
              
            item = BomItem(value, footprint, height)
            self.parts.append(item)
            
            #find designator references for part
            refs = line_values[refs_field_idx].split(" ")
            for ref in refs:
              self.references[ref] = item
          else:
            print("Fields:" + str(fields_cnt) + "values:" + str(len(line_values)))
                        
      return len(self.parts) > 0
        
#     def make_OpenPnPPartnames
            
    #Use a dict of package aliases to modify package names in the bom
    def alias_packages(self, aliases):
        for part in self.parts:
          if part.package in aliases.keys():
            part.package_alias = aliases[part.package]
        
        