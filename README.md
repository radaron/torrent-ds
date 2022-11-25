# Torrent-ds service

## Leírás
Torrentszerver applikáció Ncore-hoz. Képes kezelni az rss feed-eket illetve az Ncore ajánlott funkcióját.
Öszekapcsolható a Transmisison-al, ami le tudja tölteni a torrent tartalmát.

Funkciók:
* Periódikusan megnyitja a torrenteket az rss feed linkeket használva, és a meghatározott kategóriákat képes külön könyvtárakba letölteni. (Bármennyi rss link megadható)
* A konfigurációban meghatározott intervallum alatt leállítja az összes torrentet (pl.: napközben munka mellett) (opcionális)
* Meghatározott időnként letölti a staff által ajánlottnak jelölt torrenteket, kategóriánként beállított könyvtárakba (opcionális)


## Telepítés

```
pip install torrent-ds --upgrade --user
```
```
echo "[Unit]
Description=Torrent-ds service
After=multi-user.target
Conflicts=getty@tty1.service
[Service]
User=${USER}
Type=simple
Environment="LC_ALL=C.UTF-8"
Environment="LANG=C.UTF-8"
ExecStart=${HOME}/.local/bin/torrent-ds
[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/torrent-ds.service
```
```
sudo systemctl daemon-reload
sudo systemctl enable torrent-ds.service
sudo systemctl start torrent-ds.service
```

## Konfiguráció

Két fájl tartalmazza az összes konfigurációt a programhoz:
* $HOME/.config/torrent_ds/config.ini
* $HOME/.config/torrent_ds/credentials.ini

### config.ini
Minden szekció ([]-ben) kötelező mező (kivéve az rss), a többi lehet opcionális vagy kötelező.
```
[transmission]
authenticate = False  | Kötelező
                      | A lehetséges értékek: True és False.
                      | Értelemszerűen ha azonosításra van szükség: True.
                      | A hozzá tartozó azonosító adatokat a credentials.ini fájl
                      | [transmission] szekcióban kell definiálni
ip_address =          | Opcionális
                      | A transmission remote ip_címe
port =                | Opcionális
                      | A transmission remote port-ja. Az alapértelmezett: 9091
sleep_days =          | Opcionális
                      | A megadott napokon fog érvénybe lépni a sleep_time értéke
                      | 1:hétfő -> 7:vasárnap, ;-vel elválasztva. Pl.: 1;2;3;4;5
                      | vagyis hétfő,kedd,szerda,csütörtök,péntek. Ezeken a napokon
                      | fog végrehajtódni.
sleep_time =          | Opcionális
                      | A megadott intervallumban az aktuálisan futó torrenteket
                      | szünetelteti. A formátum: 00:00:00-00:00:00

[download]
retry_interval = 10   | Kötelező
                      | Az rss feed-ek ellenőrzési intervalluma másodperben

[recommended]         | A staff által ajánlottnak jelölt torrentek letöltése
                      | meghatározottan periódusonként.
enable = False        | Kötelező
                      | Lehetséges értékek True és False.
credential = cred1    | Kötelező
                      | Azonosító szekció a credentials.ini fájlban
categories =          | Opcionális
                      | ;-vel elválasztva a kategóriákat. A kategóriák az alábbiak lehetnek:
                      | movies;series;musics;games;books;programs;xxx
max_size = 3 GiB      | Opcionális
                      | Maximum limit. Az ennél nagyobb méretű torrenteket nem tölti le
                      | ajánlott módban. Lehetséges dimenziók: KiB, MiB, GiB, TiB.
                      | A helyes formátum: '<érték> <dimenzió>'
retry_interval = 5    | Kötelező
                      | Az ajánlott torrentek letöltésének gyakorisága (órában)
movies =              | A filmeket az itt megadott mappába tölti le pl: /home/osmc/Downloads/movies
series =              | A sorozatokat az itt megadott mappába tölti le pl: /home/osmc/Downloads/series
musics =              | A zenéket az itt megadott mappába tölti le pl: /home/osmc/Downloads/musics
games =               | A játékokat az itt megadott mappába tölti le pl: /home/osmc/Downloads/games
books =               | A könyveket az itt megadott mappába tölti le pl: /home/osmc/Downloads/books
programs =            | A filmeket az itt megadott mappába tölti le pl: /home/osmc/Downloads/programs
xxx =

[rss bookmark1]       | Az rss-el kezdődő szekció: [rss <szekciónév>] pl: [rss Bela_rss]
credential = cred1    | Kötelező
                      | Azonosító szekció a credentials.ini fájlban
url =                 | Kötelező, Rss url -> ncore könyvjelzők
limit =               | Letölthető torrentek száma havonta
movies =              | A filmeket az itt megadott mappába tölti le pl: /home/osmc/Downloads/movies
series =              | A sorozatokat az itt megadott mappába tölti le pl: /home/osmc/Downloads/series
musics =              | A zenéket az itt megadott mappába tölti le pl: /home/osmc/Downloads/musics
games =               | A játékokat az itt megadott mappába tölti le pl: /home/osmc/Downloads/games
books =               | A könyveket az itt megadott mappába tölti le pl: /home/osmc/Downloads/books
programs =            | A filmeket az itt megadott mappába tölti le pl: /home/osmc/Downloads/programs
xxx =

[rss bookmark2]       | Bármennyi rss szekció használható
credential = cred2
url =
movies =
series =
musics =
clips =
games =
books =
programs =
xxx =
```

### credentials.ini
Minden szekció opcionális és bárhogy elnevezhető. Fontos: A config.ini 'credential' neveit itt kell definiálni.
A username értéke legyen a felhasználónév és a raw_password a jelszó. A jelszó automatikusan títkosítva lesz
és visszakerül a password értékeként, a raw_password törlődik.
```
[transmission]      | Azonsító a Transmission-hoz. Ha az authenticate értéke True a config.ini-ben
user_name =         | Transmission felhasználónév
raw_password =      | Transmission jelszó
password =          | Titkosított jelszó. Automatikusan íródik ki

[cred1]             | Azonosító mező az Ncore-hoz. Bármilyen nevet kaphat pl.: [Bela]
user_name =         | Felhasználónév
raw_password =      | Jelszó
password =          | Titkosított jelszó.

[cred2]
user_name =
raw_password =
password =
```
## Használat
### torrent-ds service indítása
```
sudo systemctl start torrent-ds
```
### torrent-ds service megállítása
```
sudo systemctl stop torrent-ds
```
### logok megtekintése
```
journalctl -fu torrent-ds
```
### Bármilyen konfiguráció módosítása után újraindítás szükséges
```
sudo systemctl restart torrent-ds
```
