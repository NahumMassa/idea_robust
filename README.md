# Migración de la db en Notion a PostgreSQL

## Este proyecto integra 3 tecnologias
1. Base de datos en postgres
2. Dashboard interactivo en streamlit
3. Program de CLI para subir y dar formato al setlist 

## Objetivo de la migración
El objetivo de esta migración es poder tener más control de manera histórica de las canciones que se tocan en los servicios y de los usuarios que las solicitan. 
Poder sacar métricas de:
1. Cuantas veces se ha tocado una canción a lo largo del tiempo
2. Tener un control estricto sobre los resgistro
3. Tener un mejor manejo sobre la información el dashboard (Ya que se creará uno)

En general, tener un control más análitico y de más manejable

## Data Defininition Language
La base de datos cuenta con las siguientes tablas:
![alt text](image.png)

### songs
| id | title | artist_id | genre_id | tempo | tone | link_yt |
|----|-------|-----------|----------|-------|------|---------|
| SERIAL | VARCHAR | INT | INT | INT | VARCHAR | TEXT |

Tabla principal para poder visualizar los contenidos de los setslists
imporante!!
esta tabla contiene un constraint en (title, link_yt), por qué?
Es para poder evitar el registro de la misma canción dos veces. Esto es especialmente útil en la tabla performance.


Ob
### artist
| id | name |
|----|------|
| SERIAL | VARCHAR |

### genre
| id | name |
|----|------|
| SERIAL | VARCHAR | 
Tambien se le conoce como "estilo", es el ritmo que lleva la canción 

### performance
| id | song_id | played_at |
|----|---------|-----------|
| SERIAL | INT | DATE |

Esta es la que se encargar de llevar el registro histórico de cuantas veces se toca una canción

## Se dejará de usar Notion?
No, para nada, pero cambiará en enfoque. Notion servirá poder visualizar las canciones y armar el setlist de cada semana. Se eliminarán las columnas, ahora inncesarias (Tone, LastPlay, TimesPlayed    ).

## Enfoque histórico de los registros
### Problema con Notion
Hay dos problemas con la DB anterior (Notion), la primera es que no tiene un registro histórico (fecha en la que se tocaron las canciones), por lo que al momento de migrar la base de datos, se tendrá que iniciar desde 0, pero no será un problema ya que se podrá ir registrando los servicios futuros. 


El segundo problema Es que el csv esta lleno de Nan (valors vacíos). Para resolver este problema se encontraron estas dos soluciones. Recordemos que la tabal en Notion tiene las siguientes columnas: 

| Song | Artist | Genre | LastPlay | Tempo | TimesPlayed | Tone | link |
|------|--------|-------|----------|-------|-------------|------|------|

En notion hay 48 canciones que tienes valores vacíos. Pueden ser que falten uno o más campos de un canción.
Dada la naturaleza de la información, estos tiene que ser llenados a manos. Para limpiar el csv y tener solo la información valida:
1. Se creó un script que permite explorar la información y llenarla de manera interactiva en python.
2. Hacaer webscrapping para poner conseguir los links de youtube (columna link) mediante el título de la canción y del artista





## Data Manipulation Language (script de python)
### Cómo se hizo la migración?
1. Creación script ETL de Notion -> PostgreSQL
Se hizo un script de python para poder extraer los datos de Notion y subirlos a la base de datos en PostgreSQL.
Hay un problema mayor co