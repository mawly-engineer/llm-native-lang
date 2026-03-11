#!/usr/bin/env python3
"""LND Format Validator - Validates .lnd files according to spec."""

import sys
import re
from pathlib import Path


class LNDError:
    def __init__(self, code, line, message, path):
        self.code = code
        self.line = line
        self.message = message
        self.path = path
    
    def __str__(self):
        return f"{self.path}:{self.line}: {self.code}: {self.message}"


def parse_yaml_lite(content):
    """Lightweight YAML parser for LND structure validation.
    
    Handles:
    - Basic key-value pairs
    - Nested dictionaries
    - Lists (both inline [a, b] and block style with - items)
    - Multi-line values with | and >
    """
    data = {}
    lines = content.split('\n')
    
    def get_indent(line):
        if not line.strip():
            return -1
        return len(line) - len(line.lstrip())
    
    def parse_value(val_str):
        val = val_str.strip()
        if val.startswith('"') and val.endswith('"') and len(val) > 1:
            return val[1:-1]
        if val.startswith("'") and val.endswith("'") and len(val) > 1:
            return val[1:-1]
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        if val.lower() == 'null' or val == '':
            return None
        if re.match(r'^-?\d+$', val):
            return int(val)
        return val
    
    def parse_block(start_idx, base_indent):
        """Parse a block of content starting at start_idx with given base_indent.
        Returns (result_dict, next_idx) where result_dict may contain _list key for root-level lists."""
        result = {}
        current_list = None
        current_list_key = None
        i = start_idx
        last_key = None
        
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            indent = get_indent(line)
            
            # If we've de-dented past base_indent, return to parent
            if indent < base_indent:
                # Finish current list if any
                if current_list is not None and current_list_key:
                    result[current_list_key] = current_list
                return result, i
            
            # List item at base_indent
            if indent == base_indent and stripped.startswith('- '):
                item_text = stripped[2:].strip()
                
                # Check if it's a dictionary item (key: value) or simple value
                if ': ' in item_text or item_text.endswith(':'):
                    # This is a dict in a list
                    if current_list is None:
                        current_list = []
                    
                    if ': ' in item_text:
                        key, val = item_text.split(': ', 1)
                        key = key.strip()
                        val = val.strip()
                        
                        if val == '' or val.startswith('#'):
                            # Value continues on next lines - parse nested block
                            i += 1
                            nested, i = parse_block(i, indent + 2)
                            current_list.append({key: nested if nested else None})
                        else:
                            current_list.append({key: parse_value(val)})
                    else:
                        # Key only - nested structure follows
                        key = item_text.rstrip(':').strip()
                        i += 1
                        nested, i = parse_block(i, indent + 2)
                        current_list.append({key: nested})
                    continue
                else:
                    # Simple list item
                    if current_list is None:
                        current_list = []
                    current_list.append(parse_value(item_text))
                i += 1
                continue
            
            # Key-value pair at base_indent
            if indent == base_indent and (': ' in stripped or stripped.endswith(':')):
                # Save previous list if any
                if current_list is not None and current_list_key:
                    result[current_list_key] = current_list
                    current_list = None
                    current_list_key = None
                
                if ': ' in stripped:
                    key, val = stripped.split(': ', 1)
                    key = key.rstrip(':').strip()
                    val = val.strip()
                    
                    # Check for comment and strip it
                    if ' #' in val:
                        val = val.split(' #')[0].strip()
                    
                    if val == '' or val.startswith('#'):
                        result[key] = None
                    elif val == '[]':
                        result[key] = []
                    elif val == '{}':
                        result[key] = {}
                    elif val.startswith('[') and val.endswith(']'):
                        # Inline list
                        items = []
                        inner = val[1:-1]
                        if inner.strip():
                            for item in inner.split(','):
                                items.append(parse_value(item))
                        result[key] = items
                    elif val in ['|', '>']:
                        # Multi-line value
                        i += 1
                        lines_content = []
                        while i < len(lines):
                            next_line = lines[i]
                            if not next_line.strip():
                                i += 1
                                continue
                            next_indent = get_indent(next_line)
                            if next_indent <= base_indent and lines[i].strip():
                                break
                            lines_content.append(next_line[base_indent + 2:])
                            i += 1
                        result[key] = '\n'.join(lines_content)
                        continue
                    else:
                        result[key] = parse_value(val)
                    last_key = key
                else:
                    # Key only - starts a nested structure or list
                    key = stripped.rstrip(':').strip()
                    last_key = key
                    # Check next line to determine if it's a list or dict
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.strip() and get_indent(next_line) > base_indent:
                            if next_line.strip().startswith('- '):
                                # It's a list
                                current_list = []
                                current_list_key = key
                            else:
                                # It's a nested dict
                                i += 1
                                nested, i = parse_block(i, indent + 2)
                                result[key] = nested
                                continue
                        else:
                            result[key] = {}
                i += 1
                continue
            
            # Nested content - skip to next iteration if at higher indent
            if indent > base_indent:
                # This shouldn't happen in normal flow - content should be consumed by parent
                i += 1
                continue
            
            # Unknown line at base_indent - skip it
            i += 1
        
        # End of file - save any pending list
        if current_list is not None and current_list_key:
            result[current_list_key] = current_list
        
        return result, i
    
    result, _ = parse_block(0, 0)
    return result


