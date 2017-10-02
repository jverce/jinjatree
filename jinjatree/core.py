import os
import re

from anytree import (
    Node,
    RenderTree)
from anytree.dotexport import RenderTreeGraph


PATTERN = r'(extends|include|from) [\"\'](.*?)[\"\']'


class JinjaTree:

    RELATIONSHIP_PATTERN = r'(extends|include|from) [\"\'](.*?)[\"\']'

    def __init__(self, location):
        self.nodes = []
        self.jinjas = []
        self.location = location
        self.current_node = None
        self.root = None

        self.initialize()

    @property
    def orphan_nodes(self):
        return (node for node in self.nodes if node.is_root)

    def load_jinjas(self):
        for path, name, filenames in os.walk(self.location):
            normalized_path = path.replace(self.location, '')[1:]
            self.jinjas += [
                (f'{path}/{f}', f'{normalized_path}/{f}')
                for f in filenames if f.endswith('.jinja')
            ]

    def process_content(self, content):
        matches = re.findall(self.RELATIONSHIP_PATTERN, content)
        for relationship, name in matches:
            node, created = self.find_or_create(name)
            if relationship == 'extends':
                self.current_node.parent = node
                continue
            if relationship == 'include':
                if not created:
                    node = Node(name)
                node.parent = self.current_node

    def build_nodes(self):
        for path, jinja in self.jinjas:
            self.current_node, _ = self.find_or_create(jinja)
            with open(path, 'r') as f:
                content = f.read()
                self.process_content(content)

    def adopt_orphan_nodes(self):
        self.root = Node('templates')
        for node in self.orphan_nodes:
            node.parent = self.root

    def find_or_create(self, jinja):
        found = (node for node in self.nodes if node.name == jinja)

        try:
            return next(found), False
        except StopIteration:
            node = Node(jinja)
            self.nodes.append(node)
            return node, True

    def initialize(self):
        self.load_jinjas()
        self.build_nodes()
        self.adopt_orphan_nodes()

    def render(self):
        for pre, fill, node in RenderTree(self.root):
            print(f'{pre}{node.name}')

    def render_image(self, name):
        RenderTreeGraph(self.root).to_picture(name)
