# pyrefly: ignore [missing-import]

import pandas as pd 


setlist = pd.read_csv('setlist.csv')
rows_with_nan = setlist[setlist.isna().any(axis=1)]

for index in rows_with_nan.index:
    actual = rows_with_nan.loc[index] #agarra la row complet
    print("-"*50)
    print(f"checando el índice {index} de la canción {actual.loc['Song']} del artista {actual.loc['Artist']}")
    print("-"*50)

    print("Opciones")
    print("1: Remplazar")
    print("2: Salir")

    choice = input("Seleciciones: ")
    if choice == "1":
        #iteration over every colummn in the index
        for column in actual.index: #se debe iterar sobre el index, porque ahora tiene una sola dimensión
            if pd.isnull(actual[column]) and column == "LastPlay":
                setlist.at[index, column] = "January 1, 2026"

            elif pd.isnull(actual[column]) and column in ["Tempo", "LastPlay"]:
                new_value = int(input(f"ponga el nuevo valor para {column}: "))
                #AGREGAMOS NUEVO VALOR AL SETLIST
                setlist.at[index, column] = new_value
            
            elif pd.isnull(actual[column]):
                new_value = input(f"ponga el nuevo valor para la columna {column}: ")
                #AGREGAMOS NUEVO VALOR AL SETLIST
                setlist.at[index, column] = new_value
            
    
    elif choice == "2":
        setlist.to_csv("setlist_clean.csv", index=False)
        print("setlist guardado")
        break