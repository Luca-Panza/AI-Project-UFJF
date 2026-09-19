# AI-Project-UFJF

## Problema: 4 Cavalos

Em um tabuleiro reduzido de 3x3, posicionam-se 2 cavalos brancos na primeira linha (cantos superior esquerdo e direito) e 2 cavalos pretos na última linha (cantos inferior esquerdo e direito). O quadrado central fica vazio.

- **Objetivo**: trocar a posição dos 4 cavalos no tabuleiro.
- **Movimento**: cada cavalo só pode andar fazendo um L (avançando duas casas na horizontal ou vertical e uma casa na direção perpendicular à primeira direção adotada).
- **Restrição**: duas peças não podem ocupar a mesma casa ao mesmo tempo.

## Modelagem

O tabuleiro 3x3 é numerado da seguinte forma:

```
1 2 3
4 5 6
7 8 9
```

- **Dicionário**: As peças `bx` e `by` são (brancas),`px` e `py` (pretas) e `None` para casa vazia.
- **Estado inicial**: `bx` na casa 1, `by` na casa 3, `px` na casa 7, `py` na casa 9.
- **Estado final**: peças pretas nas casas 1 e 3 e peças brancas nas casas 7 e 9, em qualquer combinação.
- **Regras de transição**: `RULES` define 16 regras (`r1` a `r16`), cada uma com um único movimento `(origem, destino)`; a regra só pode ser aplicada se a casa de origem tiver um cavalo e a casa de destino estiver vazia.

