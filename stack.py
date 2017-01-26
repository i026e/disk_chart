#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Stack:
    def __init__(self):
        self.empty = True
        self.current = None
        self.stack_backward = []
        self.stack_forward = []

    def add(self, obj):
        if self.empty:
            self.current = obj
            self.empty = False
        else:
            self.stack_backward.append(self.current)
            self.stack_forward = []
            self.current = obj

    def clear(self):
        self.empty = True
        self.current = None
        self.stack_backward = []
        self.stack_forward = []

    def can_go_back(self):
        return len(self.stack_backward) > 0

    def can_go_forward(self):
        return len(self.stack_forward) > 0

    def full_back(self):
        while self.can_go_back():
            self.go_back()
        return self.current

    def full_forward(self):
        while self.can_go_forward():
            self.go_forward()
        return self.current

    def go_back(self):
        if self.can_go_back():
            self.stack_forward.append(self.current)
            self.current = self.stack_backward.pop(-1)
            return self.current

    def go_forward(self):
        if self.can_go_forward():
            self.stack_backward.append(self.current)
            self.current = self.stack_forward.pop(-1)
            return self.current

    def get_current(self):
        return self.current
