#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-time script: extend codes_registry.json with new codes for
road maintenance/construction, general construction, and water transmission.
Run from project root: python tools/extend_registry.py
"""

import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.json_manager import load_json, save_json

REGISTRY_PATH = Path("codes_registry.json")

NEW_CODES = {

    # ─────────────────────────────────────────────────────────────
    # ROAD MAINTENANCE / CONSTRUCTION  (network R)
    # ─────────────────────────────────────────────────────────────
    "001-TRF-MGT": {
        "code_id": "001-TRF-MGT",
        "category": "001", "phase": "TRF", "variation": "MGT",
        "activity_name_ar": "خطة إدارة حركة المرور",
        "activity_name_en": "Traffic Management Plan",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 2,
        "dependencies": ["001-SUR-BASE"],
        "has_images": True, "image_count": 2, "page_count": 4,
        "source_document": "001-TRF-MGT.docx",
        "tags": ["traffic", "road", "management"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "001-RDS-INS": {
        "code_id": "001-RDS-INS",
        "category": "001", "phase": "RDS", "variation": "INS",
        "activity_name_ar": "فحص وتقييم حالة الطريق",
        "activity_name_en": "Road Condition Inspection & Survey",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 3,
        "dependencies": ["001-SUR-BASE"],
        "has_images": True, "image_count": 4, "page_count": 5,
        "source_document": "001-RDS-INS.docx",
        "tags": ["road", "inspection", "survey", "condition"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "002-PAV-EVL": {
        "code_id": "002-PAV-EVL",
        "category": "002", "phase": "PAV", "variation": "EVL",
        "activity_name_ar": "تقييم الرصيف والطبقات الأسفلتية",
        "activity_name_en": "Pavement Evaluation & Layer Assessment",
        "project_ids": ["road_maintenance"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 6,
        "dependencies": ["001-RDS-INS"],
        "has_images": True, "image_count": 3, "page_count": 5,
        "source_document": "002-PAV-EVL.docx",
        "tags": ["pavement", "evaluation", "assessment"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "002-MIL-ASP": {
        "code_id": "002-MIL-ASP",
        "category": "002", "phase": "MIL", "variation": "ASP",
        "activity_name_ar": "جلخ وإزالة الطبقة الأسفلتية القائمة",
        "activity_name_en": "Asphalt Milling & Scarifying",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 7,
        "dependencies": ["002-PAV-EVL", "001-TRF-MGT"],
        "excavation_type": "MIL",
        "has_images": True, "image_count": 4, "page_count": 5,
        "source_document": "002-MIL-ASP.docx",
        "tags": ["milling", "asphalt", "removal", "scarify"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "002-WST-MIL": {
        "code_id": "002-WST-MIL",
        "category": "002", "phase": "WST", "variation": "MIL",
        "activity_name_ar": "نقل والتخلص من مخلفات الجلخ",
        "activity_name_en": "Milled Material Disposal & Transport",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 8,
        "dependencies": ["002-MIL-ASP"],
        "has_images": False, "image_count": 0, "page_count": 3,
        "source_document": "002-WST-MIL.docx",
        "tags": ["waste", "milling", "disposal"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-PRM-COAT": {
        "code_id": "003-PRM-COAT",
        "category": "003", "phase": "PRM", "variation": "COAT",
        "activity_name_ar": "تطبيق طبقة التشريب (Prime Coat)",
        "activity_name_en": "Prime Coat Application",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 9,
        "dependencies": ["002-WST-MIL"],
        "has_images": True, "image_count": 2, "page_count": 3,
        "source_document": "003-PRM-COAT.docx",
        "tags": ["prime coat", "road", "bitumen"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-ASP-BASE": {
        "code_id": "003-ASP-BASE",
        "category": "003", "phase": "ASP", "variation": "BASE",
        "activity_name_ar": "فرد وضغط طبقة الأساس الأسفلتية",
        "activity_name_en": "Asphalt Base Course Laying & Compaction",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 10,
        "dependencies": ["003-PRM-COAT"],
        "has_images": True, "image_count": 4, "page_count": 6,
        "source_document": "003-ASP-BASE.docx",
        "tags": ["asphalt", "base course", "road"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-ASP-WER": {
        "code_id": "003-ASP-WER",
        "category": "003", "phase": "ASP", "variation": "WER",
        "activity_name_ar": "فرد وضغط طبقة التآكل الأسفلتية",
        "activity_name_en": "Asphalt Wearing Course Laying & Compaction",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 11,
        "dependencies": ["003-ASP-BASE"],
        "has_images": True, "image_count": 4, "page_count": 6,
        "source_document": "003-ASP-WER.docx",
        "tags": ["asphalt", "wearing course", "road", "surface"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-CRB-STN": {
        "code_id": "003-CRB-STN",
        "category": "003", "phase": "CRB", "variation": "STN",
        "activity_name_ar": "تركيب حجارة الحافة والرصيف",
        "activity_name_en": "Curb Stones & Edge Restraints Installation",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 12,
        "dependencies": ["003-ASP-BASE"],
        "has_images": True, "image_count": 2, "page_count": 3,
        "source_document": "003-CRB-STN.docx",
        "tags": ["curb", "stone", "road", "edge"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "004-TST-CMP": {
        "code_id": "004-TST-CMP",
        "category": "004", "phase": "TST", "variation": "CMP",
        "activity_name_ar": "اختبار الدك والضغط",
        "activity_name_en": "Compaction Testing (Marshall & Proctor)",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 13,
        "dependencies": ["003-ASP-WER"],
        "has_images": True, "image_count": 2, "page_count": 4,
        "source_document": "004-TST-CMP.docx",
        "tags": ["testing", "compaction", "road", "quality"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "004-TST-THK": {
        "code_id": "004-TST-THK",
        "category": "004", "phase": "TST", "variation": "THK",
        "activity_name_ar": "اختبار السماكة والكثافة",
        "activity_name_en": "Thickness & Density Testing",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 14,
        "dependencies": ["003-ASP-WER"],
        "has_images": True, "image_count": 2, "page_count": 3,
        "source_document": "004-TST-THK.docx",
        "tags": ["testing", "thickness", "density", "road"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "005-MRK-RD": {
        "code_id": "005-MRK-RD",
        "category": "005", "phase": "MRK", "variation": "RD",
        "activity_name_ar": "دهان ورسم علامات الطريق والمسارات",
        "activity_name_en": "Road Markings & Lane Painting",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 15,
        "dependencies": ["004-TST-CMP"],
        "has_images": True, "image_count": 3, "page_count": 4,
        "source_document": "005-MRK-RD.docx",
        "tags": ["marking", "road", "painting", "lanes"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "005-SGN-TRF": {
        "code_id": "005-SGN-TRF",
        "category": "005", "phase": "SGN", "variation": "TRF",
        "activity_name_ar": "توريد وتركيب اللوحات والعلامات المرورية",
        "activity_name_en": "Traffic Signs Supply & Installation",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 16,
        "dependencies": ["005-MRK-RD"],
        "has_images": True, "image_count": 3, "page_count": 3,
        "source_document": "005-SGN-TRF.docx",
        "tags": ["signs", "traffic", "road"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "005-SAF-BAR": {
        "code_id": "005-SAF-BAR",
        "category": "005", "phase": "SAF", "variation": "BAR",
        "activity_name_ar": "تركيب الحواجز والدرابزينات الأمنية",
        "activity_name_en": "Safety Barriers & Guardrails Installation",
        "project_ids": ["road_maintenance", "road_construction"],
        "network_types": ["R"],
        "applicable_owners": ["mot", "amana_riyadh", "amana_qassim", "makkah", "moh"],
        "sequence_order": 17,
        "dependencies": ["003-ASP-WER"],
        "has_images": True, "image_count": 2, "page_count": 3,
        "source_document": "005-SAF-BAR.docx",
        "tags": ["safety", "barriers", "guardrails", "road"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },

    # ─────────────────────────────────────────────────────────────
    # GENERAL CONSTRUCTION  (network C)
    # ─────────────────────────────────────────────────────────────
    "001-SOI-INV": {
        "code_id": "001-SOI-INV",
        "category": "001", "phase": "SOI", "variation": "INV",
        "activity_name_ar": "دراسة التربة والتحقيق الجيوتقني",
        "activity_name_en": "Soil Investigation & Geotechnical Study",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 2,
        "dependencies": ["001-SUR-BASE"],
        "has_images": True, "image_count": 3, "page_count": 6,
        "source_document": "001-SOI-INV.docx",
        "tags": ["soil", "geotechnical", "investigation", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "002-EXC-FND": {
        "code_id": "002-EXC-FND",
        "category": "002", "phase": "EXC", "variation": "FND",
        "activity_name_ar": "حفر الأساسات والقواعد",
        "activity_name_en": "Foundation Excavation",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 6,
        "dependencies": ["001-SOI-INV", "001-APP-DES"],
        "excavation_type": "FND",
        "has_images": True, "image_count": 3, "page_count": 5,
        "source_document": "002-EXC-FND.docx",
        "tags": ["excavation", "foundation", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "002-EXC-BLK": {
        "code_id": "002-EXC-BLK",
        "category": "002", "phase": "EXC", "variation": "BLK",
        "activity_name_ar": "الحفر العام وتسوية الموقع",
        "activity_name_en": "Bulk Excavation & Site Grading",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 7,
        "dependencies": ["001-APP-DES"],
        "excavation_type": "BLK",
        "has_images": True, "image_count": 2, "page_count": 4,
        "source_document": "002-EXC-BLK.docx",
        "tags": ["excavation", "bulk", "grading"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-FND-CON": {
        "code_id": "003-FND-CON",
        "category": "003", "phase": "FND", "variation": "CON",
        "activity_name_ar": "أعمال خرسانة الأساسات",
        "activity_name_en": "Foundation Concrete Works",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 9,
        "dependencies": ["002-EXC-FND"],
        "has_images": True, "image_count": 4, "page_count": 7,
        "source_document": "003-FND-CON.docx",
        "tags": ["foundation", "concrete", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-RBR-WRK": {
        "code_id": "003-RBR-WRK",
        "category": "003", "phase": "RBR", "variation": "WRK",
        "activity_name_ar": "أعمال حديد التسليح",
        "activity_name_en": "Rebar & Steel Reinforcement Works",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 10,
        "dependencies": ["003-FND-CON"],
        "has_images": True, "image_count": 3, "page_count": 5,
        "source_document": "003-RBR-WRK.docx",
        "tags": ["rebar", "steel", "reinforcement"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-STR-CON": {
        "code_id": "003-STR-CON",
        "category": "003", "phase": "STR", "variation": "CON",
        "activity_name_ar": "أعمال الخرسانة الإنشائية",
        "activity_name_en": "Structural Concrete Works",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 11,
        "dependencies": ["003-RBR-WRK"],
        "has_images": True, "image_count": 4, "page_count": 8,
        "source_document": "003-STR-CON.docx",
        "tags": ["structural", "concrete", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-MAS-BLK": {
        "code_id": "003-MAS-BLK",
        "category": "003", "phase": "MAS", "variation": "BLK",
        "activity_name_ar": "أعمال البناء بالطوب والبلوك",
        "activity_name_en": "Masonry & Blockwork",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 12,
        "dependencies": ["003-STR-CON"],
        "has_images": True, "image_count": 2, "page_count": 4,
        "source_document": "003-MAS-BLK.docx",
        "tags": ["masonry", "blockwork", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-STL-STR": {
        "code_id": "003-STL-STR",
        "category": "003", "phase": "STL", "variation": "STR",
        "activity_name_ar": "أعمال الهياكل الفولاذية",
        "activity_name_en": "Structural Steel Works",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 13,
        "dependencies": ["003-FND-CON"],
        "has_images": True, "image_count": 3, "page_count": 6,
        "source_document": "003-STL-STR.docx",
        "tags": ["steel", "structural", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "004-TST-CON": {
        "code_id": "004-TST-CON",
        "category": "004", "phase": "TST", "variation": "CON",
        "activity_name_ar": "اختبارات الخرسانة ومراقبة الجودة",
        "activity_name_en": "Concrete Testing & Quality Control",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 14,
        "dependencies": ["003-STR-CON"],
        "has_images": True, "image_count": 3, "page_count": 5,
        "source_document": "004-TST-CON.docx",
        "tags": ["testing", "concrete", "quality"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "004-INS-ELE": {
        "code_id": "004-INS-ELE",
        "category": "004", "phase": "INS", "variation": "ELE",
        "activity_name_ar": "تركيب الأنظمة الكهربائية والإنارة",
        "activity_name_en": "Electrical Systems & Lighting Installation",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 15,
        "dependencies": ["003-MAS-BLK"],
        "has_images": True, "image_count": 3, "page_count": 6,
        "source_document": "004-INS-ELE.docx",
        "tags": ["electrical", "installation", "lighting"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "004-INS-FIN": {
        "code_id": "004-INS-FIN",
        "category": "004", "phase": "INS", "variation": "FIN",
        "activity_name_ar": "أعمال التشطيبات والإنهاء",
        "activity_name_en": "Finishes & Architectural Works",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 16,
        "dependencies": ["003-MAS-BLK"],
        "has_images": True, "image_count": 4, "page_count": 7,
        "source_document": "004-INS-FIN.docx",
        "tags": ["finishes", "architectural", "construction"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "005-CLN-STE": {
        "code_id": "005-CLN-STE",
        "category": "005", "phase": "CLN", "variation": "STE",
        "activity_name_ar": "تنظيف الموقع وإزالة المخلفات النهائية",
        "activity_name_en": "Final Site Cleanup & Waste Removal",
        "project_ids": ["general_construction"],
        "network_types": ["C"],
        "applicable_owners": ["nhi", "amana_riyadh", "amana_qassim", "mot", "ksia", "moh"],
        "sequence_order": 18,
        "dependencies": ["004-TST-CON"],
        "has_images": False, "image_count": 0, "page_count": 2,
        "source_document": "005-CLN-STE.docx",
        "tags": ["cleanup", "site", "waste"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },

    # ─────────────────────────────────────────────────────────────
    # WATER TRANSMISSION  (network T) — large-diameter pipelines
    # ─────────────────────────────────────────────────────────────
    "003-PIP-TRN": {
        "code_id": "003-PIP-TRN",
        "category": "003", "phase": "PIP", "variation": "TRN",
        "activity_name_ar": "تركيب خط نقل المياه الرئيسي",
        "activity_name_en": "Main Water Transmission Pipeline Installation",
        "project_ids": ["water_transmission"],
        "network_types": ["T"],
        "applicable_owners": ["swa", "nwc", "amana_riyadh"],
        "sequence_order": 11,
        "dependencies": ["002-WST-EXC"],
        "has_images": True, "image_count": 5, "page_count": 8,
        "source_document": "003-PIP-TRN.docx",
        "tags": ["pipeline", "transmission", "water", "main line"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-ANC-BLK": {
        "code_id": "003-ANC-BLK",
        "category": "003", "phase": "ANC", "variation": "BLK",
        "activity_name_ar": "أعمال كتل الارتكاز والتثبيت",
        "activity_name_en": "Anchor Blocks & Thrust Blocks",
        "project_ids": ["water_transmission"],
        "network_types": ["T"],
        "applicable_owners": ["swa", "nwc", "amana_riyadh"],
        "sequence_order": 12,
        "dependencies": ["003-PIP-TRN"],
        "has_images": True, "image_count": 2, "page_count": 4,
        "source_document": "003-ANC-BLK.docx",
        "tags": ["anchor", "thrust block", "pipeline"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "003-AIR-VLV": {
        "code_id": "003-AIR-VLV",
        "category": "003", "phase": "AIR", "variation": "VLV",
        "activity_name_ar": "تركيب صمامات تنفيس الهواء",
        "activity_name_en": "Air Release Valves Installation",
        "project_ids": ["water_transmission"],
        "network_types": ["T"],
        "applicable_owners": ["swa", "nwc", "amana_riyadh"],
        "sequence_order": 13,
        "dependencies": ["003-PIP-TRN"],
        "has_images": True, "image_count": 2, "page_count": 3,
        "source_document": "003-AIR-VLV.docx",
        "tags": ["air valve", "valve", "pipeline"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
    "004-TST-PRE": {
        "code_id": "004-TST-PRE",
        "category": "004", "phase": "TST", "variation": "PRE",
        "activity_name_ar": "اختبار ضغط خط النقل",
        "activity_name_en": "Transmission Line Pressure Testing",
        "project_ids": ["water_transmission"],
        "network_types": ["T"],
        "applicable_owners": ["swa", "nwc", "amana_riyadh"],
        "sequence_order": 14,
        "dependencies": ["003-ANC-BLK", "003-AIR-VLV"],
        "has_images": True, "image_count": 2, "page_count": 4,
        "source_document": "004-TST-PRE.docx",
        "tags": ["testing", "pressure", "transmission", "pipeline"],
        "status": "active", "created_date": "2026-04-20", "last_modified": "2026-04-20", "version": "1.0"
    },
}


def main():
    reg = load_json(REGISTRY_PATH)
    codes = reg["codes"]
    before = len(codes)
    added = []
    skipped = []
    for code_id, data in NEW_CODES.items():
        if code_id in codes:
            skipped.append(code_id)
        else:
            codes[code_id] = data
            added.append(code_id)

    # Update statistics
    active_count = sum(1 for c in codes.values() if c.get("status") == "active")
    reg["statistics"] = reg.get("statistics", {})
    reg["statistics"]["total_active_codes"] = active_count
    reg["statistics"]["last_expanded"] = "2026-04-20"
    reg["metadata"]["total_codes"] = len(codes)
    reg["metadata"]["last_updated"] = "2026-04-20T18:00:00Z"

    save_json(reg, REGISTRY_PATH)
    print(f"Registry expanded: {before} -> {len(codes)} codes")
    print(f"  Added   ({len(added)}): {', '.join(added)}")
    if skipped:
        print(f"  Skipped ({len(skipped)}): {', '.join(skipped)}")


if __name__ == "__main__":
    main()
