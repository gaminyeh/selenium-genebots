<!-- README for selenium‑genebots -->
<h1 align="center">
  🧬 selenium‑genebots 🤖  
</h1>

<p align="center">
Automated, Selenium‑powered crawlers for harvesting gene & variant data from biomedical resources such as <a href="https://www.ncbi.nlm.nih.gov/clinvar/">NCBI ClinVar</a>, <a href="https://www.ncbi.nlm.nih.gov/snp/">NCBI dbSNP</a> and regional variant browsers.<br>
<em>Because even genomes deserve a friendly robot side‑kick.</em>
</p>

<p align="center">
  <!-- Badges are optional – remove or replace if you add CI later -->
  <img alt="Made with Python" src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python">
  <img alt="License"        src="https://img.shields.io/github/license/gaminyeh/selenium-genebots">
  <img alt="Stars"          src="https://img.shields.io/github/stars/gaminyeh/selenium-genebots?style=social">
</p>

---

## Table of Contents
1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features
- **Multi‑database support**  
  *ClinVar*, *dbSNP*, regional browsers (TaiwanView, Vietnamese browser, etc.) are each handled by a dedicated crawler script.
- **Headless or full‑GUI** Chrome/Chromium sessions via Selenium.
- **Container‑first workflow** – one‑line spin‑up using `docker-compose`.
- **CSV output** ready for downstream analytics.

| Script                              | Target database                                              | Input Fields              | Output Fields              |
| ----------------------------------- | ------------------------------------------------------------ | ------------------------- | -------------------------- |
| `ncbi-clinvar_automate_download.py` | [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)             |  disease name e.g. Best Macular dystrophy | download disease-related `Variation`, `Gene (Protein Change)`, `Type(Consequence)`, `Condition`, `Classification, Review status` of the disease into a text file    
| `ncbi-dbSNP_automate.py`            | [dbSNP](https://www.ncbi.nlm.nih.gov/snp/)                   |  rsID (a unique label of the specific SNP)           | `SNP position` in genome GRCh38 and GRCh37
| `taiwanview_automate.py`            | [TaiwanView](https://taiwanview.twbiobank.org.tw/variant.php)|  rsID (a unique label of the specific SNP)           | `Gene` and `Allele Frequency, AF` of SNP        
| `vietnamese_automate.py`            | [Vietnamese](https://genomes.vn/)                            |  rsID (a unique label of the specific SNP)           | `ALT`, `KHV`, `KHV-G` ,`Region` ,`Gene`, `Impact`, `AA Change` of SNP
---

## Project Structure
```text
selenium-genebots/
├── inputs/                                 # Example input of Gene variant or diseases lists
├── docker-compose.yml                      
├── Dockerfile                              
├── ncbi-clinvar_automate_download.py       # ClinVar crawler
├── ncbi-dbSNP_automate.py                  # dbSNP crawler
├── taiwanview_automate.py                  # Taiwan variant browser crawler
├── taiwanview_automate_xy.py               # Taiwan variant browser crawler for sex chromosome
├── vietnamese_automate.py                  # Vietnamese browser crawler
└── README.md                               # You are here 🙂
```

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/gaminyeh/selenium-genebots.git
cd selenium-genebots
```
### 2. Run in Docker
```bash
docker compose up --build
```
### 3. Running the Bots
| Script                              | Target database                                              | Example (with default `--input` from `./inputs`)    | 
| ----------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------- | 
| `ncbi-clinvar_automate_download.py` | [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)             | `docker compose exec selenium-genebots python ncbi-clinvar_automate_download.py` | 
| `ncbi-dbSNP_automate.py`            | [dbSNP](https://www.ncbi.nlm.nih.gov/snp/)                   | `docker compose exec selenium-genebots python ncbi-dbSNP_automate.py`            |
| `taiwanview_automate.py`            | [TaiwanView](https://taiwanview.twbiobank.org.tw/variant.php)| `docker compose exec selenium-genebots python taiwanview_automate.py`            |
| `vietnamese_automate.py`            | [Vietnamese](https://genomes.vn/)                            | `docker compose exec selenium-genebots python vietnamese_automate.py`            |

### 4. Outputs
Default: an output in outputs/ screenshot photo(.png) in screenshots/ plus a verbose log in logs/.
```text
outputs/
└── clinvar_download/                # ncbi-clinvar output directory
└── rename_clinvar_download/         # ncbi-clinvar output directory
└── ncbi-dbSNP_example_output.csv    # ncbi-dbSNP output file
└── taiwanview_example_output.csv    # taiwanview output file 
└── vietnamese_example_output.csv    # vietnamese output file 

logs/
└── clinvar_automator_2025-06-16.log
└── dbSNP_automator_2025-06-16.log
└── taiwanview_automator_2025-06-16.log
└── vietnamese_automator_2025-06-16.log

screenshots/
└── 2025-06-16_clinvar_screenshot/
└── 2025-06-16_dbsnp_screenshot/
└── 2025-06-16_taiwanview_screenshot/
└── 2025-06-16_vietnamese_screenshot/
```
### 4. Using Your Own Input Data
You can run each bot with your own gene or variant list by specifying the --input and --output options.
```bash
docker compose exec selenium-genebots python ncbi-dbSNP_automate.py \
  --input ./inputs/your_input.csv \
  --output ./outputs/your_output.csv
```
Notes:

-Input files are typically in CSV or TXT format, depending on the crawler.

-The format and required columns may vary between crawlers. Use the example files in the inputs/ folder as a reference.

-The output will be saved to the path you provide with --output.

-To view all available options for a crawler script (with -h/--help):
```bash
docker compose exec selenium-genebots python ncbi-dbSNP_automate.py --help
```

## Contributing
★ Star the repo to show your support!

Fork → Feature branch → Pull Request.

Follow PEP 8 + ruff linting; run pre‑commit run --all-files before pushing.

## License
MIT © 2025 Gamin Yeh
“Bots may crawl, but knowledge should stay free.”


##  Disclaimer
This project is not affiliated with NCBI or any regional genome initiative.
Use responsibly and abide by each database’s terms of service.