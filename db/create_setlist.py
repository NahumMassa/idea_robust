
import re

def _print_table(songs, artists, links):
    # HEADER con f-strings alineados (útil para visualización de datos en consola)
    print(f"{'CANCIÓN'} | {'ARTISTA'} | {'LINK'}")
    print("-" * 20)

    # zip() es O(n) y mucho más limpio que usar rangos e índices
    for song, artist, link in zip(songs, artists, links):
        print(f"{song} | {artist} | {link}")


def format(text):
  songs = []
  artists = []
  links = []
  counter = 0

  # Filter out empty lines and strip whitespace
  pattern = re.compile(r"^-+$") #busca patrones de "-" de cualquier longitud
  cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]



  for line in cleaned_lines:
      if pattern.match(line):
        counter += 1
      else:
        if counter == 0:
          songs.append(line)
        elif counter == 1:
          artists.append(line)
        else:
          links.append(line)

  _print_table(songs, artists, links)
  return (songs, artists, links)




text = """
    Por el poder de tu amor
    Tú mereces gloria (en A)
    Cantos de Júbilo
    Mi Gozo (En E)
    Él Es Más Grande (en B)
    ----
    Ingrid Rosario
    Juan Carlos Alvarado
    Jaime Murrel
    Barak
    Avivamiento
    ---
    https://youtu.be/Tssk5UWxvuw?si=6Tu8AYIb3SCKbHuL
    https://youtu.be/443LjjL_1bs?si=dhpO4c2zrWY1KQXu
    https://youtu.be/wchrgDmxzXw?si=Q-rycHgbcLQHt7q2
    https://youtu.be/IxD3JiOo9DY?si=A1lmh1HrkPnIfenz
    https://www.youtube.com/watch?v=c_7xEmW8RxM
  """

text2 = """
    Haz llover
    Preciosa Sangre
    Cantos de Júbilo
    Eres Fiel
    Sube, Sube
    ----
    Vino Nuevo
    Marco Barrientos
    Jaime Murrel
    Cristhian Hidall
    New Wine
    ---
    https://youtu.be/i0NjvZP-xp8?si=1wX6d0g_xNSj0XKP
    https://www.youtube.com/watch?v=6gO9rCFJ1wk
    https://youtu.be/wchrgDmxzXw?si=Q-rycHgbcLQHt7q2
    https://www.youtube.com/watch?v=O6JrDUyeVV4&list=PLFFUlmL5xmATnbG9wr_4SxaQom9Y0PZjk&index=8
    https://www.youtube.com/watch?v=izxfXTvv67U
  """
text3 = """
Eres Señor Vencedor
Abba Padre
Él es más grande
El poderoso de Israel
Grande y fuerte (Proezas)
---
Juan Carlos Alvarado
Marco Barrientos
Avivamiento
Juan Carlos Alvarado
Miel San Marcos
---
https://youtu.be/YgzL38Uh3z0?si=RwJbv-TRYr0CArYO
https://youtu.be/TzC42TFbB2Y?si=R4uiW-9e4d96t1XZ
https://www.youtube.com/watch?v=c_7xEmW8RxM
https://youtu.be/2cbVxPKaik4?si=fjG4yF0niQUsG_TO
https://youtu.be/WZC9RAk7dOI?si=ma74qgy1Kc5PNkRy
"""

if __name__ == "__main__":
  titles, artists, links = format(text2)  
  print(titles,artists,links)
