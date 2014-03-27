import re, os

class PatchFile(object):
    
    def __init__(self, path):
        self.path = path
        
        src_file = open(path)
        self.content = src_file.read()
        src_file.close()
        
    def insert(self, pattern, part, is_regexp=False, before=False):
        if is_regexp:
            reg = re.compile(pattern, re.DOTALL)
            m = reg.search(self.content)
            if before:
                insert_pos = m.start()
            else:
                insert_pos = m.end()
        else:
            pos = self.content.find(pattern)
            if before:
                insert_pos = pos
            else:
                insert_pos = pos + len(pattern)
    
        self.content = self.content[:insert_pos] + part + self.content[insert_pos:]

    def save(self):
        os.rename(self.path, self.path + ".old")
        src_file = open(self.path, 'w')
        src_file.write(self.content)
        src_file.close()
    
