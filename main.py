#!/usr/bin/env python3
"""Comparador de chaves JSON.

Uso: execute sem argumentos e siga as instruções, ou passe dois nomes de arquivos dentro da pasta samples:
    python main.py base.json compare.json

O script lista keys (paths) recursivamente e mostra as diferenças:
- Chaves presentes no primeiro (base) mas faltando no segundo: exibidas em verde
- Chaves presentes no segundo mas faltando no primeiro: exibidas em vermelho

"""
import json
import os
import sys
from typing import Any, Dict, Set, List


GREEN = "\x1b[32m"
RED = "\x1b[31m"
RESET = "\x1b[0m"


def collect_keys(obj: Any, prefix: str = "") -> Set[str]:
    """Recursively collect JSON key paths.

    - For dicts, append .key
    - For lists, include index as [i]
    Returns a set of string paths.
    """
    keys: Set[str] = set()

    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            keys.add(path)
            keys.update(collect_keys(v, path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            path = f"{prefix}[{i}]" if prefix else f"[{i}]"
            keys.add(path)
            keys.update(collect_keys(item, path))
    else:
        # primitives: nothing to add beyond the prefix (which is the key path to the value)
        pass

    return keys


def load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_keys(base_keys: Set[str], cmp_keys: Set[str]):
    only_in_base = sorted(base_keys - cmp_keys)
    only_in_cmp = sorted(cmp_keys - base_keys)
    return only_in_base, only_in_cmp


def _root_of_path(path: str) -> str:
    """Retorna a raiz do path (primeiro segmento antes de '.' ou '[').

    Ex: 'ETQ806.assignments[0].name' -> 'ETQ806'
    """
    if not path:
        return path
    # split by '.' first
    dot_split = path.split('.', 1)
    first = dot_split[0]
    # if the first contains a list index like 'something[0]', return before '['
    bracket_idx = first.find('[')
    if bracket_idx != -1:
        return first[:bracket_idx]
    return first


def _group_roots(paths: List[str]) -> List[str]:
    """If multiple paths share same root, return only the root once; otherwise keep full path.

    This function reduces a list of paths to a list where if more than one path
    has the same root, we show the root instead of multiple entries.
    """
    roots = {}
    for p in paths:
        r = _root_of_path(p)
        roots.setdefault(r, []).append(p)

    out = []
    for r, group in sorted(roots.items()):
        if len(group) > 1:
            out.append(r)
        else:
            out.append(group[0])
    return out


def print_differences(only_in_base: List[str], only_in_cmp: List[str], full_paths: bool = False):
    if not only_in_base and not only_in_cmp:
        print("Nenhuma diferença de chaves encontrada. Os dois JSONs têm as mesmas keys (paths).")
        return

    if only_in_base:
        print("\nChaves presentes no primeiro (base) mas faltando no segundo:")
        to_print = only_in_base if full_paths else _group_roots(only_in_base)
        tag = "[ALL]" if full_paths else "[ROOT]"
        for k in to_print:
            print(f"{GREEN}{tag} {k}{RESET}")

    if only_in_cmp:
        print("\nChaves presentes no segundo mas faltando no primeiro (base):")
        to_print = only_in_cmp if full_paths else _group_roots(only_in_cmp)
        tag = "[ALL]" if full_paths else "[ROOT]"
        for k in to_print:
            print(f"{RED}{tag} {k}{RESET}")


def print_both_views(only_in_base: List[str], only_in_cmp: List[str]):
    """Print both ROOT (grouped) and ALL (full paths) views, tagged."""
    # ROOT view
    print("\n[ROOT] — resumo por raiz:")
    root_base = _group_roots(only_in_base)
    root_cmp = _group_roots(only_in_cmp)
    if root_base:
        print("\nChaves presentes no primeiro (base) mas faltando no segundo:")
        for k in sorted(root_base):
            print(f"{GREEN}[ROOT] {k}{RESET}")
    if root_cmp:
        print("\nChaves presentes no segundo mas faltando no primeiro (base):")
        for k in sorted(root_cmp):
            print(f"{RED}[ROOT] {k}{RESET}")

    # ALL view
    print("\n[ALL] — lista completa de paths diferentes:")
    if only_in_base:
        print("\nChaves presentes no primeiro (base) mas faltando no segundo:")
        for k in sorted(only_in_base):
            print(f"{GREEN}[ALL] {k}{RESET}")
    if only_in_cmp:
        print("\nChaves presentes no segundo mas faltando no primeiro (base):")
        for k in sorted(only_in_cmp):
            print(f"{RED}[ALL] {k}{RESET}")


# mapping antigo -> novo para raízes
MAPA_ANTIGO_PARA_NOVO = {
    'AL': 'EAL', 'CA': 'ECA', 'CMP': 'ECM', 'EN': 'EEN', 'ET': 'EET',
    'MC': 'EMC', 'PM': 'EPM', 'QM': 'EQM', 'CV': 'ETC', 'RI': 'RIT',
    'ADM': 'ADM', 'DSG': 'DSG', 'CIC': 'CIC', 'SIN': 'SIN', 'ARQ': 'ARQ',
    'ICD': 'ICD'
}


def map_root_names(paths: List[str], mapa: Dict[str, str]) -> List[str]:
    """Substitui a raiz dos paths de acordo com o mapa.

    Ex: 'CA.something.x' com mapa {'CA':'ECA'} => 'ECA.something.x'
    Se a raiz não estiver no mapa, mantém a mesma.
    """
    out = []
    for p in paths:
        if not p:
            out.append(p)
            continue
        # encontrar root no path
        # root = parte antes do primeiro '.' ou '['
        root = p.split('.', 1)[0]
        bracket_idx = root.find('[')
        if bracket_idx != -1:
            root_key = root[:bracket_idx]
            suffix = root[bracket_idx:] + p[len(root):]
        else:
            root_key = root
            suffix = p[len(root):]

        new_root = mapa.get(root_key, root_key)
        new_path = new_root + suffix
        out.append(new_path)
    return out


def save_json_file(path: str, obj: Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def apply_map_to_keys(obj: Any, mapa: Dict[str, str]) -> Any:
    """Renomeia recursivamente as chaves do dicionário verificando uma correspondência EXATA no mapa.

    A regra: se uma chave de dicionário 'k' existir EXATAMENTE no `mapa`,
    ela é substituída pelo valor mapeado.
    """

    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if k in mapa:
                new_key = mapa[k]  # Ex: 'ET' é encontrado e vira 'EET'
            else:
                new_key = k  # Ex: 'ETQ801' não é encontrado e permanece 'ETQ801'

            new_obj[new_key] = apply_map_to_keys(v, mapa)
        return new_obj
    elif isinstance(obj, list):
        return [apply_map_to_keys(i, mapa) for i in obj]
    else:
        return obj


def find_samples_dir() -> str:
    cwd = os.getcwd()
    samples_path = os.path.join(cwd, "samples")
    if not os.path.isdir(samples_path):
        # try relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        samples_path = os.path.join(script_dir, "samples")
        if not os.path.isdir(samples_path):
            # create it
            os.makedirs(samples_path, exist_ok=True)
    return samples_path


def choose_file(prompt: str, samples_dir: str) -> str:
    files = [f for f in os.listdir(samples_dir) if f.lower().endswith('.json')]
    if not files:
        print(f"Nenhum arquivo JSON encontrado em {samples_dir}. Por favor adicione arquivos e tente novamente.")
        sys.exit(1)

    print(f"\nArquivos JSON em {samples_dir}:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f}")

    while True:
        choice = input(prompt).strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return os.path.join(samples_dir, files[idx])
        else:
            # allow direct filename
            candidate = os.path.join(samples_dir, choice)
            if os.path.isfile(candidate):
                return candidate

        print("Escolha inválida. Digite o número listado ou o nome do arquivo conforme mostrado.")


def main():
    samples_dir = find_samples_dir()

    # parse simple flags: --full-paths and --map-roots
    full_paths = False
    map_roots_flag = False
    show_both = False
    args = [a for a in sys.argv[1:] if a not in ('--full-paths', '--map-roots', '--show-both')]
    if '--full-paths' in sys.argv:
        full_paths = True
    if '--map-roots' in sys.argv:
        map_roots_flag = True
    if '--show-both' in sys.argv:
        show_both = True

    # support CLI args
    if len(args) >= 2:
        base_name = args[0]
        cmp_name = args[1]
        base_path = os.path.join(samples_dir, base_name) if not os.path.isabs(base_name) else base_name
        cmp_path = os.path.join(samples_dir, cmp_name) if not os.path.isabs(cmp_name) else cmp_name
    else:
        print("Comparador de chaves JSON. Os arquivos devem estar na pasta 'samples' (criada automaticamente).")
        base_path = choose_file("Escolha o número ou nome do JSON base: ", samples_dir)
        cmp_path = choose_file("Escolha o número ou nome do JSON a comparar: ", samples_dir)

    if not os.path.isfile(base_path):
        print(f"Arquivo base não encontrado: {base_path}")
        sys.exit(1)
    if not os.path.isfile(cmp_path):
        print(f"Arquivo a comparar não encontrado: {cmp_path}")
        sys.exit(1)

    base = load_json_file(base_path)
    cmp = load_json_file(cmp_path)

    # If requested, apply mapping to the compare file's keys and save a mapped copy
    if map_roots_flag:
        mapped_cmp = apply_map_to_keys(cmp, MAPA_ANTIGO_PARA_NOVO)
        # create mapped filename
        cmp_dir, cmp_file = os.path.split(cmp_path)
        name, ext = os.path.splitext(cmp_file)
        mapped_name = f"{name}_mapped{ext or '.json'}"
        mapped_path = os.path.join(cmp_dir or samples_dir, mapped_name)
        save_json_file(mapped_path, mapped_cmp)
        print(f"Arquivo de comparação mapeado salvo em: {mapped_path}")
        # use mapped object for comparison
        cmp = mapped_cmp

    base_keys = collect_keys(base)
    cmp_keys = collect_keys(cmp)

    # opcionalmente aplicar mapeamento nas raízes antes da comparação (normaliza chaves)
    if map_roots_flag:
        base_keys = set(map_root_names(list(base_keys), MAPA_ANTIGO_PARA_NOVO))
        cmp_keys = set(map_root_names(list(cmp_keys), MAPA_ANTIGO_PARA_NOVO))

    only_in_base, only_in_cmp = compare_keys(base_keys, cmp_keys)

    print(f"\nComparando:\n  Base: {base_path}\n  Comparado: {cmp_path}\n")
    if show_both:
        print_both_views(only_in_base, only_in_cmp)
    else:
        print_differences(only_in_base, only_in_cmp, full_paths=full_paths)


if __name__ == "__main__":
    main()
