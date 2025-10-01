import os, ast

PROJECT = "seguradora"

def all_py(root):
    for base, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(base, f)

def module_name(path):
    rel = os.path.relpath(path).replace("\\", "/")
    if rel.endswith(".py"):
        rel = rel[:-3]
    if rel.endswith("/__init__"):
        rel = rel[:-9]
    return rel.replace("/", ".")

def find_imports(pyfile):
    with open(pyfile, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=pyfile)
        except Exception:
            return set()
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods

# Mapeia módulos do pacote
modules = {module_name(p): p for p in all_py(PROJECT)}

# Quem importa o quê
imports = {}
for m, path in modules.items():
    imports[m] = find_imports(path)

# Marca módulos alcançáveis a partir do app
roots = [f"{PROJECT}.app"]
reachable = set()

def dfs(mod):
    if mod in reachable:
        return
    reachable.add(mod)
    # segue imports que pertencem ao pacote
    for im in imports.get(mod, []):
        pref = PROJECT  # só segue se for do pacote local
        for k in modules:
            if k == im or k.startswith(im + "."):
                dfs(k)

for r in roots:
    if r in modules:
        dfs(r)

unused = sorted(set(modules) - reachable)
print("Possivelmente não utilizados:")
for m in unused:
    print("-", m, "=>", modules[m])
