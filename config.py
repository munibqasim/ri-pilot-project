"""
Configuration file for RI Pilot Project
Contains keyword taxonomy and all configuration constants
"""

# Comprehensive RI Keyword Taxonomy
RI_KEYWORDS = {
    
    # CORE RI TERMS (Cross-cutting)
    "core_resilience": [
        "resilient", "resilience",
        "climate-proof", "climate-proofing", "climateproof",
        "disaster-resistant", "disaster risk",
        "adaptive", "adaptation", "adaptability",
        "robust", "robustness",
        "redundancy", "redundant",
        "flexible", "flexibility",
        "withstand",
        "climate change",
        "extreme event", "extreme weather",
        "hazard mitigation",
        "risk-informed",
        "future-proof"
    ],
    
    # HAZARD KEYWORDS
    "hazards": [
        "flood", "flooding", "floodplain", "inundation",
        "seismic", "earthquake", "tremor",
        "cyclone", "hurricane", "typhoon", "storm surge",
        "drought", "water scarcity",
        "heat", "heatwave", "temperature extreme",
        "landslide", "erosion", "slope failure",
        "wind", "windstorm", "gale",
        "fire", "wildfire",
        "tsunami",
        "coastal erosion", "sea level rise",
        "precipitation", "rainfall", "heavy rain",
        "lightning",
        "avalanche"
    ],
    
    # RESILIENCE ACTIVITIES (8 Pillars)
    "activities": [
        "asset management",
        "preventive maintenance", "predictive maintenance",
        "condition monitoring", "structural health monitoring",
        "contingency plan", "emergency response", "business continuity",
        "early warning system",
        "disaster preparedness",
        "system planning", "systems approach",
        "risk assessment", "vulnerability assessment", "hazard assessment",
        "climate screening", "climate risk",
        "institutional capacity",
        "stakeholder engagement",
        "backup system",
        "design standards", "engineering standards"
    ],
    
    # ENERGY SECTOR
    "energy": [
        # Infrastructure
        "substation", "transmission line", "distribution line", "power grid",
        "hydropower", "dam", "reservoir", "spillway",
        "generator", "turbine", "transformer",
        
        # Resilience Features
        "elevated substation", "raised substation",
        "flood-proof", "floodproofing",
        "mobile substation", "portable substation",
        "backup power", "emergency power", "auxiliary power",
        "battery storage", "energy storage", "BESS",
        "microgrid", "mini-grid", "off-grid",
        "N-1 redundancy",
        "grid stability", "system reliability",
        "corrosion-resistant",
        "wind-resistant tower", "reinforced tower",
        "seismic design",
        "insulated cable", "weatherproof cable",
        "underground cabling",
        "dam safety", "dam monitoring",
        "hydrology study", "hydrological analysis"
    ],
    
    # TRANSPORT SECTOR - ROADS
    "transport_roads": [
        "elevated roadbed", "raised embankment",
        "climate-resilient pavement", "heat-resistant pavement",
        "drainage system", "culvert", "stormwater",
        "flood-resistant",
        "erosion control", "slope stabilization", "bioengineering",
        "all-weather road", "all-season connectivity",
        "reinforced pavement",
        "retaining wall",
        "bridge elevation", "bridge clearance",
        "road asset management",
        "pavement condition",
        "road maintenance"
    ],
    
    # TRANSPORT SECTOR - RAILWAYS
    "transport_rail": [
        "ballast", "track bed",
        "drainage", "track drainage",
        "elevated track", "viaduct",
        "slope protection",
        "signaling system", "communication system",
        "tunnel ventilation",
        "rail monitoring"
    ],
    
    # TRANSPORT SECTOR - PORTS
    "transport_ports": [
        "breakwater", "seawall", "revetment",
        "dredging", "sediment management",
        "quay wall", "wharf",
        "storm surge protection",
        "port infrastructure",
        "berth", "pier"
    ],
    
    # WATER SECTOR
    "water": [
        # Water Supply
        "water treatment plant", "treatment facility",
        "reservoir", "water storage",
        "distribution network", "water pipeline",
        "pump station", "pumping system",
        "backup water supply",
        "water quality monitoring",
        
        # Wastewater
        "wastewater treatment", "sewage treatment",
        "collection system", "sewer network",
        "lift station",
        "outfall",
        
        # Flood Protection
        "levee", "embankment", "bund",
        "retention basin", "detention pond",
        "flood barrier", "flood gate",
        "channel", "canal",
        "pumping station"
    ],
    
    # ICT SECTOR
    "ict": [
        "data center", "server room",
        "telecommunications", "telecom infrastructure",
        "fiber optic", "cable network",
        "cell tower", "base station",
        "backup generator", "UPS", "uninterruptible power",
        "redundant system",
        "disaster recovery", "data backup",
        "cooling system"
    ],
    
    # BUILDINGS
    "buildings": [
        "seismic retrofit", "structural reinforcement",
        "wind-resistant design",
        "flood-resistant construction",
        "building code", "construction standard",
        "foundation", "structural design",
        "fire protection", "fire safety",
        "HVAC system",
        "emergency exit", "evacuation route"
    ],
    
    # URBAN INFRASTRUCTURE
    "urban": [
        "green infrastructure",
        "permeable pavement", "porous pavement",
        "rain garden", "bioswale",
        "urban drainage",
        "heat island mitigation",
        "urban forest", "tree canopy",
        "cooling center", "emergency shelter"
    ],
    
    # AGRICULTURE/IRRIGATION
    "agriculture": [
        "irrigation system", "irrigation infrastructure",
        "water harvesting", "rainwater collection",
        "drought-resistant crop",
        "soil conservation",
        "terracing",
        "drainage system"
    ]
}

