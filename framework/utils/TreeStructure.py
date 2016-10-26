"""
Created on Jan 28, 2014
@ author: alfoa
"""

#for future compatibility with Python 3--------------------------------------------------------------
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)
#End compatibility block for Python 3----------------------------------------------------------------

#message handler
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir)))
import MessageHandler

class Node(MessageHandler.MessageUser):
  """
    The Node class. It represents the base for each TreeStructure construction
  """
  def __init__(self, messageHandler, name, valuesIn={}, text=''):
    """
      Initialize Tree,
      @ In, messageHandler, MessageHandler instance, the message handler to use
      @ In, name, string, is the node name
      @ In, valuesIn, dict, optional, is a dictionary of values
      @ In, text, string, optional, the node's text, as <name>text</name>
    """
    #check message handler is first object
    values         = valuesIn.copy()
    self.name      = name
    self.type      = 'Node'
    self.printTag  = 'Node:<'+self.name+'>'
    if type(messageHandler) != MessageHandler.MessageHandler:
      raise(IOError,'Tried to initialize '+self.type+' without a message handler!  Was given: '+str(messageHandler))
    self.values    = values
    self.text      = text
    self._branches = []
    self.parentname= None
    self.parent    = None
    self.depth     = 0
    self.messageHandler = messageHandler
    self.iterCounter = 0

  def __eq__(self,other):
    """
      Overrides the default equality check
      @ In, other, object, comparison object
      @ Out, eq, bool, True if both are the same
    """
    if isinstance(other,self.__class__):
      same = True
      if self.name != other.name:
        #self.raiseADebug('equality check: name not same!')
        same = False
      elif self.text != other.text:
        #self.raiseADebug('equality check: text not same!')
        same = False
      elif self.values != other.values:
        #self.raiseADebug('equality check: values not same!')
        same = False
      # TODO ... check parent and children?
      return same
    return NotImplemented

  def __ne__(self,other):
    """
      Overrides the default equality check
      @ In, other, object, comparison object
      @ Out, ne, bool, True if both aren't the same
    """
    if isinstance(other,self.__class__):
      return not self.__eq__(other)
    return NotImplemented

  def __hash__(self):
    """
      Overrides the default hash.
      @ In, None
      @ Out, hash, tuple, name and values and text
    """
    return hash(tuple(self.name,tuple(sorted(self.values.items())),self.text))

  def __iter__(self):
    """
      basic iteration method
      @ In, None
      @ Out, self, Node instance, iterate over self
    """
    i=0
    while i<len(self._branches):
      yield self._branches[i]
      i+=1
    #return self

  def __repr__(self):
    """
      Overload the representation of this object... We want to show the name and the number of branches!!!!
      @ In, None
      @ Out, __repr__, string, the representation of this object
    """
    return "<Node %s values=%s at 0x%x containing %s branches>" % (repr(self.name), str(self.values), id(self), repr(len(self._branches)))

  def copyNode(self):
    """
      Method to copy this node and return it
      @ In, None
      @ Out, node, instance, a new instance of this node
    """
    node = self.__class__(self.name, self.values)
    node[:] = self
    return node

  def isAnActualBranch(self,branchName):
    """
      Method to check if branchName is an actual branch
      @ In, branchName, string, the branch name
      @ Out, isHere, bool, True if it found
    """
    isHere = False
    for branchv in self._branches:
      if branchName.strip() == branchv.name: isHere = True
    return isHere

  def numberBranches(self):
    """
      Method to get the number of branches
      @ In, None
      @ Out, len, int, number of branches
    """
    return len(self._branches)

  def appendBranch(self, node, updateDepthLocal = False):
    """
      Method used to append a new branch to this node
      @ In, node, Node, the newer node
      @ In, updateDepthLocal, if the depth needs to be updated locally only
      @ Out, None
    """
    node.parentname = self.name
    node.parent     = self
    # this is to avoid max number of recursion if a close loop. TODO: BETTER WAY
    if not updateDepthLocal: node.updateDepth()
    else                   : node.depth      = self.depth + 1
    self._branches.append(node)

  def updateDepth(self):
    """
      updates the 'depth' parameter throughout the tree
      @In, None
      @ Out, None
    """
    if self.parent=='root': self.depth=0
    else: self.depth = self.parent.depth+1
    for node in self._branches:
      node.updateDepth()

  def extendBranch(self, nodes):
    """
      Method used to append subnodes from a sequence of them
      @ In, nodes, list, list of NodeTree
      @ Out, None
    """
    for nod in nodes:
      nod.parentname = self.name
      nod.parent     = self
    self._branches.extend(nodes)

  def insertBranch(self, pos, node):
    """
      Method used to insert a new branch in a given position
      @ In, pos, integer, the position
      @ In, node, Node, the newer node
      @ Out, None
    """
    node.parentname = self.name
    node.parent     = self
    self._branches.insert(pos, node)

  def removeBranch(self, node):
    """
      Method used to remove a subnode
      @ In, node, Node, the node to remove
      @ Out, None
    """
    self._branches.remove(node)

  def findBranch(self, path):
    """
      Method used to find the first matching branch (subnode)
      @ In, path, string, is the name of the branch or the path
      @ Out, node, Node, the matching subnode
    """
    return NodePath().find(self, path)

  def findallBranch(self, path):
    """
      Method used to find all the matching branches (subnodes)
      @ In, path, string, is the name of the branch or the path
      @ Out, nodes, list, list of all the matching subnodes
    """
    return NodePath().findall(self, path)

  def iterfind(self, path):
    """
      Method used to find all the matching branches (subnodes)
      @ In, path, string, is the name of the branch or the path
      @ Out, iterator, iterator instance, iterator containing all matching nodes
    """
    return NodePath().iterfind(self, path)

  def getParentName(self):
    """
      Method used to get the parentname
      @ In, None
      @ Out, parentName, string, the parent name
    """
    return self.parentname

  def clearBranch(self):
    """
      Method used clear this node
      @ In, None
      @ Out, None
    """
    self.values.clear()
    self._branches = []

  def get(self, key, default=None):
    """
      Method to get a value from this element tree
      If the key is not present, None is returned
      @ In, key, string, id name of this value
      @ In, default, object, optional, an optional default value returned if not found
      @ Out, object, object, the coresponding value or default
    """
    return self.values.get(key, default)

  def add(self, key, value):
    """
      Method to add a new value into this node
      If the key is already present, the corresponding value gets updated
      @ In, key, string, id name of this value
      @ In, value, whatever type, the newer value
    """
    self.values[key] = value

  def keys(self):
    """
      Method to return the keys of the values dictionary
      @ In, None
      @ Out, keys, list, the values keys
    """
    return self.values.keys()

  def getValues(self):
    """
      Method to return values dictionary
      @ In, None
      @ Out, self.values, dict, the values
    """
    return self.values

  def iter(self, name=None):
    """
      Creates a tree iterator.  The iterator loops over this node
      and all subnodes and returns all nodes with a matching name.
      @ In, name, string, optional, name of the branch wanted
      @ Out, e, iterator, the iterator
    """
    if name == "*":
      name = None
    if name is None or self.name == name:
      yield self
    for e in self._branches:
      for e in e.iter(name):
        yield e

  def iterProvidedFunction(self, providedFunction):
    """
      Creates a tree iterator.  The iterator loops over this node
      and all subnodes and returns all nodes for which the providedFunction returns True
      @ In, providedFunction, method, the function instance
      @ Out, e, iterator, the iterator
    """
    if  providedFunction(self.values):
      yield self
    for e in self._branches:
      for e in e.iterProvidedFunction(providedFunction):
        yield e

  def iterEnding(self):
    """
      Creates a tree iterator for ending branches.  The iterator loops over this node
      and all subnodes and returns all nodes without branches
      @ In, None
      @ Out, e, iterator, the iterator

    """
    if len(self._branches) == 0:
      yield self
    for e in self._branches:
      for e in e.iterEnding():
        yield e

  def iterWholeBackTrace(self,startnode):
    """
      Method for creating a sorted list (backward) of nodes starting from node named "name"
      @ In, startnode, Node, the node
      @ Out, result, list, the list of nodes
    """
    result    =  []
    parent    =  startnode.parent
    ego       =  startnode
    while parent:
      result.insert (0, ego)
      parent, ego  =  parent.parent, parent
    if ego.parentname == 'root': result.insert (0, ego)
    return result

  def setText(self,entry):
    """
      Sets the text of the node, as <node>text</node>.
      @ In, entry, string, string to store as node text
      @ Out, None
    """
    self.text = str(entry)

  def writeNode(self,dumpFileObj):
    """
      This method is used to write the content of the node into a file (it recorsevely prints all the sub-nodes and sub-sub-nodes, etc)
      @ In, dumpFileObj, file instance, file instance(opened file)
      @ Out, None
    """
    dumpFileObj.write(' '+'  '*self.depth + '<branch name="' + self.name + '" parent_name="' + self.parentname + '"'+ ' n_branches="'+str(self.numberBranches())+'" >\n')
    if len(self.values.keys()) >0: dumpFileObj.write(' '+'  '*self.depth +'  <attributes>\n')
    for key,value in self.values.items(): dumpFileObj.write(' '+'  '*self.depth+'    <'+ key +'>' + str(value) + '</'+key+'>\n')
    if len(self.values.keys()) >0: dumpFileObj.write(' '+'  '*self.depth +'  </attributes>\n')
    for e in self._branches: e.writeNode(dumpFileObj)
    if self.numberBranches()>0: dumpFileObj.write(' '+'  '*self.depth + '</branch>\n')

  def stringNode(self,msg=''):
    """
      As writeNode, but returns a string representation of the tree instead of writing it to file.
      @ In, msg, string, optional, the string to populate
      @ Out, msg, string, the modified string
    """
    msg+=''+'  '*self.depth + '<' + self.name + '>'+str(self.text)
    if self.numberBranches()==0:msg+='</'+self.name+'>'
    msg+='\n'
    if len(self.values.keys()) >0: msg+=''+'  '*self.depth +'  <attributes>\n'
    for key,value in self.values.items(): msg+=' '+'  '*self.depth+'    <'+ key +'>' + str(value) + '</'+key+'>\n'
    if len(self.values.keys()) >0: msg+=''+'  '*self.depth +'  </attributes>\n'
    for e in self._branches: msg=e.stringNode(msg)
    if self.numberBranches()>0: msg+=''+'  '*self.depth + '</'+self.name+'>\n'
    return msg

