"""
scripts/build_college_db.py — JoSAA Cutoff Data Extractor

Reads JoSAA Round 6 (closing rank) Excel files from 2022–2024 and builds
a clean college database with real cutoff ranks.

Usage:
    python backend/scripts/build_college_db.py

Output:
    backend/data/colleges_josaa.json
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

import openpyxl

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
EXCEL_DIR = PROJECT_ROOT / "JEE and NEET csv files"
OUTPUT_FILE = BACKEND_DIR / "data" / "colleges_josaa.json"

# Round 6 files (closing ranks) — 2024 only has Round 5
ROUND6_FILES = [
    "2022Round6.xlsx",
    "2023Round6.xlsx",
    "2024Round5.xlsx",  # 2024 final round
]

# ── Institute name canonicalization ───────────────────────────────────────────
INSTITUTE_MAP = {
    "Indian Institute of Technology Bombay": "IIT Bombay",
    "Indian Institute of Technology Delhi": "IIT Delhi",
    "Indian Institute of Technology Madras": "IIT Madras",
    "Indian Institute of Technology Kanpur": "IIT Kanpur",
    "Indian Institute of Technology Kharagpur": "IIT Kharagpur",
    "Indian Institute of Technology Roorkee": "IIT Roorkee",
    "Indian Institute of Technology Guwahati": "IIT Guwahati",
    "Indian Institute of Technology Hyderabad": "IIT Hyderabad",
    "Indian Institute of Technology Indore": "IIT Indore",
    "Indian Institute of Technology (BHU) Varanasi": "IIT BHU Varanasi",
    "Indian Institute of Technology Bhubaneswar": "IIT Bhubaneswar",
    "Indian Institute of Technology Gandhinagar": "IIT Gandhinagar",
    "Indian Institute of Technology Jodhpur": "IIT Jodhpur",
    "Indian Institute of Technology Patna": "IIT Patna",
    "Indian Institute of Technology Ropar": "IIT Ropar",
    "Indian Institute of Technology Mandi": "IIT Mandi",
    "Indian Institute of Technology (ISM) Dhanbad": "IIT ISM Dhanbad",
    "Indian Institute of Technology Bhilai": "IIT Bhilai",
    "Indian Institute of Technology Goa": "IIT Goa",
    "Indian Institute of Technology Jammu": "IIT Jammu",
    "Indian Institute of Technology Dharwad": "IIT Dharwad",
    "Indian Institute of Technology Tirupati": "IIT Tirupati",
    "Indian Institute of Technology Palakkad": "IIT Palakkad",
    
    "National Institute of Technology Tiruchirappalli": "NIT Trichy",
    "National Institute of Technology, Tiruchirappalli": "NIT Trichy",
    "National Institute of Technology Karnataka, Surathkal": "NIT Surathkal",
    "National Institute of Technology Rourkela": "NIT Rourkela",
    "National Institute of Technology, Rourkela": "NIT Rourkela",
    "National Institute of Technology Warangal": "NIT Warangal",
    "National Institute of Technology, Warangal": "NIT Warangal",
    "National Institute of Technology Calicut": "NIT Calicut",
    "National Institute of Technology Durgapur": "NIT Durgapur",
    "National Institute of Technology Jamshedpur": "NIT Jamshedpur",
    "National Institute of Technology, Jamshedpur": "NIT Jamshedpur",
    "National Institute of Technology Kurukshetra": "NIT Kurukshetra",
    "National Institute of Technology, Kurukshetra": "NIT Kurukshetra",
    "National Institute of Technology Silchar": "NIT Silchar",
    "National Institute of Technology, Silchar": "NIT Silchar",
    "National Institute of Technology Srinagar": "NIT Srinagar",
    "National Institute of Technology, Srinagar": "NIT Srinagar",
    "National Institute of Technology Hamirpur": "NIT Hamirpur",
    "National Institute of Technology Jalandhar": "NIT Jalandhar",
    "National Institute of Technology Patna": "NIT Patna",
    "National Institute of Technology Raipur": "NIT Raipur",
    "National Institute of Technology Agartala": "NIT Agartala",
    "National Institute of Technology Arunachal Pradesh": "NIT Arunachal Pradesh",
    "National Institute of Technology, Arunachal Pradesh": "NIT Arunachal Pradesh",
    "National Institute of Technology Delhi": "NIT Delhi",
    "National Institute of Technology Goa": "NIT Goa",
    "National Institute of Technology Manipur": "NIT Manipur",
    "National Institute of Technology, Manipur": "NIT Manipur",
    "National Institute of Technology Meghalaya": "NIT Meghalaya",
    "National Institute of Technology Mizoram": "NIT Mizoram",
    "National Institute of Technology, Mizoram": "NIT Mizoram",
    "National Institute of Technology Nagaland": "NIT Nagaland",
    "National Institute of Technology Puducherry": "NIT Puducherry",
    "National Institute of Technology Sikkim": "NIT Sikkim",
    "National Institute of Technology Uttarakhand": "NIT Uttarakhand",
    "National Institute of Technology, Uttarakhand": "NIT Uttarakhand",
    "National Institute of Technology, Andhra Pradesh": "NIT Andhra Pradesh",
    "Visvesvaraya National Institute of Technology, Nagpur": "VNIT Nagpur",
    "Maulana Azad National Institute of Technology Bhopal": "MANIT Bhopal",
    "Motilal Nehru National Institute of Technology Allahabad": "MNNIT Allahabad",
    "Sardar Vallabhbhai National Institute of Technology, Surat": "SVNIT Surat",
    "Dr. B R Ambedkar National Institute of Technology, Jalandhar": "NIT Jalandhar",
    "Malaviya National Institute of Technology Jaipur": "MNIT Jaipur",
    
    "Indian Institute of Information Technology Allahabad": "IIIT Allahabad",
    "Indian Institute of Information Technology Gwalior": "IIIT Gwalior",
    "Indian Institute of Information Technology Jabalpur": "IIIT Jabalpur",
    "Indian Institute of Information Technology Kancheepuram": "IIIT Kancheepuram",
    "Indian Institute of Information Technology, Design & Manufacturing, Kurnool": "IIITDM Kurnool",
    "Indian Institute of Information Technology, Design & Manufacturing, Jabalpur": "IIITDM Jabalpur",
    "Indian Institute of Information Technology (IIIT) Kota, Rajasthan": "IIIT Kota",
    "Indian Institute of Information Technology Vadodara": "IIIT Vadodara",
    "Indian Institute of Information Technology Nagpur": "IIIT Nagpur",
    "Indian Institute of Information Technology Pune": "IIIT Pune",
    "Indian Institute of Information Technology Kottayam": "IIIT Kottayam",
    "Indian Institute of Information Technology Tiruchirappalli": "IIIT Trichy",
    "Indian Institute of Information Technology Sri City, Chittoor": "IIIT Sri City",
    "Indian Institute of Information Technology Lucknow": "IIIT Lucknow",
    "Indian Institute of Information Technology Dharwad": "IIIT Dharwad",
    "Indian Institute of Information Technology Bhagalpur": "IIIT Bhagalpur",
    "Indian Institute of Information Technology Bhopal": "IIIT Bhopal",
    "Indian Institute of Information Technology Surat": "IIIT Surat",
    "Indian Institute of Information Technology Ranchi": "IIIT Ranchi",
    "Indian Institute of Information Technology Kalyani": "IIIT Kalyani",
    "Indian Institute of Information Technology Sonepat": "IIIT Sonepat",
    "Indian Institute of Information Technology Manipur": "IIIT Manipur",
    "Indian Institute of Information Technology Agartala": "IIIT Agartala",
    
    "Birla Institute of Technology and Science, Pilani - Pilani Campus": "BITS Pilani",
    "Birla Institute of Technology and Science, Pilani - Goa Campus": "BITS Goa",
    "Birla Institute of Technology and Science, Pilani - Hyderabad Campus": "BITS Hyderabad",
    
    "Delhi Technological University": "DTU Delhi",
    "Netaji Subhas University of Technology": "NSUT Delhi",
    "Indraprastha Institute of Information Technology, Delhi": "IIIT Delhi",
}

# ── Branch name mapping ───────────────────────────────────────────────────────
BRANCH_MAP = {
    "Computer Science and Engineering": "CS",
    "Computer Science & Engineering": "CS",
    "Computer Science and Engineering (4 Years, Bachelor of Technology)": "CS",
    "Computer Science and Engineering (Artificial Intelligence and Machine Learning)": "CS",
    "Computer Science and Engineering (Data Science)": "CS",
    "Computer Science and Engineering with specialization in Artificial Intelligence and Machine Learning": "CS",
    "Artificial Intelligence and Data Science": "CS",
    "Artificial Intelligence": "CS",
    "Data Science and Artificial Intelligence": "CS",
    
    "Electronics and Communication Engineering": "Electronics",
    "Electronics & Communication Engineering": "Electronics",
    "Electronics and Communication Engineering (4 Years, Bachelor of Technology)": "Electronics",
    "Electronics and Electrical Communication Engineering": "Electronics",
    "Electrical and Electronics Engineering": "Electronics",
    "Electronics Engineering": "Electronics",
    "Electronics and Instrumentation Engineering": "Electronics",
    "Electronics and Computer Engineering": "Electronics",
    
    "Electrical Engineering": "Electrical",
    "Electrical Engineering (4 Years, Bachelor of Technology)": "Electrical",
    "Electrical Engineering (Power and Automation)": "Electrical",
    
    "Mechanical Engineering": "Mechanical",
    "Mechanical Engineering (4 Years, Bachelor of Technology)": "Mechanical",
    "Manufacturing Science and Engineering": "Mechanical",
    "Production and Industrial Engineering": "Mechanical",
    
    "Civil Engineering": "Civil",
    "Civil Engineering (4 Years, Bachelor of Technology)": "Civil",
    "Civil and Infrastructure Engineering": "Civil",
    
    "Chemical Engineering": "Chemical",
    "Chemical Engineering (4 Years, Bachelor of Technology)": "Chemical",
    "Chemical Science and Technology": "Chemical",
    
    "Aerospace Engineering": "Aerospace",
    "Aerospace Engineering (4 Years, Bachelor of Technology)": "Aerospace",
    
    "Biotechnology": "Biotechnology",
    "Biological Sciences and Bioengineering": "Biotechnology",
    "Biomedical Engineering": "Biotechnology",
    
    "Metallurgical and Materials Engineering": "Metallurgy",
    "Metallurgical Engineering": "Metallurgy",
    "Materials Science and Engineering": "Metallurgy",
    
    "Engineering Physics": "Engineering Physics",
    "Mathematics and Computing": "Mathematics and Computing",
}


def normalize_branch(program_name: str) -> Optional[str]:
    """Map a JoSAA program name to a canonical branch code."""
    # Direct match first (most reliable)
    if program_name in BRANCH_MAP:
        return BRANCH_MAP[program_name]
    
    # Fuzzy match with strict rules to avoid false positives
    program_lower = program_name.lower()
    
    # CS: must explicitly mention "computer science" or "artificial intelligence" or "data science"
    # Do NOT match "Mathematics and Computing" here (it has its own category)
    if ("computer science" in program_lower or 
        "computer engineering" in program_lower or
        "artificial intelligence" in program_lower or 
        "data science" in program_lower):
        # Exclude dual degrees with other branches
        if "mechanical" in program_lower or "civil" in program_lower:
            return None
        return "CS"
    
    # Electronics: must mention "electronics" or "communication" or "ece"
    if ("electronics" in program_lower or 
        "communication engineering" in program_lower or 
        "ece" in program_lower):
        return "Electronics"
    
    # Electrical: must mention "electrical" but NOT "electronics"
    if "electrical" in program_lower and "electronics" not in program_lower:
        return "Electrical"
    
    # Mechanical: must mention "mechanical" or "manufacturing" or "production"
    if ("mechanical" in program_lower or 
        "manufacturing" in program_lower or 
        "production" in program_lower):
        return "Mechanical"
    
    # Civil: must mention "civil"
    if "civil" in program_lower:
        return "Civil"
    
    # Chemical: must mention "chemical"
    if "chemical" in program_lower:
        return "Chemical"
    
    # Aerospace: must mention "aerospace" or "aeronautical"
    if "aerospace" in program_lower or "aeronautical" in program_lower:
        return "Aerospace"
    
    # Biotechnology: must mention "bio" in the context of engineering
    if ("biotechnology" in program_lower or 
        "bioengineering" in program_lower or 
        "biomedical" in program_lower):
        return "Biotechnology"
    
    # Metallurgy: must mention "metallurg" or "materials"
    if "metallurg" in program_lower or "materials science" in program_lower:
        return "Metallurgy"
    
    # Engineering Physics: exact match only
    if "engineering physics" in program_lower:
        return "Engineering Physics"
    
    # Mathematics and Computing: exact match only
    if "mathematics and computing" in program_lower:
        return "Mathematics and Computing"
    
    # If none of the above, return None (skip this program)
    return None


def get_rank_type(institute_name: str) -> str:
    """Determine if the institute uses JEE Advanced or JEE Main ranks."""
    if "IIT" in institute_name and "IIIT" not in institute_name:
        return "jee_advanced"
    return "jee_main"


def get_location(institute_name: str) -> str:
    """Extract location from institute name."""
    # City/state extraction
    locations = {
        "Bombay": "Maharashtra",
        "Mumbai": "Maharashtra",
        "Delhi": "Delhi",
        "Madras": "Tamil Nadu",
        "Chennai": "Tamil Nadu",
        "Kanpur": "Uttar Pradesh",
        "Kharagpur": "West Bengal",
        "Roorkee": "Uttarakhand",
        "Guwahati": "Assam",
        "Hyderabad": "Telangana",
        "Indore": "Madhya Pradesh",
        "Varanasi": "Uttar Pradesh",
        "Bhubaneswar": "Odisha",
        "Gandhinagar": "Gujarat",
        "Jodhpur": "Rajasthan",
        "Patna": "Bihar",
        "Ropar": "Punjab",
        "Mandi": "Himachal Pradesh",
        "Dhanbad": "Jharkhand",
        "Bhilai": "Chhattisgarh",
        "Goa": "Goa",
        "Jammu": "Jammu and Kashmir",
        "Dharwad": "Karnataka",
        "Tirupati": "Andhra Pradesh",
        "Palakkad": "Kerala",
        "Tiruchirappalli": "Tamil Nadu",
        "Trichy": "Tamil Nadu",
        "Surathkal": "Karnataka",
        "Rourkela": "Odisha",
        "Warangal": "Telangana",
        "Calicut": "Kerala",
        "Durgapur": "West Bengal",
        "Jamshedpur": "Jharkhand",
        "Kurukshetra": "Haryana",
        "Silchar": "Assam",
        "Srinagar": "Jammu and Kashmir",
        "Hamirpur": "Himachal Pradesh",
        "Jalandhar": "Punjab",
        "Raipur": "Chhattisgarh",
        "Agartala": "Tripura",
        "Arunachal Pradesh": "Arunachal Pradesh",
        "Manipur": "Manipur",
        "Meghalaya": "Meghalaya",
        "Mizoram": "Mizoram",
        "Nagaland": "Nagaland",
        "Puducherry": "Puducherry",
        "Sikkim": "Sikkim",
        "Uttarakhand": "Uttarakhand",
        "Nagpur": "Maharashtra",
        "Bhopal": "Madhya Pradesh",
        "Allahabad": "Uttar Pradesh",
        "Surat": "Gujarat",
        "Jaipur": "Rajasthan",
        "Gwalior": "Madhya Pradesh",
        "Jabalpur": "Madhya Pradesh",
        "Kancheepuram": "Tamil Nadu",
        "Kurnool": "Andhra Pradesh",
        "Kota": "Rajasthan",
        "Vadodara": "Gujarat",
        "Pune": "Maharashtra",
        "Kottayam": "Kerala",
        "Sri City": "Andhra Pradesh",
        "Chittoor": "Andhra Pradesh",
        "Lucknow": "Uttar Pradesh",
        "Bhagalpur": "Bihar",
        "Ranchi": "Jharkhand",
        "Kalyani": "West Bengal",
        "Sonepat": "Haryana",
        "Pilani": "Rajasthan",
    }
    
    for city, state in locations.items():
        if city in institute_name:
            return state
    
    return "India"


def get_tier(institute_name: str, branch: str) -> str:
    """Assign a tier based on institute prestige."""
    name_lower = institute_name.lower()
    
    # Elite: Top 7 IITs + BITS Pilani
    if any(x in name_lower for x in ["iit bombay", "iit delhi", "iit madras", "iit kanpur", "iit kharagpur", "iit roorkee", "iit guwahati"]):
        return "elite"
    if "bits pilani" in name_lower and "pilani" in institute_name:
        return "elite"
    
    # Premium: Other old IITs, top NITs, BITS campuses, IIIT Hyderabad/Delhi
    if "iit" in name_lower and "iiit" not in name_lower:
        return "premium"
    if any(x in name_lower for x in ["nit trichy", "nit surathkal", "nit warangal", "nit rourkela", "nit calicut"]):
        return "premium"
    if "bits" in name_lower:
        return "premium"
    if any(x in name_lower for x in ["iiit hyderabad", "iiit delhi", "iiit allahabad"]):
        return "premium"
    if "dtu" in name_lower or "nsut" in name_lower:
        return "premium"
    
    # Good: Other NITs, IIITs
    if "nit" in name_lower or "iiit" in name_lower:
        return "good"
    
    return "average"


def get_fees(institute_name: str) -> int:
    """Estimate annual fees based on institute type."""
    name_lower = institute_name.lower()
    if "iit" in name_lower and "iiit" not in name_lower:
        return 200000  # ₹2L/year
    if "nit" in name_lower:
        return 150000  # ₹1.5L/year
    if "iiit" in name_lower:
        return 180000  # ₹1.8L/year
    if "bits" in name_lower:
        return 500000  # ₹5L/year (private)
    if "dtu" in name_lower or "nsut" in name_lower:
        return 180000
    return 200000


def get_placement_avg(institute_name: str, branch: str) -> int:
    """Estimate average placement package."""
    name_lower = institute_name.lower()
    
    # Elite IITs CS
    if branch == "CS" and any(x in name_lower for x in ["iit bombay", "iit delhi", "iit madras", "iit kanpur"]):
        return 2800000  # ₹28 LPA
    
    # Elite IITs other branches
    if any(x in name_lower for x in ["iit bombay", "iit delhi", "iit madras", "iit kanpur"]):
        return 1800000  # ₹18 LPA
    
    # Other IITs CS
    if branch == "CS" and "iit" in name_lower and "iiit" not in name_lower:
        return 2000000  # ₹20 LPA
    
    # Other IITs
    if "iit" in name_lower and "iiit" not in name_lower:
        return 1500000  # ₹15 LPA
    
    # Top NITs CS
    if branch == "CS" and any(x in name_lower for x in ["nit trichy", "nit surathkal", "nit warangal"]):
        return 1800000
    
    # Top NITs
    if any(x in name_lower for x in ["nit trichy", "nit surathkal", "nit warangal"]):
        return 1200000
    
    # Other NITs CS
    if branch == "CS" and "nit" in name_lower:
        return 1400000
    
    # Other NITs
    if "nit" in name_lower:
        return 1000000
    
    # BITS
    if "bits" in name_lower:
        return 1600000
    
    # IIITs
    if "iiit" in name_lower:
        return 1200000
    
    return 1000000


def get_accreditation(institute_name: str) -> str:
    """Assign accreditation based on institute type."""
    name_lower = institute_name.lower()
    if "iit" in name_lower and "iiit" not in name_lower:
        return "NAAC A++"
    if "nit" in name_lower or "bits" in name_lower:
        return "NAAC A+"
    if "iiit" in name_lower:
        return "NAAC A"
    return "NAAC A"


def get_established(institute_name: str) -> Optional[int]:
    """Return establishment year for known institutes."""
    years = {
        "IIT Bombay": 1958,
        "IIT Delhi": 1961,
        "IIT Madras": 1959,
        "IIT Kanpur": 1959,
        "IIT Kharagpur": 1951,
        "IIT Roorkee": 1847,
        "IIT Guwahati": 1994,
        "IIT Hyderabad": 2008,
        "NIT Trichy": 1964,
        "NIT Surathkal": 1960,
        "NIT Warangal": 1959,
        "BITS Pilani": 1964,
        "DTU Delhi": 1941,
    }
    return years.get(institute_name)


# ── Main extraction logic ─────────────────────────────────────────────────────

def extract_cutoffs() -> dict[tuple[str, str], list[int]]:
    """
    Extract closing ranks from all Round 6 Excel files.
    Returns: {(canonical_name, branch): [rank_2022, rank_2023, rank_2024]}
    """
    cutoffs: dict[tuple[str, str], list[int]] = defaultdict(list)
    
    for filename in ROUND6_FILES:
        filepath = EXCEL_DIR / filename
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            continue
        
        logger.info(f"Reading {filename}...")
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        
        rows = list(ws.rows)
        header = [cell.value for cell in rows[0]]
        
        # Find column indices
        try:
            institute_idx = header.index("Institute")
            program_idx = header.index("Academic Program Name")
            seat_type_idx = header.index("Seat Type")
            gender_idx = header.index("Gender")
            closing_rank_idx = header.index("Closing Rank")
        except ValueError as e:
            logger.error(f"Missing column in {filename}: {e}")
            continue
        
        for row in rows[1:]:
            try:
                institute_raw = row[institute_idx].value
                program_raw = row[program_idx].value
                seat_type = row[seat_type_idx].value
                gender = row[gender_idx].value
                closing_rank = row[closing_rank_idx].value
                
                if not all([institute_raw, program_raw, seat_type, gender, closing_rank]):
                    continue
                
                # Filter: OPEN category, Gender-Neutral only
                if seat_type != "OPEN" or gender != "Gender-Neutral":
                    continue
                
                # Normalize institute name
                canonical_name = INSTITUTE_MAP.get(institute_raw, institute_raw)
                
                # Normalize branch
                branch = normalize_branch(program_raw)
                if not branch:
                    continue
                
                # Parse closing rank (handle "123P" format for PwD)
                if isinstance(closing_rank, str):
                    closing_rank = re.sub(r'[^\d]', '', closing_rank)
                    if not closing_rank:
                        continue
                    closing_rank = int(closing_rank)
                elif isinstance(closing_rank, (int, float)):
                    closing_rank = int(closing_rank)
                else:
                    continue
                
                # Sanity check
                if closing_rank < 1 or closing_rank > 500000:
                    continue
                
                key = (canonical_name, branch)
                cutoffs[key].append(closing_rank)
                
            except Exception as e:
                logger.debug(f"Skipping row: {e}")
                continue
        
        wb.close()
    
    return cutoffs


def build_college_db(cutoffs: dict[tuple[str, str], list[int]]) -> list[dict]:
    """Build the final college database with averaged cutoffs."""
    colleges = []
    skipped = 0
    
    for (institute_name, branch), ranks in cutoffs.items():
        if not ranks:
            skipped += 1
            continue
        
        # 3-year rolling average
        avg_rank = int(sum(ranks) / len(ranks))
        
        # Generate ID
        college_id = f"josaa_{institute_name.lower().replace(' ', '_')}_{branch.lower()}"
        
        # Build entry
        entry = {
            "id": college_id,
            "name": institute_name,
            "branch": branch,
            "cutoff_rank": avg_rank,
            "rank_type": get_rank_type(institute_name),
            "annual_fees": get_fees(institute_name),
            "location": get_location(institute_name),
            "tier": get_tier(institute_name, branch),
            "placement_avg": get_placement_avg(institute_name, branch),
            "accreditation": get_accreditation(institute_name),
            "established": get_established(institute_name),
        }
        
        colleges.append(entry)
    
    # Sort by cutoff_rank (best first)
    colleges.sort(key=lambda c: c["cutoff_rank"])
    
    logger.info(f"Built {len(colleges)} college entries. Skipped {skipped} incomplete entries.")
    return colleges


def validate_cutoffs(colleges: list[dict]) -> None:
    """Validate cutoff ranks and log warnings for suspicious data."""
    for college in colleges:
        rank = college["cutoff_rank"]
        name = college["name"]
        branch = college["branch"]
        rank_type = college["rank_type"]
        
        if rank_type == "jee_advanced":
            if rank < 50:
                logger.warning(f"Suspiciously low rank: {name} {branch} = {rank} (JEE Advanced)")
            elif rank > 20000:
                logger.warning(f"Suspiciously high rank: {name} {branch} = {rank} (JEE Advanced)")
        else:  # jee_main
            if rank < 100:
                logger.warning(f"Suspiciously low rank: {name} {branch} = {rank} (JEE Main)")
            elif rank > 500000:
                logger.warning(f"Suspiciously high rank: {name} {branch} = {rank} (JEE Main)")


def print_summary(colleges: list[dict]) -> None:
    """Print a summary of the generated database."""
    print("\n" + "="*80)
    print("JoSAA College Database Summary")
    print("="*80)
    
    print(f"\nTotal colleges: {len(colleges)}")
    
    # By rank type
    advanced = [c for c in colleges if c["rank_type"] == "jee_advanced"]
    main = [c for c in colleges if c["rank_type"] == "jee_main"]
    print(f"  JEE Advanced (IITs): {len(advanced)}")
    print(f"  JEE Main (NITs/IIITs/GFTIs): {len(main)}")
    
    # By branch
    branches = defaultdict(int)
    for c in colleges:
        branches[c["branch"]] += 1
    print(f"\nBy branch:")
    for branch, count in sorted(branches.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {count}")
    
    # Cutoff range
    ranks = [c["cutoff_rank"] for c in colleges]
    print(f"\nCutoff rank range: {min(ranks)} – {max(ranks)}")
    
    # Sample entries
    print(f"\nSample entries (top 10):")
    for c in colleges[:10]:
        print(f"  {c['name']:30} {c['branch']:15} Rank: {c['cutoff_rank']:6} ({c['rank_type']})")
    
    print("\n" + "="*80)


def main():
    logger.info("Starting JoSAA college database builder...")
    
    # Extract cutoffs
    cutoffs = extract_cutoffs()
    logger.info(f"Extracted cutoffs for {len(cutoffs)} (institute, branch) pairs")
    
    # Build database
    colleges = build_college_db(cutoffs)
    
    # Validate
    validate_cutoffs(colleges)
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(colleges, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote {len(colleges)} colleges to {OUTPUT_FILE}")
    
    # Print summary
    print_summary(colleges)
    
    logger.info("Done!")


if __name__ == "__main__":
    main()
