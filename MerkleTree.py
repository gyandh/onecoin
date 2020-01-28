import hashlib, random, time
import ecdsa
from ecdsa import SigningKey

# Creates the Merkle Tree to use in the Blocks
class MerkleTree:

    # A simple class to easier create nodes
    class Node:
        def __init__(self, data, left=None, right=None):
            self.left = left
            self.right = right
            self.data = data

    def __init__(self):
        self.dataNodes = []
        self.root = None

    # Creates a list of Node objects that will form the tree
    def add(self, data):
        self.dataNodes += [self.Node(data)]
    
    # Starts building the tree:
    # Creates a new list with Nodes containing the hashed data while pointing to the old Node
    # then calls build_help() to finish
    def build(self):
        tree = []
        # hash every data added and make nodes
        for d in self.dataNodes:
            tree += [self.Node(hashlib.sha256(b'0'+d.data).digest(), d)]
        self.dataNodes = []
        if(self.root == None):
            # no previous tree created
            self.root = self.build_help(tree)
        else:
            # adding data to existing tree so save old root and make a new tree with new data
            old_root = self.root
            temp_root = self.build_help(tree)
            root_hash = hashlib.sha256(b'1'+old_root.data+temp_root.data).digest()
            # new root is parent of both sub-trees where left was old tree and right new tree
            self.root = MerkleTree.Node(root_hash, old_root, temp_root)
    
    # Iterates through the list of Nodes and connects them together in the Merkle Tree structure
    @staticmethod
    def build_help(datanodes):
        current_level = []
        for i in range(0, len(datanodes), 2):
            left = datanodes[i]
            # check if index out of range
            if i+1 != len(datanodes):
                right = datanodes[i+1]
            else:
                # if un-even concatenate left with itself to create parent hash
                right = left
            lrhash = hashlib.sha256(b'1'+left.data+right.data).digest()
            current_level += [MerkleTree.Node(lrhash, left, right)]
        
        # recursive base case, when one entry is left in list it's finished
        if len(current_level) != 1:
            return MerkleTree.build_help(current_level)
        else:
            return current_level[0]

    # Finds and returns the the path of a specified node in the tree by searching for it's data
    @staticmethod
    def find_d(tree, data, path=[]):
        # base case, leaf node reached if this is true
        if(tree.right == None):
            if(tree.left.data == data):
                # if data in leaf is the one we're looking for, return
                return path+[(0, hashlib.sha256(b'0'+tree.left.data).digest())]
            else:
                return None
        else:
            # recursively look through left sub-tree for data
            left_sub = MerkleTree.find_d(tree.left, data, path+[(0,tree.right.data)])
            if(left_sub == None):
                # if not found in left sub-tree recursively go through right one
                return MerkleTree.find_d(tree.right, data, path+[(1, tree.left.data)])
            return left_sub
    
    # Checks if the specified data exists in the tree
    def get_proof(self, data):
        path = MerkleTree.find_d(self.root, data)
        if(path == None):
            return False
        return path

    # Returns the root of the tree
    def get_root(self):
        return self.root.data

    # Verifies the proof by checking that the given path leads back to the root
    @staticmethod
    def verify_proof(root, proof):
        # last entry in proof list is bottom hash
        prev_hash = proof[-1][1]
        # loop through proof list computing each successive hash
        for i in range(len(proof)-2, -1, -1):
            if (proof[i][0] == 0):
                # current index is a right-node
                prev_hash = hashlib.sha256(b'1'+prev_hash+proof[i][1]).digest()
            else:
                # current index is a left-node
                prev_hash = hashlib.sha256(b'1'+proof[i][1]+prev_hash).digest()
        return prev_hash == root