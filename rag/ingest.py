# Import neecessary modules
from pathlib import Path
import re

# Read all .txt files
files = Path("../data/guidelines").glob("*.txt")

content = {}
for file in files:
    text = file.read_text()
    content[file] = text


# Split the texts in chunks
texts = []
metadatas = []
ids = []
counter = 0

for filename, text in content.items():
    chunks_of_this_file = text.split("\n## ")
    filename = Path(filename).name
    for chunk in chunks_of_this_file:
        clean = chunk.strip()
        url = re.search(r"https\S+", chunk)
        if clean:
            texts.append(clean)
            if url:
                meta = {"source": url.group(0), "filename": filename}
                metadatas.append(meta)
            else:
                meta = {"source": filename, "filename": filename}
                metadatas.append(meta)         
            ids.append(filename + "_" + str(counter))
            counter+=1
    

print(len(texts), len(metadatas), len(ids))


