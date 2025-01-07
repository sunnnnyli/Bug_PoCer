def write_file(content, filepath):
    with open(filepath, "w") as file:
        file.write(content)

def read_file(filepath):
    if filepath is None:
        return None
    
    try:
        with open(filepath, "r") as file:
            content = file.read()
            return content
    except Exception:
        return ""
