
# JSON Key Comparator

Ferramenta simples para comparar keys (paths) entre dois arquivos JSON.

Coloque seus arquivos JSON na pasta `samples/` (por padrão o script lista os arquivos lá). Existem dois exemplos permitidos no repositório:

- `samples/example_base.json`
- `samples/example_compare.json`

Flags e comportamento:

- `--map-roots`: aplica o mapa de prefixos (definido no código) ao arquivo de comparação, salva uma cópia mapeada com sufixo `_mapped` e usa essa cópia para a comparação. Útil quando o arquivo compare usa siglas antigas (ex.: `CA`) e você quer normalizar para `ECA`.
- `--full-paths`: força exibição de todos os paths completos (comportamento "ALL").
- `--show-both`: imprime as duas visões, primeiro o resumo por raiz (`[ROOT]`) e depois a lista completa (`[ALL]`).

Exemplos de uso:

```bash
# visão agrupada por raiz (padrão)
python main.py example_base.json example_compare.json

# aplicar map-roots e ver só o resumo por raiz
python main.py --map-roots example_base.json example_compare.json

# aplicar map-roots e mostrar ambas as visões (ROOT e ALL)
python main.py --map-roots --show-both example_base.json example_compare.json

# mostrar apenas ALL (todos os paths completos)
python main.py --full-paths example_base.json example_compare.json
```

Comportamento do `--map-roots`:

1. O script aplica o mapeamento recursivamente nas chaves do arquivo de comparação.
2. Salva uma cópia com sufixo `_mapped` (ex.: `todas_materias_FINAL_compare_mapped.json`).
3. Usa o JSON mapeado para extrair keys e comparar com o arquivo base.

Marcações na saída:

- `[ROOT]`: resumo por chave raiz (agrupamento). Útil para ver quais objetos-pai faltam.
- `[ALL]`: lista completa de todos os paths diferentes (detalhado).