#################
#   NODE TREE   #
#################
class NodeTree(MessageHandler.MessageUser):
  """
    NodeTree class. The class tha realizes the Tree Structure
  """
  def __init__(self, messageHandler, node=None):
    """
      Constructor
      @ In, messageHandler, MessageHandler instance, the message handler to use
      @ In, node, Node, optional, the rootnode
      @ Out, None
    """
    if not hasattr(self,"type"):
      self.type = 'NodeTree'
    self.printTag  = self.type+'<'+str(node)+'>'
    if type(messageHandler) != MessageHandler.MessageHandler:
      raise(IOError,'Tried to initialize NodeTree without a message handler!  Was given: '+str(messageHandler))
    self.messageHandler = messageHandler
    self._rootnode = node
    if node: node.parentname='root'

  def getrootnode(self):
    """
      Get the root node reference
      @ In, None
      @ Out, self._rootnode, Node, the root node
    """
    return self._rootnode

  def _setrootnode(self, node):
    """
      Method used to replace the rootnode with this node
      @ In, node, Node, the newer node
      @ Out, None
    """
    self._rootnode = node

  def updateNodeName(self,path, newName):
    """
      Method to update the name of a node
      @ In, path, string, the node name or full path
      @ In, newName, string, the new name
      @ Out, None
    """
    if path == "root": node = self.getrootnode()
    else             : node = self.find(path)
    if node != None: node.name = newName

  def iter(self, name=None):
    """
      Method for creating a tree iterator for the root node
      @ In, name, string, the path or the node name
      @ Out, iter, iterator, the iterator
    """
    if name == 'root': return self.__rootnode
    else:              return self._rootnode.iter(name)

  def iterEnding(self):
    """
      Method for creating a tree iterator for the root node (ending branches)
      @ In, None
      @ Out, iterEnding, iterator, the iterator
    """
    return self._rootnode.iterEnding()

  def iterProvidedFunction(self, providedFunction):
    """
      Method for creating a tree iterator for the root node (depending on returning of provided function)
      @ In, providedFunction, instance, the function
      @ Out, iterProvidedFunction, iterator, the iterator
    """
    return self._rootnode.iterProvidedFunction(providedFunction)

  def iterWholeBackTrace(self,startnode):
    """
      Method for creating a sorted list (backward) of nodes starting from node named "name"
      @ In, startnode, Node, the node
      @ Out, iterWholeBackTrace, list, the list of pointers to nodes
    """
    return self._rootnode.iterWholeBackTrace(startnode)

  def find(self, path):
    """
      Method to find the first toplevel node with a given name
      @ In, path, string, the path or name
      @ Out, find, Node, first matching node or None if no node was found
    """
    if self._rootnode.name == path: return self.getrootnode()
    if path[:1] == "/":
      path = "." + path
    return self._rootnode.findBranch(path)

  def findall(self, path):
    """
      Method to find the all toplevel nodes with a given name
      @ In, path, string, the path or name
      @ Out, findall, list of Node iterators, A list or iterator containing all matching nodes
    """
    if self._rootnode.name == path: return [self.getrootnode()]
    if path[:1] == "/":
      path = "." + path
    return self._rootnode.findallBranch(path)

  def iterfind(self, path):
    """
      Method to find the all matching subnodes with a given name
      @ In, path, string, the path or name
      @ Out, iterfind, list of Node iterators, a sequence of node instances
    """
    if path[:1] == "/":
      path = "." + path
    return self._rootnode.iterfind(path)

  def writeNodeTree(self,dumpFile):
    """
      This method is used to write the content of the whole tree into a file
      @ In, dumpFile, file instance or string, filename (string) or file instance(opened file)
      @ Out, None
    """
    if type(dumpFile).__name__ == 'FileObject' : myFile = open(dumpFile,'w')
    else                                       : myFile = dumpFile
    myFile.write('<NodeTree name = "'+self._rootnode.name+'">\n')
    self._rootnode.writeNode(myFile)
    myFile.write('</NodeTree>\n')
    if type(dumpFile).__name__ == 'FileObject' : myFile.close()

  def stringNodeTree(self,msg=''):
    """
      As writeNodeTree, but creates a string representation instead of writing to a file.
      @ In, msg, string, the string to populate
      @ Out, msg, string, the populated string
    """
    msg=str(msg)
    msg=self._rootnode.stringNode(msg)
    return msg

