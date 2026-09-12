import json
import urllib.request

# In a production automated workflow, you could fetch from an external scraper 
# or a data source here. For now, this template handles writing the structure 
# programmatically so GitHub Actions can commit it.

updated_data = {
    "boxing": [
        { 
            "weight": "Heavyweight", 
            "champion": "Murat Gassiev (WBA) / Agit Kabayel (WBC)", 
            "rankings": [
                "Jarrell Miller (WBA) / Tyson Fury (WBC)", 
                "Tyson Fury (WBA) / Anthony Joshua (WBC)", 
                "Anthony Joshua (WBA) / Frank Sanchez (WBC)", 
                "Vartan Arutyunyan (WBA) / Deontay Wilder (WBC)", 
                "Nelson Hysa (WBA) / Moses Itauma (WBC)"
            ] 
        }
    ],
    "ufc": [
        {
            "weight": "Heavyweight",
            "champion": "Tom Aspinall",
            "rankings": [
                "Ciryl Gane", "Alexander Volkov", "Sergei Pavlovich", 
                "Curtis Blaydes", "Waldo Cortes Acosta", "Jailton Almeida", 
                "Marcin Tybura", "Derrick Lewis", "Tai Tuivasa", "Sergey Spivak"
            ]
        }
    ]
}

with open("rankings.json", "w") as f:
    json.dump(updated_data, f, indent=4)

print("rankings.json updated successfully via automation script.")
