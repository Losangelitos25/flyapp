"""
destinations.py — Mapa de regiones, países y destinos turísticos.
Usado por google_flights.py para expandir búsquedas de destino abierto.
"""

# ── Aeropuertos por continente ────────────────────────────────────────────────
CONTINENTS = {
    "Europa": [
        "MAD", "BCN", "LIS", "FCO", "MXP", "CDG", "ORY", "AMS", "FRA", "MUC",
        "VIE", "ZRH", "BRU", "CPH", "ARN", "OSL", "HEL", "ATH", "IST", "LHR",
        "MAN", "DUB", "PRG", "BUD", "WAW", "OTP", "SOF", "LJU", "ZAG", "BEG",
        "SKP", "TIA", "SVO", "LED", "KBP", "TXL", "HAM", "DUS", "STN", "LGW",
    ],
    "América del Norte": [
        "JFK", "LAX", "MIA", "ORD", "SFO", "BOS", "ATL", "DFW", "YYZ", "YVR",
        "MEX", "CUN", "GDL", "PTY", "SJO", "SJU",
    ],
    "América del Sur": [
        "GRU", "GIG", "SCL", "BOG", "LIM", "UIO", "MVD", "ASU", "CCS", "VVI",
        "MDE", "CTG", "BSB", "SSA", "POA", "FOR",
    ],
    "Asia": [
        "DXB", "DOH", "BKK", "SIN", "KUL", "HKG", "NRT", "KIX", "ICN", "PEK",
        "PVG", "DEL", "BOM", "CMB", "MLE", "CGK", "MNL", "SGN", "HAN", "TPE",
    ],
    "África": [
        "CAI", "CMN", "JNB", "CPT", "LOS", "ACC", "NBO", "DAR", "ADD", "TUN",
        "ALG", "RAK", "DKR", "MRU",
    ],
    "Oceanía": [
        "SYD", "MEL", "BNE", "PER", "AKL", "CHC", "NAN", "PPT",
    ],
    "Caribe": [
        "HAV", "SDQ", "PUJ", "SXM", "SJU", "NAS", "BGI", "POS", "KIN", "MBJ",
    ],
    "Medio Oriente": [
        "DXB", "DOH", "AUH", "RUH", "AMM", "BEY", "TLV", "MCT", "KWI", "BAH",
    ],
}

# ── Aeropuertos por país ──────────────────────────────────────────────────────
COUNTRIES = {
    "España":         ["MAD", "BCN", "AGP", "ALC", "VLC", "BIO", "SVQ", "PMI"],
    "Francia":        ["CDG", "ORY", "NCE", "LYS", "MRS", "BOD", "TLS", "NTE"],
    "Italia":         ["FCO", "MXP", "VCE", "NAP", "PSA", "BLQ", "CAG", "PMO"],
    "Portugal":       ["LIS", "OPO", "FAO"],
    "Alemania":       ["FRA", "MUC", "TXL", "HAM", "DUS", "STR", "CGN"],
    "Países Bajos":   ["AMS"],
    "Reino Unido":    ["LHR", "LGW", "STN", "MAN", "EDI", "GLA", "BHX"],
    "Grecia":         ["ATH", "SKG", "HER", "RHO", "CFU", "JMK", "JTR"],
    "Turquía":        ["IST", "SAW", "AYT", "ADB", "ESB"],
    "Suiza":          ["ZRH", "GVA", "BSL"],
    "Austria":        ["VIE", "SZG", "INN"],
    "Bélgica":        ["BRU", "CRL"],
    "Dinamarca":      ["CPH"],
    "Suecia":         ["ARN", "GOT"],
    "Noruega":        ["OSL", "BGO", "TRD"],
    "Finlandia":      ["HEL"],
    "Irlanda":        ["DUB", "ORK"],
    "República Checa":["PRG"],
    "Hungría":        ["BUD"],
    "Polonia":        ["WAW", "KRK", "GDN", "KTW"],
    "Rumanía":        ["OTP", "CLJ"],
    "Croacia":        ["ZAG", "SPU", "DBV"],
    "Brasil":         ["GRU", "GIG", "BSB", "SSA", "POA", "FOR", "REC", "NAT"],
    "Chile":          ["SCL", "PMC", "IQQ"],
    "Colombia":       ["BOG", "MDE", "CTG", "CLO", "BAQ"],
    "Perú":           ["LIM", "CUZ"],
    "Uruguay":        ["MVD"],
    "Paraguay":       ["ASU"],
    "Bolivia":        ["VVI", "LPB"],
    "Venezuela":      ["CCS", "MAR"],
    "Ecuador":        ["UIO", "GYE"],
    "México":         ["MEX", "CUN", "GDL", "MTY", "TIJ", "OAX", "SJD"],
    "Cuba":           ["HAV", "VRA", "SCU"],
    "Emiratos Árabes":["DXB", "AUH", "SHJ"],
    "Qatar":          ["DOH"],
    "Tailandia":      ["BKK", "HKT", "CNX", "USM"],
    "Japón":          ["NRT", "KIX", "NGO", "CTS", "FUK"],
    "Indonesia":      ["CGK", "DPS", "SUB"],
    "India":          ["DEL", "BOM", "BLR", "MAA", "CCU", "HYD"],
    "Singapur":       ["SIN"],
    "Malasia":        ["KUL", "PEN", "LGK"],
    "Australia":      ["SYD", "MEL", "BNE", "PER", "ADL"],
    "Nueva Zelanda":  ["AKL", "CHC", "WLG"],
    "Marruecos":      ["CMN", "RAK", "AGA", "TNG"],
    "Sudáfrica":      ["JNB", "CPT", "DUR"],
    "Egipto":         ["CAI", "HRG", "SSH"],
    "Kenia":          ["NBO", "MBA"],
    "Tanzania":       ["DAR", "JRO"],
    "Etiopía":        ["ADD"],
    "Maldivas":       ["MLE"],
    "Sri Lanka":      ["CMB"],
    "Estados Unidos": ["JFK", "LAX", "MIA", "ORD", "SFO", "BOS", "ATL", "DFW", "LAS", "MCO", "SEA", "DEN"],
    "Canadá":         ["YYZ", "YVR", "YUL", "YYC", "YEG", "YOW"],
}