##################
# METADATA TREE #
#################
class MetadataTree(NodeTree):
  """
    Class for construction of metadata xml trees used in data objects.  Usually contains summary data
    such as that produced by postprocessor models.  Two types of tree exist: dynamic and static.  See
    RAVEN Output type of Files object.
  """
  def __init__(self,messageHandler,rootName):
    self.pivotParam = None
    node = Node(messageHandler,rootName, valuesIn={'dynamic':str(self.dynamic)})
    NodeTree.__init__(self,messageHandler,node)

  def __repr__(self):
    """
      Overridden print method
      @ In, None
      @ Out, repr, string, string of tree
    """
    return self.stringNodeTree()

  def addScalar(self,target,name,value,root=None,pivotVal=None):
    """
      Adds a node entry named "name" with value "value" to "target" node
      Note that Static uses this method exactly, and Dynamic extends it a little
      @ In, target, string, target parameter to add node value to
      @ In, name, string, name of characteristic of target to add
      @ In, value, string/float/etc, value of characteristic
      @ In, root, Node object, optional, node to which "target" belongs or should be added to
      @ In, pivotVal, float, optional, if specified the value of the pivotParam to add target value to
      @ Out, None
    """
    if root is None:
      root = self.getrootnode()
    #FIXME it's possible the user could provide illegal characters here.  What are illegal characters for us?
    targ = self._findTarget(root,target,pivotVal)
    targ.appendBranch(Node(self.messageHandler,name,text=value))

  def _findTarget(self,root,target,pivotVal=None):
    """
      Used to find target node.  This implementation is specific to static, extend it for dynamic.
      @ In, root, Node object, node to search for target
      @ In, target, string, name of target to find/create
      @ In, pivotVal, float, optional, not used in this method but kept for consistency
      @ Out, tNode, Node object, target node (either created or existing)
    """
    tNode = root.findBranch(target)
    if tNode is None:
      tNode = Node(self.messageHandler,target)
      root.appendBranch(tNode)
    return tNode



