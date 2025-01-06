def parse_raw_headers_as_snippet(raw_headers: str) -> str:
    """
    Parse raw headers (each header name on one line, value on the next line)
    into a Python dictionary, skipping HTTP/2 pseudo-headers (begin with ':').
    Then return a nicely formatted code snippet that defines this dictionary.
    """
    lines = [line.strip() for line in raw_headers.splitlines() if line.strip()]
    
    headers_dict = {}
    i = 0
    while i < len(lines):
        header_name = lines[i].rstrip(':')
        
        # Skip lines starting with ':' (HTTP/2 pseudo-headers)
        if header_name.startswith(':'):
            i += 2  # Skip the name line and the value line
            continue
        
        i += 1  # Move to the value line
        header_value = lines[i] if i < len(lines) else ''
        
        headers_dict[header_name] = header_value
        i += 1  # Move to the next header name
    
    # Build the dictionary snippet
    snippet_lines = ["headers = {"]
    for name, value in headers_dict.items():
        # Escape double quotes, backslashes, etc. if necessary
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
        snippet_lines.append(f'    "{name}": "{escaped_value}",')
    snippet_lines.append("}")
    
    return "\n".join(snippet_lines)


# ------------------ Example usage ------------------ #
if __name__ == "__main__":

#copy this from chrome headers overview at a request.


    raw = r"""
<<INPUT>>
"""

    result_snippet = parse_raw_headers_as_snippet(raw)
    print(result_snippet)
