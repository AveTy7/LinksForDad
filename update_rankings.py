import json
import re
import requests
from bs4 import BeautifulSoup


def clean_text(text):
  if not text:
    return ""
  return re.sub(r"\[.*?\]", "", text).strip()


def format_fighter_cell(cell_text):
  cleaned = clean_text(cell_text)
  if not cleaned or cleaned.lower() == "vacant":
    return "vacant"
  is_super = False
  if "super champion" in cleaned.lower():
    is_super = True
    cleaned = re.sub(r"super champion", "", cleaned, flags=re.IGNORECASE)
  match = re.search(
      r"(\d+\s*[-–]\s*\d+(?:\s*[-–]\s*\d+)?(?:\s*\(\s*\d+\s*\))?)", cleaned
  )
  record = ""
  if match:
    record = match.group(1).strip()
    cleaned = cleaned.replace(record, "").strip()
  name = re.sub(r"\s*\(.*?\)", "", cleaned).strip()
  if not name:
    return cleaned
  super_badge = (
      ' <span style="color: #fbbf24; font-size: 0.85em;" title="Super'
      ' Champion">★</span>'
      if is_super
      else ""
  )
  if record:
    return f"{name}{super_badge}<br>{record}"
  return f"{name}{super_badge}"


def scrape_ufc():
  url = "https://en.wikipedia.org/wiki/UFC_rankings"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  ufc_data = []
  divisions = [
      "Heavyweight",
      "Light Heavyweight",
      "Middleweight",
      "Welterweight",
      "Lightweight",
      "Featherweight",
      "Bantamweight",
      "Flyweight",
      "Women's Bantamweight",
      "Women's Flyweight",
      "Women's Strawweight",
  ]

  tables = soup.find_all("table", {"class": "wikitable"})
  valid_tables = []
  for table in tables:
    rows = table.find_all("tr")
    if len(rows) > 5:
      header_text = rows[0].get_text().lower()
      if "fighter" in header_text or "rank" in header_text or "iso" in header_text:
        valid_tables.append(table)

  for idx, table in enumerate(valid_tables):
    if idx >= len(divisions):
      break

    weight_name = divisions[idx]
    rows = table.find_all("tr")

    champion = "Vacant"
    rankings = []

    for row in rows:
      cols = row.find_all(["th", "td"])
      if len(cols) >= 3:
        # Search columns dynamically for rank and fighter name to handle new layout columns
        row_texts = [clean_text(c.get_text()) for c in cols]
        
        rank_text = ""
        fighter_name = ""
        
        for t in row_texts:
          if t in ["C", "IC"] or (t.isdigit() and 1 <= int(t) <= 15):
            rank_text = t
            break
            
        # The fighter name is usually the longest text field that isn't a number or record format
        for t in row_texts:
          if t and t != rank_text and not t.isdigit() and not re.match(r"^\d+[-–]\d+", t):
            if len(t) > 2 and "UFC" not in t and "Win" not in t and "Loss" not in t:
              fighter_name = t
              break

        if rank_text in ["C", "IC"]:
          if fighter_name and fighter_name.lower() != "fighter":
            champion = fighter_name
        elif rank_text.isdigit():
          rank_num = int(rank_text)
          if 1 <= rank_num <= 15:
            if fighter_name and fighter_name != champion and fighter_name.lower() != "fighter":
              if fighter_name not in rankings:
                rankings.append(fighter_name)

    ufc_data.append({
        "weight": weight_name,
        "champion": champion,
        "rankings": rankings[:10],
    })

  return ufc_data


def scrape_boxing():
  url = "https://en.wikipedia.org/wiki/List_of_current_world_boxing_champions"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  boxing_data = []
  tables = soup.find_all("table", {"class": "wikitable"})

  for table in tables:
    rows = table.find_all("tr")
    if len(rows) < 2:
      continue

    header_row = rows[0].get_text()
    if "WBA" in header_row and "WBC" in header_row:
      weight_name = "Division"
      prev = table.find_previous(["h3", "h4", "span", "th"])
      while prev:
        headline = (
            prev.find("span", {"class": "mw-headline"})
            if hasattr(prev, "find")
            else None
        )
        raw_head = headline.get_text() if headline else prev.get_text()
        cleaned_head = clean_text(raw_head)
        if cleaned_head and any(
            w in cleaned_head
            for w in [
                "weight",
                "Heavy",
                "Cruiser",
                "Light",
                "Middle",
                "Welter",
                "Feather",
                "Bantam",
                "Fly",
                "Straw",
            ]
        ):
          weight_name = (
              cleaned_head.split("(")[0]
              .replace("Men's", "")
              .replace("Women's", "")
              .strip()
          )
          break
        prev = prev.find_previous(["h3", "h4", "span", "th"])

      for row in rows[1:]:
        cols = row.find_all(["th", "td"])
        if len(cols) >= 5:
          pot_weight = clean_text(cols[0].get_text())
          if any(
              term in pot_weight
              for term in [
                  "lb",
                  "kg",
                  "Heavyweight",
                  "Cruiserweight",
                  "Middleweight",
                  "Welterweight",
                  "Light",
                  "Featherweight",
                  "Bantamweight",
                  "Flyweight",
                  "Strawweight",
              ]
          ):
            weight_name = pot_weight.split("(")[0].strip()
            wba = format_fighter_cell(cols[1].get_text())
            wbc = format_fighter_cell(cols[2].get_text())
            ibf = format_fighter_cell(cols[3].get_text())
            wbo = format_fighter_cell(cols[4].get_text())
          else:
            wba = format_fighter_cell(cols[0].get_text())
            wbc = format_fighter_cell(cols[1].get_text())
            ibf = format_fighter_cell(cols[2].get_text())
            wbo = format_fighter_cell(cols[3].get_text())

          boxing_data.append({
              "weight": weight_name,
              "wba": wba,
              "wbc": wbc,
              "ibf": ibf,
              "wbo": wbo,
          })
          break
  return boxing_data


if __name__ == "__main__":
  data = {"boxing": scrape_boxing(), "ufc": scrape_ufc()}

  with open("rankings.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
  print("Successfully updated rankings.json.")
