#!/usr/bin/env python3
"""
Scraper de la tabla de posiciones - Liga de Primera Mercado Libre (ANFP / campeonatochileno.cl)

Cómo encuentra la tabla:
Busca todas las <table> de la página y se queda con la que tiene, en su encabezado,
las columnas PJ / V / E / D / GC / DG / PT. No depende de nombres de clase CSS
(esos pueden cambiar sin aviso en cualquier actualización del sitio).

Cómo lee cada fila:
- Nombre del club: el primer link <a> dentro de la fila.
- Escudo: el primer <img> dentro de la fila (src o data-src).
- Posición: el orden en que aparece la fila en la tabla, tal como la publica la ANFP
  (no se recalcula con puntos/diferencia de gol, porque puede haber descuentos de
  puntos por resoluciones del Tribunal de Disciplina que este script no puede conocer).
- PJ/V/E/D/GF/GC/DG/PT: los últimos 8 números enteros encontrados en la fila, en ese orden.
- Variación de posición (▲/▼): si el símbolo aparece como texto en la primera celda.
  Es un dato "best effort": si el sitio lo renderiza como ícono/imagen en vez de texto,
  este campo queda en null y no rompe el resto del scraping.

Si la tabla no se encuentra, o se extraen menos de 10 clubes, el script termina con
error (exit code 1) SIN escribir data.json. Así el workflow de GitHub Actions queda
marcado en rojo y nunca se publican datos incompletos o inventados.
"""

import json
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://www.campeonatochileno.cl/"
OUTPUT_FILE = "data.json"
EXPECTED_HEADERS = {"pj", "v", "e", "d", "gc", "dg", "pt"}
MIN_CLUBS_ESPERADOS = 10  # la Liga de Primera tiene 16, se deja margen por si algún club queda mal parseado


def find_standings_table(soup: BeautifulSoup):
    for table in soup.find_all("table"):
        sample_text = table.get_text(" ", strip=True)[:300].lower()
        tokens = set(re.findall(r"\b[a-záéíóúñ]+\b", sample_text))
        if EXPECTED_HEADERS.issubset(tokens):
            return table
    return None


def parse_row(row, position_index):
    cells = row.find_all(["td", "th"])
    if len(cells) < 6:
        return None

    club_link = row.find("a")
    if not club_link:
        return None
    club_name = club_link.get_text(strip=True)
    if not club_name:
        return None
    club_url = club_link.get("href")

    crest_img = row.find("img")
    crest_url = None
    if crest_img:
        crest_url = crest_img.get("src") or crest_img.get("data-src")
        if crest_url and crest_url.startswith("//"):
            crest_url = "https:" + crest_url

    text_cells = [c.get_text(" ", strip=True) for c in cells]
    numbers = [int(t) for t in text_cells if re.fullmatch(r"-?\d+", t)]
    if len(numbers) < 8:
        return None
    pj, v, e, d, gf, gc, dg, pt = numbers[-8:]

    first_cell_text = text_cells[0] if text_cells else ""
    movement = None
    if "▲" in first_cell_text:
        movement = "up"
    elif "▼" in first_cell_text:
        movement = "down"

    return {
        "pos": position_index,
        "movement": movement,
        "club": club_name,
        "club_url": club_url,
        "crest_url": crest_url,
        "pj": pj,
        "v": v,
        "e": e,
        "d": d,
        "gf": gf,
        "gc": gc,
        "dg": dg,
        "pt": pt,
    }


def main():
    resp = requests.get(
        URL,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; PulsoLaTerceraBot/1.0; +https://www.latercera.com)"},
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = find_standings_table(soup)
    if table is None:
        print("ERROR: no se encontró la tabla de posiciones. El sitio pudo haber cambiado de estructura.", file=sys.stderr)
        sys.exit(1)

    clubs = []
    position_counter = 0
    for row in table.find_all("tr"):
        position_counter_candidate = position_counter + 1
        parsed = parse_row(row, position_counter_candidate)
        if parsed:
            clubs.append(parsed)
            position_counter = position_counter_candidate

    if len(clubs) < MIN_CLUBS_ESPERADOS:
        print(
            f"ERROR: solo se extrajeron {len(clubs)} clubes (se esperaban ~16). "
            "Abortando para no publicar una tabla incompleta.",
            file=sys.stderr,
        )
        sys.exit(1)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "clubs": clubs,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(clubs)} clubes extraídos y guardados en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
