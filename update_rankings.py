import json
import re
import requests
from bs4 import BeautifulSoup


def clean_text(text):
  if not text:
    return ""
  text = re.sub(r"\[\d+\]", "", text)
  text = re.sub(
      r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
      "",
      text,
  )
  text = re.sub(r"\s*-\s*$", "", text)
  text = re.sub(r"\s*\(\s*\)", "", text)
  return text.strip()


def format_fighter_cell(cell_text):
  cleaned = clean_text(cell_text)
  if not cleaned or cleaned.lower() == "vacant":
    return "vacant"

  # Pattern to match record format like "34-2", "27-0-1", or "21-1" inside the string
  match = re.search(
      r"(\d+\s*[-–]\s*\d+(?:\s*[-–]\s*\d+)?(?:\s*\(\s*\d+\s*\))?)", cleaned
  )
  if match:
    record = match.group(1).strip()
    name = cleaned.replace(record, "").strip()
    name = re.sub(r"\s*\(.*?\)", "", name).strip()  # remove leftover notes like Super champion
    if name and record:
      return f"{name}<br>{record}"

  return cleaned


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
      prev = table.find_previous(["h3", "h4", "span"])
      if prev:
        headline = prev.find("span", {"class": "mw-headline"})
        raw_head = headline.get_text() if headline else prev.get_text()
        weight_name = (
            raw_head.split("(")[0]
            .replace("Men's", "")
            .replace("Women's", "")
            .strip()
        )

      for row in rows[1:]:
        cols = row.find_all(["th", "td"])
        if len(cols) >= 5:
          pot_weight = cols[0].get_text(strip=True)
          if (
              "lb" in pot_weight
              or "kg" in pot_weight
              or "Heavyweight" in pot_weight
              or "Cruiserweight" in pot_weight
              or "Middleweight" in pot_weight
              or "Welterweight" in pot_weight
              or "Light" in pot_weight
              or "Featherweight" in pot_weight
              or "Bantamweight" in pot_weight
              or "Flyweight" in pot_weight
              or "Strawweight" in pot_weight
          ):
            weight_name = pot_weight.split("(")[0].strip()
            wba = format_fighter_cell(cols[1].get_text(strip=True))
            wbc = format_fighter_cell(cols[2].get_text(strip=True))
            ibf = format_fighter_cell(cols[3].get_text(strip=True))
            wbo = format_fighter_cell(cols[4].get_text(strip=True))
          else:
            wba = format_fighter_cell(cols[0].get_text(strip=True))
            wbc = format_fighter_cell(cols[1].get_text(strip=True))
            ibf = format_fighter_cell(cols[2].get_text(strip=True))
            wbo = format_fighter_cell(cols[3].get_text(strip=True))

          boxing_data.append({
              "weight": weight_name,
              "wba": wba,
              "wbc": wbc,
              "ibf": ibf,
              "wbo": wbo,
          })
          break
  return boxing_data


def scrape_ufc():
  url = "https://en.wikipedia.org/wiki/UFC_rankings"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  ufc_data = []
  tables = soup.find_all("table", {"class": "wikitable"})

  for table in tables:
    rows = table.find_all("tr")
    if len(rows) < 3:
      continue

    weight_name = ""
    caption = table.find("caption")
    if caption:
      weight_name = caption.get_text(strip=True)
    else:
      prev = table.find_previous(["h3", "h4", "span"])
      if prev:
        headline = prev.find("span", {"class": "mw-headline"})
        raw_head = headline.get_text() if headline else prev.get_text()
        weight_name = (
            raw_head.replace("Men's", "")
            .replace("Women's", "")
            .replace("rankings", "")
            .strip()
        )

    if not weight_name or weight_name.lower() in [
        "pound-for-pound",
        "pound for pound",
    ]:
      continue

    champion = "Vacant"
    rankings = []

    for row in rows:
      cols = row.find_all(["th", "td"])
      row_text = row.get_text()

      if len(cols) >= 2:
        rank_text = cols[0].get_text(strip=True)
        fighter_name = clean_text(cols[1].get_text(strip=True))

        if "C" == rank_text or rank_text.startswith("C\n") or "Champion" in row_text:
          if fighter_name and fighter_name != "Fighter":
            champion = fighter_name
        elif rank_text.isdigit():
          if fighter_name and fighter_name != champion:
            rankings.append(fighter_name)

    if weight_name:
      ufc_data.append({
          "weight": weight_name,
          "champion": champion,
          "rankings": rankings[:10],
      })

  return ufc_data


if __name__ == "__main__":
  data = {"boxing": scrape_boxing(), "ufc": scrape_ufc()}

  with open("rankings.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
  print("Successfully updated rankings.json with proper divisions and records.")
