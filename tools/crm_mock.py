"""
tools/crm_mock.py
Mock CRM data store.  In production this would call a real CRM API
(Salesforce, HubSpot, Dynamics 365) — see Section 5 design notes.
Provides realistic sample data for demonstration.
"""

import json
from pathlib import Path
from utils.logger import logger

# ── Embedded mock CRM records ─────────────────────────────────────────────────
_MOCK_CRM: list[dict] = [
    {
        "company": "Infosys",
        "country": "India",
        "account_status": "Prospect",
        "last_contact": "2024-11-10",
        "contact_name": "Rajesh Kumar",
        "contact_title": "VP of Engineering",
        "notes": "Interested in AI automation solutions. Had intro call in Q4 2024.",
        "estimated_deal_size": "$250,000",
        "stage": "Discovery",
        "tags": ["AI", "enterprise", "India"],
    },
    {
        "company": "Tata Consultancy Services",
        "country": "India",
        "account_status": "Customer",
        "last_contact": "2025-01-15",
        "contact_name": "Priya Sharma",
        "contact_title": "Director of Procurement",
        "notes": "Active customer. Renewal due Q2 2025. Upsell opportunity in cloud migration.",
        "estimated_deal_size": "$1,200,000",
        "stage": "Renewal",
        "tags": ["cloud", "enterprise", "India"],
    },
    {
        "company": "Wipro",
        "country": "India",
        "account_status": "Churned",
        "last_contact": "2024-06-01",
        "contact_name": "Amit Patel",
        "contact_title": "CTO",
        "notes": "Chose competitor solution. Pain point was integration complexity.",
        "estimated_deal_size": "$500,000",
        "stage": "Closed-Lost",
        "tags": ["India", "integration", "competitor"],
    },
]


def crm_lookup(company: str, country: str) -> list[dict]:
    """
    Fuzzy-match company name against mock CRM records.
    Returns matching records formatted as document dicts.
    """
    company_lower = company.lower()
    country_lower = country.lower()
    matches = []

    for record in _MOCK_CRM:
        crm_company = record["company"].lower()
        crm_country = record["country"].lower()
        # Simple substring match — production would use fuzzy matching
        if company_lower in crm_company or crm_company in company_lower:
            if not country_lower or country_lower in crm_country or crm_country in country_lower:
                content = (
                    f"CRM Record — {record['company']} ({record['country']})\n"
                    f"Account Status: {record['account_status']}\n"
                    f"Last Contact: {record['last_contact']}\n"
                    f"Primary Contact: {record['contact_name']} — {record['contact_title']}\n"
                    f"Deal Stage: {record['stage']}\n"
                    f"Estimated Deal Size: {record['estimated_deal_size']}\n"
                    f"Notes: {record['notes']}\n"
                    f"Tags: {', '.join(record.get('tags', []))}"
                )
                matches.append({
                    "title": f"CRM: {record['company']}",
                    "content": content,
                    "url": "internal://crm",
                    "score": 0.95,
                    "source_type": "crm",
                    "raw": record,
                })
                logger.info(f"CRM match found for '{company}': {record['company']} [{record['account_status']}]")

    if not matches:
        logger.info(f"No CRM record found for '{company}'")

    return matches
