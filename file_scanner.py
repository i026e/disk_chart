#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 19:05:40 2017

@author: pavel
"""
import os
import sys

FOLLOW_SYMLINKS_FILES = False
FOLLOW_SYMLINKS_DIRS = False
MAX_LEVEL = 100


class Element:
    def __init__(self, name, level, size = 0, is_file = False):        
        self.name = name
        self.parent = None
        
        self.level = level
        self.size = size
        
        self.is_file = is_file
        
        self.num_child_files = 0
        self.num_child_dirs = 0
        
        self.children = []
        
    def add_child(self, child): 
        if child is not None:    
            self.children.append(child)
            self.size += child.size
            child.parent = self

            if child.is_file:
                self.num_child_files += 1
            else:
                self.num_child_files += child.num_child_files
                self.num_child_dirs += (1 + child.num_child_dirs)
           
    def max_level(self):
        if self.is_file:
            return self.level
            
        level = self.level
        for child in self.children:
            level = max(level, child.max_level())
            
        return level

    def path(self):
        if self.parent is None:
            return self.name
        return os.path.join(self.parent.path(), self.name)

    def resize(self, size_delta):
        self.size += size_delta
        if self.parent is not None:
            self.parent.resize(size_delta)

    def delete(self, on_error = print):
        try:
            if self.is_file:
                os.remove(self.path())
            else:
                os.rmdir(self.path())

            if self.parent is not None:
                self.parent.resize(-self.size)
                while self in self.parent.children:
                    self.parent.children.remove(self)

            return True

        except Exception as e:
            on_error(e)
        return False

    def __repr__(self):
        lines = ["-"*self.level + self.name + " ["  + str(self.size) + "]"]
        for child in self.children:
            lines.append(child.__repr__())
            
        return os.linesep.join(lines)
        
def get_total_size(path, on_error = print):
    size = 0
    try:
        for root, dirs, files in os.walk(path):
            size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    except Exception as e:
        on_error(e)
    finally:
        return size
        
def stab(*args, **kwargs):
    pass

def scan(root, on_progress = stab, on_error = print):
    #recursion
    def rec_scan(path_obj, level):
        # report progress
        on_progress(path_obj.path)

        # file
        if path_obj.is_file(follow_symlinks=FOLLOW_SYMLINKS_FILES):
            size = os.path.getsize(path_obj.path)
            return Element(path_obj.name, level, size, True)

        # directory
        elif path_obj.is_dir(follow_symlinks=FOLLOW_SYMLINKS_DIRS):
            elm = Element(path_obj.name, level, 0, False)

            if level >= MAX_LEVEL:
                size = get_total_size(path_obj.path, on_error)
                elm.size = size
            else:
                try:
                    for obj in os.scandir(path_obj.path):
                        child = rec_scan(obj, level + 1)
                        elm.add_child(child)
                except Exception as e:
                    on_error(e)
            return elm

    root = os.path.expanduser(root)
    if not os.path.exists(root):
        return None
    if os.path.isfile(root):
        return Element(root, 0, os.path.getsize(root), is_file = True)
        
    root_element = Element(root, 0, 0, is_file = False)
    
    for child in os.scandir(root):        
        root_element.add_child(rec_scan(child,
                                        level = 1))
    
       
        
    #print(root_element)            
    return root_element
    #for root, dirs, files in os.walk(root):
        #print(root, dirs)
        #print(sum(os.path.getsize(os.path.join(root, name)) for name in files), end=" ")
        #print("bytes in", len(files), "non-directory files")
      
        

if __name__ == "__main__":
    print(scan("~/Downloads"))