# ── Regiones turísticas ───────────────────────────────────────────────────────
REGIONS = {
    "Mediterráneo":       ["BCN", "MAD", "PMI", "AGP", "FCO", "MXP", "VCE", "NAP", "ATH", "HER", "RHO", "LIS", "CMN", "TUN", "ALG"],
    "Europa del Este":    ["PRG", "BUD", "WAW", "KRK", "OTP", "SOF", "ZAG", "BEG", "SKP", "TIA", "LJU"],
    "Escandinavia":       ["ARN", "CPH", "OSL", "HEL", "GOT", "TRD", "BGO"],
    "Europa Central":     ["FRA", "MUC", "VIE", "ZRH", "BRU", "AMS", "TXL", "HAM"],
    "Caribe":             ["HAV", "SDQ", "PUJ", "SXM", "SJU", "NAS", "BGI", "KIN", "MBJ", "VRA", "CUN"],
    "Sudeste Asiático":   ["BKK", "HKT", "SIN", "KUL", "CGK", "DPS", "MNL", "SGN", "HAN", "RGN"],
    "Playas del Pacífico":["DPS", "HKT", "USM", "LGK", "PPT", "NAN", "ROR"],
    "Oriente Medio":      ["DXB", "DOH", "AUH", "BEY", "AMM", "TLV", "MCT"],
    "África del Sur":     ["JNB", "CPT", "DUR", "HRE", "LUN"],
    "África del Norte":   ["CAI", "CMN", "RAK", "TUN", "ALG", "HRG", "SSH"],
    "Safari / África Oriental": ["NBO", "DAR", "JRO", "ADD", "MBA"],
    "Sudamérica Andina":  ["LIM", "CUZ", "UIO", "VVI", "LPB", "SCL"],
    "Brasil":             ["GRU", "GIG", "SSA", "FOR", "NAT", "REC", "POA"],
    "Islas del Índico":   ["MLE", "CMB", "MRU", "SEZ"],
    "Japón / Corea":      ["NRT", "KIX", "ICN", "GMP", "CTS", "FUK"],
    "China":              ["PEK", "PVG", "CAN", "SZX", "CTU"],
    "Australia / NZ":     ["SYD", "MEL", "BNE", "PER", "AKL", "CHC"],
    "Norteamérica":       ["JFK", "LAX", "MIA", "ORD", "SFO", "YYZ", "YVR", "MEX", "CUN"],
    "América Central":    ["PTY", "SJO", "GUA", "SAL", "MGA", "TGU", "BZE"],
}

# ── Provincias / Destinos Argentina ──────────────────────────────────────────
ARGENTINA_PROVINCES = {
    "Buenos Aires":        ["EZE", "AEP"],
    "Córdoba":             ["COR"],
    "Mendoza":             ["MDZ"],
    "Bariloche / Patagonia":["BRC", "PMQ", "REL"],
    "Salta / NOA":         ["SLA", "JUJ"],
    "Misiones / Cataratas":["IGR"],
    "Mar del Plata":       ["MDQ"],
    "Ushuaia / Tierra del Fuego": ["USH"],
    "Neuquén":             ["NQN"],
    "Santa Fe":            ["SFN"],
    "Tucumán":             ["TUC"],
    "Chubut / Puerto Madryn": ["PMY"],
    "El Calafate":         ["FTE"],
    "La Rioja":            ["IRJ"],
    "Catamarca":           ["CTC"],
}

# ── Índice plano: nombre → lista de IATAs ─────────────────────────────────────
def get_airports_for_scope(scope_type: str, scope_value: str) -> list[str]:
    """
    Dado tipo y valor de scope, devuelve lista de códigos IATA.
    scope_type: "continent" | "country" | "region" | "province" | "airport"
    """
    if scope_type == "airport":
        return [scope_value.upper()]
    if scope_type == "continent":
        return CONTINENTS.get(scope_value, [])
    if scope_type == "country":
        return COUNTRIES.get(scope_value, [])
    if scope_type == "region":
        return REGIONS.get(scope_value, [])
    if scope_type == "province":
        return ARGENTINA_PROVINCES.get(scope_value, [])
    return []

# ── Opciones para el dashboard ────────────────────────────────────────────────
SCOPE_OPTIONS = {
    "Continente": list(CONTINENTS.keys()),
    "País":       sorted(COUNTRIES.keys()),
    "Región turística": list(REGIONS.keys()),
    "Provincia Argentina": list(ARGENTINA_PROVINCES.keys()),
}