# Semantic Search Queries
SEMANTIC_QUERIES = [
    {
        "query": "infrastructure designed to withstand floods through elevation, waterproofing, or drainage systems",
        "sector": "flood_resilience"
    },
    {
        "query": "earthquake-resistant design including seismic retrofitting, base isolation, or reinforced structures",
        "sector": "seismic_resilience"
    },
    {
        "query": "power systems with backup generation, battery storage, or microgrids for reliability",
        "sector": "energy_resilience"
    },
    {
        "query": "transportation infrastructure designed for extreme weather including elevated roads and reinforced bridges",
        "sector": "transport_resilience"
    },
    {
        "query": "water systems with redundant supply, backup pumping, or flood protection measures",
        "sector": "water_resilience"
    },
    {
        "query": "climate adaptation measures including early warning systems and disaster preparedness",
        "sector": "climate_adaptation"
    },
    {
        "query": "infrastructure asset management including monitoring, maintenance, and condition assessment",
        "sector": "asset_management"
    },
    {
        "query": "nature-based solutions including green infrastructure, bioengineering, and ecosystem approaches",
        "sector": "nature_based"
    }
]

# AWS Configuration
AWS_CONFIG = {
    "region": "us-east-1",
    "s3_bucket": "cpf-2025",
    "s3_input_prefix": "Natalias-Batch-Work/bedrock-batch-input",
    "s3_output_prefix": "Natalias-Batch-Work/bedrock-batch-output",
    "bedrock_model_id": "anthropic.claude-sonnet-4-20250514",
    "batch_size": 5
}

# File Paths
FILE_PATHS = {
    "keyword_results": "keyword_search_results.json",
    "semantic_results": "semantic_search_results.json",
    "combined_results": "combined_deduplicated_results.json",
    "bedrock_input": "bedrock_batch_input.jsonl",
    "bedrock_classifications": "bedrock_classifications.json",
    "final_results": "final_enriched_results.json",
    "final_results_positive": "final_enriched_results_positive_only.json",
    "activity_classifications": "final_ri_classifications.json"
}

# Search Parameters
SEARCH_PARAMS = {
    "keyword_context_sentences": 3,
    "semantic_chunk_size": 500,
    "semantic_overlap": 100,
    "semantic_similarity_threshold": 0.3,
    "dedup_overlap_threshold": 0.5
}
