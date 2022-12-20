"""
main.py: třetí projekt do Engeto Online Python Akademie
author: Pavel Šmíd
email: 78.78@seznam.cz
discord: Pavel Šmíd#2969

"""

#Elections scraper#
###################


import os
import csv
import requests
import bs4
import argparse


mesta = []
href = []


def odkaz(odkaz_1, odkaz_2, znak_1):

    # return vrací odkaz na stránku obce

    odkaz_2 = odkaz_2[znak_1 : odkaz_2[znak_1 : len(odkaz_2)].find('"') + znak_1]
    odkaz_2 = odkaz_1 + odkaz_2.replace("amp;", "")
    return odkaz_2


def mesta_hledej():

    odezva = requests.get("https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ")
    print(odezva)
    if odezva.status_code == 200:
        skok = -1
        soup = bs4.BeautifulSoup(odezva.text, "html.parser")
        for item in soup.find_all("td"):
            skok += 1
            if len(item.get_text()) > 1 and not item.get_text().startswith("CZ"):
                mesta.append(item.get_text())
                skok = 0
            if skok == 2:
                href.append(
                    odkaz(
                        "https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&",
                        str(item.find("a")),
                        28,
                    )
                )


def obec_hledej(i):

    # dle sys.argv[1] vyhledá všechny obce a linky na detailní výsledky voleb
    # proměnná skok zajišťuje přeskakování řádků dle obsahu proměnné soup
    # return vrací dict klíč je název obce a hodnnota je list 2 hodnoty, číslo # obce a link na výsledky voleb

    obec_dict = {}
    obec_cislo = ""
    obec_odkaz = ""
    odezva = requests.get(href[i])
    soup = bs4.BeautifulSoup(odezva.text, "html.parser")
    skok = -1
    for item in soup.find_all("td"):
        skok += 1
        if len(item.get_text()) > 1 and item.get_text().isnumeric():
            obec_cislo = str(item.get_text())
            obec_odkaz = odkaz(
                "https://volby.cz/pls/ps2017nss/", str(item.find("a")), 9
            )
            skok = 0
        if skok == 1:
            obec_jmeno = str(item.get_text())
            obec_dict[obec_jmeno] = [obec_cislo, obec_odkaz]

    return obec_dict


def zapis_csv(obec_dict, fname):

    hlavicka_csv = [
        "Kód obce",
        "Název obce",
        "Voliči v seznamu",
        "Vydané obálky",
        "Platné hlasy",
    ]
    vystup_csv = []

    soubor_csv = open(fname, "w", encoding="UTF8", newline="")
    zapisovac_csv = csv.writer(soubor_csv)

    def tabulka_csv_1(tab: bs4.element.ResultSet):

        hlavicka = [header.text for header in tab[0].find_all("th")]
        hlavicka.insert(1, "Zprac.")
        hlavicka.insert(2, "Zprac %")
        strany = [
            {hlavicka[i]: cell.text for i, cell in enumerate(row.find_all("td"))}
            for row in tab[0].find_all("tr")
        ]
        return strany

    def tabulka_csv_2_3(tab: bs4.element.ResultSet):

        strany = []
        hlavicka = ["Poradi", "Nazev", "Hlasy", "Hlasy %", "Link"]
        for k in range(1, 3):
            strany.extend(
                [
                    {
                        hlavicka[i]: cell.text
                        for i, cell in enumerate(row.find_all("td"))
                    }
                    for row in tab[k].find_all("tr")
                ][2:]
            )

        return strany

    for i, obec in enumerate(obec_dict):
        pracuji = ["*", " ", "*", " "]
        odezva = requests.get(obec_dict[obec][1])
        vystup_csv.clear()
        soup = bs4.BeautifulSoup(odezva.text, "html.parser")
        tabulka = soup.find_all("table")
        vystup_csv = [obec_dict[obec][0], obec]
        vysledek = tabulka_csv_1(tabulka)
        vystup_csv.extend(
            [
                vysledek[2]["Voličiv seznamu"],
                vysledek[2]["Vydanéobálky"],
                vysledek[2]["Platnéhlasy"],
            ]
        )
        vysledek.clear()
        vysledek = tabulka_csv_2_3(tabulka)
        if i == 0:
            hlavicka_csv.extend([strana["Nazev"] for strana in vysledek])
            zapisovac_csv.writerow(hlavicka_csv)
        vystup_csv.extend([strana["Hlasy %"] for strana in vysledek])
        zapisovac_csv.writerow(vystup_csv)
        print(pracuji[i % 4], end="\r")
    soubor_csv.close()
    print(" ", end="\r")
    print("Požadavek zpracován.")


def main(mesto, soubor):

    mesta_hledej()

    try:
        inx = mesta.index(mesto)
    except ValueError:
        print("Špatně zadaný uzemní celek " + '"' + mesto + '"!')
        return
    if soubor in os.listdir():
        print('Tento soubor "' + soubor + '" již existuje!')
        return

    obec = obec_hledej(inx)
    zapis_csv(obec, soubor)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mesto",
        help="Zadej název územního celku (mesto), první písmeno velké a s diakritikou např.: 'Benešov'.",
    )
    parser.add_argument(
        "--soubor",
        help="Zadej název nového souboru s příponou .csv, kam se uloží detailní výsledky voleb např.: 'vysledky_voleb2017_benesov.csv'.",
    )

    args = parser.parse_args()

    main(args.mesto, args.soubor)