class LNDValidator:
    def __init__(self):
        self.errors = []
        self.seen_ids = set()
    
    def validate_file(self, filepath):
        path = Path(filepath)
        if not path.exists():
            self.errors.append(LNDError('LND_PARSE_001', 0, f"File not found: {filepath}", filepath))
            return False
        
        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        if not lines or not lines[0].startswith('@lnd'):
            self.errors.append(LNDError('LND_PARSE_001', 1, "Missing '@lnd <version>' header", filepath))
            return False
        
        header_match = re.match(r'^@lnd\s+(\d+\.\d+)$', lines[0])
        if not header_match:
            self.errors.append(LNDError('LND_PARSE_001', 1, "Invalid header format", filepath))
            return False
        
        version = header_match.group(1)
        if version != '0.2':
            self.errors.append(LNDError('LND_PARSE_001', 1, f"Unsupported version: {version}", filepath))
        
        # Check for tabs and hidden characters
        for i, line in enumerate(lines, 1):
            if '\t' in line:
                self.errors.append(LNDError('LND_PARSE_002', i, "Tab character detected", filepath))
        
        hidden_controls = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']
        for i, line in enumerate(lines, 1):
            for ctrl in hidden_controls:
                if ctrl in line:
                    self.errors.append(LNDError('LND_PARSE_005', i, "Hidden unicode control", filepath))
        
        yaml_content = '\n'.join(lines[1:])
        try:
            data = parse_yaml_lite(yaml_content)
        except Exception as e:
            self.errors.append(LNDError('LND_PARSE_001', 2, f"Parse error: {e}", filepath))
            return False
        
        if data is None:
            data = {}
        
        # Check required fields
        for field in ['kind', 'id']:
            if field not in data:
                self.errors.append(LNDError('LND_SCHEMA_001', 2, f"Missing required key: '{field}'", filepath))
        
        if 'id' in data:
            id_val = str(data['id'])
            if not re.match(r'^[A-Z0-9-_]+$', id_val):
                self.errors.append(LNDError('LND_SCHEMA_004', 2, f"ID '{id_val}' invalid format", filepath))
            if id_val in self.seen_ids:
                self.errors.append(LNDError('LND_SCHEMA_003', 2, f"Duplicate ID: '{id_val}'", filepath))
            else:
                self.seen_ids.add(id_val)
        
        # Check for duplicate keys and invalid key names
        def check_keys(obj, depth=0, path=""):
            if depth > 8:
                return
            if isinstance(obj, dict):
                keys_seen = set()
                for key in obj.keys():
                    if not isinstance(key, str):
                        continue
                    if not re.match(r'^[a-zA-Z0-9_]+$', key):
                        self.errors.append(LNDError('LND_PARSE_004', 2, f"Invalid key: '{key}'", filepath))
                    if key in keys_seen:
                        self.errors.append(LNDError('LND_PARSE_003', 2, f"Duplicate key: '{key}'", filepath))
                    keys_seen.add(key)
                    check_keys(obj[key], depth + 1, f"{path}.{key}")
            elif isinstance(obj, list):
                for item in obj:
                    check_keys(item, depth + 1, path)
        
        check_keys(data)
        return len(self.errors) == 0
    
    def validate_directory(self, dirpath):
        path = Path(dirpath)
        if not path.exists():
            print(f"Error: Directory not found: {dirpath}", file=sys.stderr)
            return False
        
        lnd_files = list(path.rglob('*.lnd'))
        if not lnd_files:
            print(f"No .lnd files found in {dirpath}")
            return True
        
        all_valid = True
        for lnd_file in sorted(lnd_files):
            if not self.validate_file(str(lnd_file)):
                all_valid = False
        return all_valid
    
    def print_errors(self):
        for error in self.errors:
            print(str(error), file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path>", file=sys.stderr)
        sys.exit(1)
    
    target = sys.argv[1]
    validator = LNDValidator()
    
    path = Path(target)
    if path.is_file():
        valid = validator.validate_file(target)
    else:
        valid = validator.validate_directory(target)
    
    if not valid:
        validator.print_errors()
        print(f"\nValidation failed: {len(validator.errors)} error(s)", file=sys.stderr)
        sys.exit(1)
    else:
        print("Validation passed: all LND files are valid")
        sys.exit(0)


if __name__ == '__main__':
    main()
