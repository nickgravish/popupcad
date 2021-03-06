# -*- coding: utf-8 -*-
"""
Written by Daniel M. Aukes and CONTRIBUTORS
Email: danaukes<at>asu.edu.
Please see LICENSE for full license.
"""
try:
    import itertools.izip as zip
except ImportError:
    pass

class TreeNode(object):
    def __init__(self):
        self.parent = None
        self.children = []
        self.decendents = []
        self.ancestors = []
        self.value = None

    def _set_parent(self,parent):
        self.parent = parent

    def _add_children(self,children):
        self.children.extend(children)
        self.children = unique_seq(self.children)

    def _add_decendents(self,decendents,recursive = True):
        self.decendents.extend(decendents)
        self.decendents = unique_seq(self.decendents)
        if recursive:
            if self.parent!=None:
                self.parent._add_decendents(decendents,recursive)

    def _add_ancestors(self,ancestors):
        self.ancestors.extend(ancestors)
        self.ancestors = unique_seq(self.ancestors)

    def top(self):
        if self.parent==None:
            return self
        else:
            return self.parent.top()
            
    def getNode(self, value):
        for item in ([self] + self.decendents + self.ancestors):
            if item.value == value:
                return item
        print("Warning: Could not find " + str(value) + " in tree.")
        return None
            
    def path_to_top(self,path_in=None):
        if path_in == None:
            path_in = []
        path_in = path_in+[self]
        if self.parent==None:
            return path_in
        else:
            return self.parent.path_to_top(path_in)

    def build_topology(self,ancestors=None,parent = None):
        if ancestors == None:
            ancestors = []
        self._set_parent(parent)
        self._add_ancestors(ancestors)

        for child in self.children:
            child.build_topology(ancestors+[self],self)
        self._add_decendents(self.children)

    def path_to(self,other):
        a = self.path_to_top()[::-1]
        b = other.path_to_top()[::-1]
        if a[0]!=b[0]:
            raise(Exception("Frames don't share a common parent"))
        for ii,(item1,item2) in enumerate(zip(a,b)):
            if item1!=item2:
                ii-=1
                break
        return a[:ii:-1]+b[ii:]

    def path_from_top(self):
        parent = self.top()
        if parent is None:
            return [self]
        return parent.path_to(self)

    def is_connected(self,other):
        return self.top()==other.top()
    
    def add_branch(self,child):
        self._add_children([child])
        child.build_topology(self.ancestors+[self],self)
        self._add_decendents([child]+child.decendents)
    
    def leaves(self):
        top = self.top()
        leaves = [item for item in top.decendents if not item.children]
        return leaves

    def __contains__(self, *item):
        other_values = [node.value for node in (self.decendents + self.ancestors)]
        return item == self.value or item in other_values
    
    def __str__(self, level=0):
        ret = "\t"*level+repr(self)+"\n"
        for child in self.children:
            ret += child.__str__(level+1)
        return ret

    def __repr__(self):
        if self.value is None:
            value_name = str(self.getID())
        else:
            value_name = repr(self.value)
        out = '<' + value_name + '>'
        return out
        
    def getSiblingIndex(self):
        parent = self.parent
        if parent is None:
            return -1
        else:
            return parent.children.index(self)
            
    def getID(self):
        path = self.path_from_top()
        indexes = [item.getSiblingIndex() for item in path]
        id_string = ""        
        index = 0
        for node in path:
            if node.parent is None:
                id_string += '*'
            elif len(node.parent.children) > 0:
                num = node.getSiblingIndex()
                #if num == -1:#Indicates the tree root
                #    num = -23
                id_string+= str(chr((65+num)))
                id_string+= str(index)
                index = 0
            else:
                index += 1
        if index > 0:
            id_string+=":"
            id_string+= str(index)
        return id_string
    
def unique_seq(seq):
    seen = list()
    seen_add = seen.append
    return [ x for x in seq if not (x in seen or seen_add(x))]
        
def spawnTreeFromList(lov, assert_connected=True, sort=True):    
    import itertools
    values = list(itertools.chain.from_iterable(lov))
    cleanlist = unique_seq(values)    
    tree_list = [(TreeNode()) for value in cleanlist]    
    value_node_dict = dict()    
    for tree, value in zip(tree_list, cleanlist):
        tree.value = value
        value_node_dict[value] = tree
    for parent, child in lov:
        value_node_dict[parent].add_branch(value_node_dict[child])
    if sort:
        #tree_list = [node.children.so for node in tree_list]
        for node in tree_list:
            node.children.sort
    if assert_connected:
        for tree in tree_list:
            if not tree.is_connected(tree_list[0]):
                print("ERROR:" + str(tree) + "is not connected to the rest of the graph")
                assert(False)
    return tree_list[0].top()
    
if __name__=='__main__':
    is_sorted = lambda l: (all(l[i] <= l[i+1] for i in xrange(len(l)-1)))
    def check_sorted_children(node):
        cur_node = node
        if not is_sorted(cur_node.children):
            return False
        for child in cur_node.children:
            if not check_sorted_children(child):
                return False
        return True
    
    A = TreeNode()
    B = TreeNode()
    C = TreeNode()
    D = TreeNode()    
    E = TreeNode()    
    F = TreeNode()    

    A.value = 'A'
    B.value = 'B'
    C.value = 'C'
    D.value = 'D'
    E.value = 'E'
    F.value = 'F'
    
    connections = [[E,F],[A,B],[B,C],[A,D],[D,E]]
    for parent, child in connections:
        parent.add_branch(child)
    
    connections2 = [['E','F'], ['A','B'], ['B','C'], ['A','D'], ['D','E']]
    top1 = connections[1][0].top()
    top2 = spawnTreeFromList(connections2, assert_connected=False)
    assert(top1.value == top2.value)
    print("Checking if tree is sorted")
    assert(check_sorted_children(top1))
    assert(check_sorted_children(top2))
    print("All tests passed!")