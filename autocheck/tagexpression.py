# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-06-01.
#=============================================================================
#   tags.py --- Tags and tag expressions
#=============================================================================
import re


class TagExpressionParseError(Exception): pass

class TagExpression(object):
    tag_re = re.compile(r'@([\w_]+)$')
    negated_tag_re = re.compile(r'~@([\w_]+)$')
    
    def __init__(self):
        self.groups = None
        self.and_node = None
    
    def match(self, value):
        if self.and_node is None:
            return True
        else:
            return self.and_node.match(set(value))
    
    def parse_and_add(self, string):
        if self.and_node is None:
            self.and_node = AndNode()
        self.and_node.add_child(self.parse(string))
    
    def parse(self, string):
        tags = string.split(',')
        if len(tags) == 1:
            tag = tags[0]
            match = self.tag_re.match(tag.strip())
            if match:
                return TagNode(match.group(1))
            match = self.negated_tag_re.match(tag.strip())
            if match:
                return NegationNode(TagNode(match.group(1)))
            raise TagExpressionParseError(string)
        elif len(tags) == 0:
            raise TagExpressionParseError(string)
        else:
            return OrNode(map(self.parse, tags))


class TagNode(object):
    
    def __init__(self, name):
        self.name = name
    
    def match(self, value):
        return self.name in value


class TrueNode(object):
    
    def match(self, value):
        return True


class FalseNode(object):
    
    def match(self, value):
        return False


class NegationNode(object):
    
    def __init__(self, child):
        self.child = child
    
    def match(self, value):
        return not self.child.match(value)


class AndNode(object):
    
    def __init__(self, child_nodes=[]):
        self.child_nodes = list(child_nodes)
    
    def add_child(self, child):
        self.child_nodes.append(child)
    
    def match(self, value):
        for child in self.child_nodes:
            if not child.match(value):
                return False
        return True


class OrNode(object):
    
    def __init__(self, child_nodes):
        self.child_nodes = tuple(child_nodes)
    
    def match(self, value):
        for child in self.child_nodes:
            if child.match(value):
                return True
        return False

#.............................................................................
#   tags.py
