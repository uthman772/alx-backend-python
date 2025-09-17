#!/usr/bin/env python3

nested_map={"a": 1}, path=("a",)
nested_map={"a": {"b": 2}}, path=("a",)
nested_map={"a": {"b": 2}}, path=("a", "b")
nested_map={"a": {"b": {"c": 3}}}, path=("a", "b", "c")
nested_map={"a": {"b": {"c": {"d": 4}}}}, path=("a", "b", "c", "d")
nested_map={"x": {"y": {"z": 0}}}, path=("x", "y", "z")
nested_map={"key1": {"key2": {"key3": "value"}}}, path=("key1", "key2", "
