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
    """Lightweight YAML parser for LND structure validation."""
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
    
    def parse_lines(start_idx, base_indent, parent_dict, list_mode=False, list_key=None):
        i = start_idx
        current_list = None
        
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            indent = get_indent(line)
            
            if indent < base_indent:
                return i
            
            if list_mode:
                if stripped.startswith('- '):
                    val = stripped[2:].strip()
                    if ':' in val and not val.startswith('"') and not val.startswith("'"):
                        key, rest = val.split(':', 1)
                        key = key.strip()
                        rest = rest.strip()
                        
                        if isinstance(current_list, list):
                            if not current_list or key in current_list[-1]:
                                current_list.append({})
                            current_list[-1][key] = parse_value(rest) if rest else None
                    else:
                        if isinstance(current_list, list):
                            current_list.append(parse_value(val))
                    i += 1
                elif indent == base_indent:
                    return i
                else:
                    i = parse_lines(i, indent, parent_dict)
            else:
                if ':' in stripped:
                    key, rest = stripped.split(':', 1)
                    key = key.strip()
                    rest = rest.strip()
                    
                    if not rest or rest.startswith('#'):
                        parent_dict[key] = {}
                        i += 1
                        i = parse_lines(i, indent + 2, parent_dict[key])
                    elif rest == '[]':
                        parent_dict[key] = []
                        i += 1
                    elif rest.startswith('[') and rest.endswith(']'):
                        items = rest[1:-1].split(',')
                        parent_dict[key] = [parse_value(item) for item in items]
                        i += 1
                    else:
                        parent_dict[key] = parse_value(rest)
                        i += 1
                elif stripped.startswith('- '):
                    if list_key and isinstance(parent_dict.get(list_key), list):
                        val = stripped[2:].strip()
                        if ':' in val and not val.startswith('"') and not val.startswith("'"):
                            key, rest = val.split(':', 1)
                            key = key.strip()
                            rest = rest.strip()
                            
                            if not parent_dict[list_key] or key in parent_dict[list_key][-1]:
                                parent_dict[list_key].append({})
                            parent_dict[list_key][-1][key] = parse_value(rest) if rest else None
                        else:
                            parent_dict[list_key].append(parse_value(val))
                    i += 1
                else:
                    i += 1
        
        return i
    
    parse_lines(0, 0, data)
    return data


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
        
        for field in ['kind', 'id']:
            if field not in data:
                self.errors.append(LNDError('LND_SCHEMA_001', 2, f"Missing required key: '{field}'", filepath))
        
        if 'id' in data:
            id_val = str(data['id'])
            if not re.match(r'^[A-Z0-9-]+$', id_val):
                self.errors.append(LNDError('LND_SCHEMA_004', 2, f"ID '{id_val}' invalid format", filepath))
            if id_val in self.seen_ids:
                self.errors.append(LNDError('LND_SCHEMA_003', 2, f"Duplicate ID: '{id_val}'", filepath))
            else:
                self.seen_ids.add(id_val)
        
        def check_keys(obj, depth=0, path=""):
            if depth > 8:
                return
            if isinstance(obj, dict):
                keys_seen = set()
                for key in obj.keys():
                    if not isinstance(key, str):
                        continue
                    if not re.match(r'^[a-z0-9_]+$', key):
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
