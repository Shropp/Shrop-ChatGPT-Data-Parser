import os
import json
from bisect import insort
import abc
from abc import abstractmethod, ABC

class TreeNode(ABC):
    '''
    This class is a simple tree mixin.
    '''
    @abstractmethod
    def __lt__(self, other):
        '''
        This has to be implemented in subclasses.
        '''
        pass

    def __init__(self, parent=None, children=None):
        self.parent = parent
        self.children = children if children != None else []

    def assign_child(self, child):
        '''
        This adds the child to this node's children and sets this node as the
        child's parent.
        '''
        insort(self.children, child)
        child.parent = self

    def assign_parent(self, parent):
        '''
        This updates the parent on the current node and adds this node to
        the children of its parent.
        '''
        self.parent = parent
        insort(parent.children, self)

    def path(self):
        '''
        This determines the path you must follow to get to the current node.
        '''
        path = []

        node = self

        while node.parent:
            if len(node.parent.children) > 1:
                path.insert(0, node.parent.children.index(node) + 1)

            node = node.parent

        return path

class DataNode(TreeNode):
    '''
    This class is a subclass of TreeNode that stores specific data about a
    mapping in the json file.
    '''
    def __init__(self, slice, title, parent=None, children=None):
        super().__init__(parent, children)

        self.title = title
        self.parent_id = slice["parent"]
        self.children_ids = slice["children"]
        self.id = slice["id"]
        self.author = ""

        if not "id" in slice or not "message" in slice or not slice["message"]:
            self.valid = False
            return

        self.valid = True
        self.enabled = True

        self.author = slice["message"]["author"]["role"]
        self.content = slice["message"]["content"]["parts"][0]
        self.create_time = slice["message"]["create_time"]

    def __eq__(self, other):
        '''
        Allows for "in" checks.
        '''
        if type(other) == str:
            return self.id == other
        return self.id == other.id

    def __lt__(self, other):
        '''
        Compares nodes by creation time, useful for sorting.
        '''
        return self.create_time < other.create_time

    def is_parental_to(self, other):
        '''
        Checks if this node is an ancestor of the other node.
        '''
        node = other
        while node != None:
            if node.parent == self:
                return True

            node = node.parent

    def __repr__(self):
        '''
        This is what prints when you do print(node)
        '''
        return self.content if self.valid else self.id if self.id else "NONE"

    def path_and_title(self):
        '''
        This function returns the path and the title of the conversation for
        this node.
        '''
        path = self.path()

        return path, self.title

    def search_down(self, string):
        '''
        This function recursively searches for a given string by descending
        through its children (and itself).
        '''
        results = []

        if self.valid and string in self.content:
            results.append(self)

        for child in self.children:
            results += child.search_down(string)

        return results

class ChatDataParser():
    '''
    This is the main class to work with, having methods for building trees
    based on your conversations, querying key words, navigating paths,
    and printing out responses.
    '''
    def __init__(self, filename):
        '''
        This is the main class you will work with, you just need to pass
        the filename when you initialize.
        '''
        if not os.path.exists(filename):
            raise ValueError(f"File {filename} not found - cannot parse file!")

        with open(filename, "r") as fp:
            self.contents = json.load(fp)

        if not self.contents:
            print("Error: Data file improperly formatted, or is not a json!")

        self.trees = []

    def build_tree(self, append=True, *args):
        '''
        This function builds a tree based on the conversation input.
        You can pass several titles as strings or slices of the dictionary
        of contents that represents a conversation.
        '''
        roots = []

        for arg in args:
            root = None

            if type(arg) == str:
                convo = ""
                for cv in self.contents:
                    if cv["title"] == arg:
                        convo = cv
                        break

                if convo == "":
                    print(f"Failed to find conversation with name \"{arg}\"")
                    continue

            else:
                convo = arg

            title = convo["title"]

            queue = [list(convo["mapping"].keys())[0]]
            done = {}

            while queue:
                curr_id = queue.pop(0)

                node = DataNode(convo["mapping"][curr_id], title)

                if node.parent_id in done:
                    done[node.parent_id].assign_child(node)
                elif node.parent_id not in queue and node.parent_id:
                    queue.append(node.parent_id)
                
                for child_id in node.children_ids:
                    if child_id in done:
                        done[child_id].assign_parent(node)
                    elif child_id not in queue and child_id:
                        queue.append(child_id)

                done[curr_id] = node

            root = done[list(done.keys())[0]]

            while root.parent:
                root = root.parent

            if append and not root in self.trees:
                self.trees.append(root)

            roots.append(root)

        return roots

    def build_all_trees(self):
        '''
        This function builds all trees.
        '''
        self.build_tree(*self.contents)

    def search_for_string(self, string):
        '''
        This function can be used to query built trees for a certain
        line of text.
        '''
        results = []

        for tree in self.trees:
            results += tree.search_down(string)

        return results

    def build_text(self, tree, path):
        '''
        Creates text based on a given tree and path. When the path runs out,
        the function defaults to the last child.
        '''

        if type(tree) == str:
            # Getting root based on title
            root = None

            for self_tree in self.trees:
                if self_tree.title == tree:
                    root = self_tree

            if not root:
                print(f"Tree {tree} not found! Could not compile text.")
                return ""

        else:
            root = tree

        full_str = ""

        curr_node = root

        while True:
            # Compiling relevant text
            if curr_node.author == "user":
                full_str += "User:\n"
                full_str += curr_node.content + "\n\n"

            elif curr_node.author == "assistant":
                full_str += "Assistant:\n"
                full_str += curr_node.content + "\n\n"
            
            if not curr_node.children:
                break

            # Deciding next child
            if len(curr_node.children) > 1:
                if path:
                    curr_node = curr_node.children[path.pop(0) - 1]
                else:
                    curr_node = curr_node.children[-1]

            else:
                curr_node = curr_node.children[0]

        return full_str