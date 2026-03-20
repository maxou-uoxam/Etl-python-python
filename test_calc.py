import pandas as pd

# Simule : mapping garde col_a et col_b, colonne calculée écrase col_a
df = pd.DataFrame({'col_a': ['hello', 'world'], 'col_b': [1, 2]})
print('Avant:', df.to_dict('list'))

# Colonne calculée qui remplace col_a (même nom)
expr = "df['col_a'].str.upper()"
df['col_a'] = eval(expr, {'df': df, 'pd': pd})
print('Après eval:', df.to_dict('list'))

# selected_columns avec doublon potentiel
selected = ['col_b', 'col_a', 'col_a']
seen = set()
deduped = []
for c in reversed(selected):
    if c not in seen and c in df.columns:
        seen.add(c)
        deduped.insert(0, c)
df = df[deduped]
print('Final:', df.to_dict('list'))
print('Colonnes:', list(df.columns))

# Test nouvelle colonne (pas de remplacement)
df2 = pd.DataFrame({'col_a': ['hello', 'world'], 'col_b': [1, 2]})
df2['col_a_upper'] = eval("df['col_a'].str.upper()", {'df': df2, 'pd': pd})
selected2 = ['col_a', 'col_b', 'col_a_upper']
seen2 = set()
deduped2 = []
for c in reversed(selected2):
    if c not in seen2 and c in df2.columns:
        seen2.add(c)
        deduped2.insert(0, c)
df2 = df2[deduped2]
print('\nNouvelle colonne:', df2.to_dict('list'))
print('OK')
