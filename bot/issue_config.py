# bot/issue_config.py
# Configuration for 20 types of civic issues, defining photo and additional data requirements.
# This ensures that the Gemini classification output maps directly to a defined requirement.

ISSUE_CONFIG = {
    # 1. Roads & Traffic
    "Roads & Traffic": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 2. Water Supply
    "Water Supply": {
        "photo_required": False, # Changed from Conditional to False for simplicity in the current bot flow
        "additional_prompt": None,
    },
    # 3. Electricity / Power
    "Electricity / Power": {
        "photo_required": False,
        "additional_prompt": "Please specify the date and time when the issue (e.g., power cut) started.",
    },
    # 4. Sewage & Drainage
    "Sewage & Drainage": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 5. Street Safety
    "Street Safety": {
        "photo_required": True,
        "additional_prompt": "Please provide the name of a nearby landmark or specific crossing for reference.",
    },
    # 6. Crime / Anti-Social Activity
    "Crime / Anti-Social Activity": {
        "photo_required": False,
        "additional_prompt": "Provide a brief description of the suspect or the nature of the activity.",
    },
    # 7. Fire Hazards
    "Fire Hazards": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 8. Garbage & Waste Management
    "Garbage & Waste Management": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 9. Pollution & Noise
    "Pollution & Noise": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 10. Green Spaces
    "Green Spaces": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 11. Public Transport
    "Public Transport": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 12. Community Facilities
    "Community Facilities": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 13. Healthcare & Hospitals
    "Healthcare & Hospitals": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 14. Documentation / Permits
    "Documentation / Permits": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 15. Billing / Taxes / Fines
    "Billing / Taxes / Fines": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 16. Corruption / Malpractice
    "Corruption / Malpractice": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 17. App / Portal Issues
    "App / Portal Issues": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 18. Noise Complaints
    "Noise Complaints": {
        "photo_required": False,
        "additional_prompt": None,
    },
    # 19. Animal-Related Issues
    "Animal-Related Issues": {
        "photo_required": True,
        "additional_prompt": None,
    },
    # 20. Other Civic Complaints (Fallback)
    "Other Civic Complaints": {
        "photo_required": False,
        "additional_prompt": None,
    },
}