class StaticMetadataTree(MetadataTree):
  """
    Class for construction of metadata xml trees used in data objects.  Usually contains summary data
    such as that produced by postprocessor models.  Two types of tree exist: dynamic and static.  See
    RAVEN Output type of Files object.
  """
  def __init__(self,messageHandler,rootName):
    """
      Constructor.
      @ In, node, Node object, optional, root of tree if provided
      @ Out, None
    """
    self.dynamic = False
    self.type = 'StaticMetadataTree'
    MetadataTree.__init__(self,messageHandler,rootName)




class DynamicMetadataTree(MetadataTree):
  """
    Class for construction of metadata xml trees used in data objects.  Usually contains summary data
    such as that produced by postprocessor models.  Two types of tree exist: dynamic and static.  See
    RAVEN Output type of Files object.
  """
  def __init__(self,messageHandler,rootName,pivotParam):
    """
      Constructor.
      @ In, node, Node object, optional, root of tree if provided
      @ Out, None
    """
    self.dynamic = True
    self.type = 'DynamicMetadataTree'
    MetadataTree.__init__(self,messageHandler,rootName)
    self.pivotParam = pivotParam

  def _findTarget(self,root,target,pivotVal):
    """
      Used to find target node.  Extension of base class method for Dynamic mode
      @ In, root, Node object, node to search for target
      @ In, target, string, name of target to find/create
      @ In, pivotVal, float, value of pivotParam to use for searching
      @ Out, tNode, Node object, target node (either created or existing)
    """
    pivotVal = float(pivotVal)
    pNode = self._findPivot(root,pivotVal)
    tNode = MetadataTree._findTarget(self,pNode,target)
    return tNode

  def _findPivot(self,root,pivotVal,tol=1e-10):
    """
      Finds the node with the desired pivotValue to the given tolerance
      @ In, root, Node instance, the node to search under
      @ In, pivotVal, float, match to search for
      @ In, tol, float, tolerance for match
      @ Out, pNode, Node instance, matching node
    """
    found = False
    for child in root:
      #make sure we're looking at a pivot node
      if child.name != self.pivotParam:
        continue
      # careful with inequality signs to check for match
      if pivotVal > 0:
        foundCondition = abs(float(child.get('value')) - pivotVal) <= 1e-10*pivotVal
      else:
        foundCondition = abs(float(child.get('value')) - pivotVal) >= 1e-10*pivotVal
      if foundCondition:
        pivotNode = child
        found = True
        break
    #if not found, make it!
    if not found:
      pivotNode = Node(self.messageHandler,self.pivotParam,valuesIn={'value':pivotVal})
      root.appendBranch(pivotNode)
    return pivotNode


