from os import listdir
from os.path import basename, exists, isfile, isdir, join as pjoin

from pyramid.url import static_url

import ROOT as R

from .locationaware import LocationAware
from .root.file import RootFileTraverser


class FilesystemTraverser(LocationAware):
    section = "directory"

    def __init__(self, request, path=None):
        self.request = request
        self.path = path or request.registry.settings["results_path"]
    
    @property
    def name(self):
        return basename(self.path)
    
    @property
    def icon_url(self):
        if isdir(self.path):
            return static_url('weboot:static/folder_32.png', self.request)
            
        if exists(self.path) and isfile(self.path):
            if self.name.endswith(".root"):
                return static_url('weboot:static/folder_chart_32.png', self.request)
                
        return static_url('weboot:static/close_32.png', self.request)
        
    @property
    def content(self):
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p) for p in self.ls)
    
    @property
    def items(self):
        items = [self[i] for i in listdir(self.path)]
        items = [i for i in items if i]
        items.sort(key=lambda o: o.name)
        return items
    
    def __getitem__(self, subpath):
        path = pjoin(self.path, subpath)
        if isfile(path) and path.endswith(".root"):
            # File
            f = R.TFile(path)
            if f.IsZombie() or not f.IsOpen():
                raise HTTPNotFound("Failed to open {0}".format(path))
            return RootFileTraverser.from_parent(self, subpath, f)
            
        elif isdir(path):
            # Subdirectory
            return FilesystemTraverser.from_parent(self, subpath, path)
            
        elif "*" in subpath:
            # Pattern
            pattern = re.compile(fnmatch.translate(subpath))
            contexts = [(f, traverse(self, f)["context"])
                        for f in listdir(self.path) if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)

        #raise KeyError(subpath)