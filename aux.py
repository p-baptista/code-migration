import pandas as pd

# Suponha que 'df' é o seu DataFrame (planilha carregada)
# Exemplo: Carregando um arquivo Excel ou CSV
try:
    # ⚙️ Mude 'seu_arquivo.csv' e 'sua_planilha' conforme necessário
    df = pd.read_csv('input/python/Request-Urllib.csv') 
except FileNotFoundError:
    # Caso o arquivo não exista, criamos um DataFrame de exemplo para demonstração
    data = {'Nome': ['Alice', 'Bob', 'Charlie'],
            'Cidade': ['SP', 'RJ', 'BH']}
    df = pd.DataFrame(data)

# --- PASSO A PASSO PARA ADICIONAR O ID ---

# 1. (Opcional) Garante que o índice atual é sequencial de 0 a N-1
df = df.reset_index(drop=True) 

# 2. Cria a nova coluna 'ID'
# O índice do DataFrame (df.index) começa em 0.
# Ao somar 1 (df.index + 1), ele se torna 1, 2, 3...
df['ID'] = df.index + 1

# 3. (Opcional) Move a coluna 'ID' para a primeira posição
cols = ['ID'] + [col for col in df.columns if col != 'ID']
df = df[cols]

# 4. Exibe o resultado e salva (se necessário)
print("DataFrame com nova coluna 'ID':")
print(df)

# Se precisar salvar a nova planilha:
# df.to_csv('planilha_com_id.csv', index=False)