####################
#  NodePath Class  #
#  used to iterate #
####################
class NodePath(object):
  """
    NodePath class. It is used to perform iterations over the Tree
  """
  def find(self, node, name):
    """
      Method to find a matching node
      @ In, node, Node, the node (Tree) where the 'name' node needs to be found
      @ In, name, string, the name of the node that needs to be found
      @ Out, nod, Node, the matching node (if found) else None
    """
    for nod in node._branches:
      if nod.name == name:
        return nod
    return None

  def iterfind(self, node, name):
    """
      Method to create an iterator starting from a matching node
      @ In, node, Node, the node (Tree) where the 'name' node needs to be found
      @ In, name, string, the name of the node from which the iterator needs to be created
      @ Out, nod, Node iterator, the matching node (if found) else None
    """
    if name[:3] == ".//":
      for nod in node.iter(name[3:]):
        yield nod
      for nod in node:
        if nod.name == name:
          yield nod

  def findall(self, node, name):
    """
      Method to create an iterator starting from a matching node for all the nodes
      @ In, node, Node, the node (Tree) where the 'name' node needs to be found
      @ In, name, string, the name of the node from which the iterator needs to be created
      @ Out, nodes, list, list of all matching nodes
    """
    nodes = list(self.iterfind(node, name))
    return nodes

def isnode(node):
  """
    Method to create an iterator starting from a matching node for all the nodes
    @ In, node, object, the node that needs to be checked
    @ Out, isnode, bool, is a node instance?
  """
  return isinstance(node, Node) or hasattr(node, "name")
