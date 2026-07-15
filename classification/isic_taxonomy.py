"""
classification/isic_taxonomy.py
--------------------------------
Complete official ISIC Rev. 5 structure at Section (1-letter) and Division
(2-digit) level, per the professor's requirement: "Go down two levels, i.e.
divisions (not just sections)".

Source: UN Statistics Division, 'Draft ISIC Revision 5 structure', Task Team
on ISIC, 2 February 2023 (endorsed by UNSC, 54th session, March 2023)
https://unstats.un.org/UNSDWebsite/statcom/session_54/documents/BG-3j-ISIC-Rev5-E.pdf
All 22 sections and all 87 divisions are represented with their official codes
and names.

Each division carries a KEYWORD HINTS list used by the rule-based classifier
in classifier.py to match project/file text against the most likely division.
Hints are curated for qualitative-research topics likely to appear in QDR /
ICPSR datasets (health, education, social science, policy, etc.); divisions
unlikely to ever appear in this corpus (e.g. detailed manufacturing, mining)
keep their official name but an empty hint list.
"""

# Structure: SECTION_CODE -> (section_name, {division_code: (division_name, [keyword hints])})

ISIC_REV5 = {
    "A": ('Agriculture, forestry and fishing', {
        "01": ('Crop and animal production, hunting and related service activities', ['farming', 'agriculture', 'crop', 'livestock', 'farmers', 'rural livelihoods']),
        "02": ('Forestry and logging', ['forestry', 'logging']),
        "03": ('Fishing and aquaculture', ['fishing', 'aquaculture', 'fisheries', 'fishing communities']),
    }),
    "B": ('Mining and quarrying', {
        "05": ('Mining of coal and lignite', []),
        "06": ('Extraction of crude petroleum and natural gas', ['oil extraction', 'petroleum', 'natural gas drilling']),
        "07": ('Mining of metal ores', []),
        "08": ('Other mining and quarrying', []),
        "09": ('Mining support service activities', []),
    }),
    "C": ('Manufacturing', {
        "10": ('Manufacture of food products', ['food manufacturing', 'food production']),
        "11": ('Manufacture of beverages', []),
        "12": ('Manufacture of tobacco products', []),
        "13": ('Manufacture of textiles', []),
        "14": ('Manufacture of wearing apparel', []),
        "15": ('Manufacture of leather and related products', []),
        "16": ('Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials', []),
        "17": ('Manufacture of paper and paper products', []),
        "18": ('Printing and reproduction of recorded media', []),
        "19": ('Manufacture of coke and refined petroleum products', []),
        "20": ('Manufacture of chemicals and chemical products', []),
        "21": ('Manufacture of basic pharmaceutical products and pharmaceutical preparations', ['pharmaceutical manufacturing', 'drug manufacturing']),
        "22": ('Manufacture of rubber and plastic products', []),
        "23": ('Manufacture of other non-metallic mineral products', []),
        "24": ('Manufacture of basic metals', []),
        "25": ('Manufacture of fabricated metal products, except machinery and equipment', []),
        "26": ('Manufacture of computer, electronic and optical products', ['hardware manufacturing', 'semiconductor']),
        "27": ('Manufacture of electrical equipment', []),
        "28": ('Manufacture of machinery and equipment n.e.c.', []),
        "29": ('Manufacture of motor vehicles, trailers and semi-trailers', []),
        "30": ('Manufacture of other transport equipment', []),
        "31": ('Manufacture of furniture', []),
        "32": ('Other manufacturing', []),
        "33": ('Repair, maintenance and installation of machinery and equipment', []),
    }),
    "D": ('Electricity, gas, steam and air conditioning supply', {
        "35": ('Electricity, gas, steam and air conditioning supply', ['energy supply', 'electricity grid', 'power plant', 'energy policy']),
    }),
    "E": ('Water supply; sewerage, waste management and remediation activities', {
        "36": ('Water collection, treatment and supply', ['water supply', 'drinking water', 'water access']),
        "37": ('Sewerage', []),
        "38": ('Waste collection, treatment and disposal, and recovery activities', ['waste management', 'recycling']),
        "39": ('Remediation and other waste management service activities', ['environmental remediation']),
    }),
    "F": ('Construction', {
        "41": ('Construction of residential and non-residential buildings', ['construction', 'housing development']),
        "42": ('Civil engineering', ['civil engineering', 'infrastructure construction']),
        "43": ('Specialized construction activities', []),
    }),
    "G": ('Wholesale and retail trade', {
        "46": ('Wholesale trade', ['wholesale']),
        "47": ('Retail trade', ['retail', 'consumer shopping']),
    }),
    "H": ('Transportation and storage', {
        "49": ('Land transport and transport via pipelines', ['transportation', 'road transport', 'rail transport', 'commuting']),
        "50": ('Water transport', []),
        "51": ('Air transport', ['aviation', 'air travel']),
        "52": ('Warehousing and support activities for transportation', ['logistics', 'warehousing', 'supply chain']),
        "53": ('Postal and courier activities', []),
    }),
    "I": ('Accommodation and food service activities', {
        "55": ('Accommodation', ['hospitality', 'hotels', 'tourism accommodation']),
        "56": ('Food and beverage service activities', ['restaurants', 'food service']),
    }),
    "J": ('Publishing, broadcasting, and content production and distribution activities', {
        "58": ('Publishing activities', ['publishing', 'journalism', 'media publishing']),
        "59": ('Motion picture, video and television programme production, sound recording and music publishing activities', ['film production', 'television', 'documentary', 'video production']),
        "60": ('Programming, broadcasting, news agency and other content distribution activities', ['broadcasting', 'news media', 'social media platform']),
    }),
    "K": ('Telecommunications, computer programming, consultancy, computing infrastructure, and other information service activities', {
        "61": ('Telecommunications', ['telecommunications', 'mobile networks']),
        "62": ('Computer programming, consultancy and related activities', ['software development', 'computer programming', 'IT consultancy', 'user experience', 'human-computer interaction']),
        "63": ('Computing infrastructure, data processing, hosting, and other information service activities', ['cloud computing', 'data hosting', 'data processing', 'search engines', 'data archiving', 'data repository', 'open data']),
    }),
    "L": ('Financial and insurance activities', {
        "64": ('Financial service activities, except insurance and pension funding', ['banking', 'financial services', 'microfinance']),
        "65": ('Insurance, reinsurance and pension funding, except compulsory social security', ['insurance', 'pension funds']),
        "66": ('Activities auxiliary to financial service and insurance activities', ['financial markets', 'investment advisory']),
    }),
    "M": ('Real estate activities', {
        "68": ('Real estate activities', ['real estate', 'property market', 'housing market']),
    }),
    "N": ('Professional, scientific and technical activities', {
        "69": ('Legal and accounting activities', ['legal services', 'law practice', 'accounting', 'legal aid', 'access to justice']),
        "70": ('Activities of head offices; management consultancy activities', ['management consulting', 'corporate strategy', 'business administration', 'organizational behavior', 'workplace culture']),
        "71": ('Architectural and engineering activities; technical testing and analysis', ['architecture', 'engineering practice', 'technical testing']),
        "72": ('Scientific research and development', ['research and development', 'scientific research', 'social science research', 'qualitative research methods', 'research methodology', 'interview study', 'ethnography', 'grounded theory', 'case study research', 'academic research', 'focus group', 'participant observation', 'narrative inquiry', 'phenomenology']),
        "73": ('Activities of advertising, market research and public relations', ['advertising', 'market research', 'public opinion polling', 'consumer research', 'public relations']),
        "74": ('Other professional, scientific and technical activities', ['design activities', 'photography', 'translation', 'interpretation']),
        "75": ('Veterinary activities', ['veterinary', 'animal health']),
    }),
    "O": ('Administrative and support service activities', {
        "77": ('Rental and leasing activities', ['equipment rental', 'leasing']),
        "78": ('Employment activities', ['employment agency', 'job placement', 'recruitment', 'labor market', 'workforce', 'unemployment', 'career transitions']),
        "79": ('Travel agency, tour operator, and other travel related activities', ['travel agency', 'tourism operations']),
        "80": ('Investigation and security activities', ['security services', 'private investigation', 'surveillance', 'policing']),
        "81": ('Services to buildings and landscape activities', ['building services', 'cleaning services', 'landscaping']),
        "82": ('Office administrative, office support and other business support activities', ['office administration', 'call center', 'business support services']),
    }),
    "P": ('Public administration and defence; compulsory social security', {
        "84": ('Public administration and defence; compulsory social security', ['public administration', 'government policy', 'public policy', 'social security policy', 'defence policy', 'foreign affairs', 'civic engagement', 'political attitudes', 'political behavior', 'voting', 'public sector', 'governance', 'policy feedback', 'immigration policy', 'refugee', 'asylum seekers', 'human rights']),
    }),
    "Q": ('Education', {
        "85": ('Education', ['education', 'teaching', 'learning', 'classroom', 'pedagogy', 'curriculum', 'students', 'school', 'university', 'higher education', 'teacher training', 'academic instructors', 'instructional methods', 'educational research', 'literacy', 'early childhood education']),
    }),
    "R": ('Human health and social work activities', {
        "86": ('Human health activities', ['health', 'patient', 'clinical', 'medical', 'hospital', 'nursing', 'disease', 'cancer', 'illness', 'healthcare', 'physician', 'treatment', 'diagnosis', 'mental health', 'public health', 'epidemiology', 'wellbeing', 'chronic illness']),
        "87": ('Residential care activities', ['residential care', 'nursing home', 'assisted living', 'long-term care']),
        "88": ('Social work activities without accommodation', ['social work', 'social services', 'community support', 'welfare services', 'disability support', 'elder care']),
    }),
    "S": ('Arts, sports and recreation', {
        "90": ('Arts creation and performing arts activities', ['arts', 'visual arts', 'performing arts', 'theatre', 'music composition', 'creative practice']),
        "91": ('Library, archives, museum and other cultural activities', ['library', 'archives', 'museum', 'cultural heritage', 'data archiving', 'data curation', 'data reuse', 'digital preservation']),
        "92": ('Gambling and betting activities', ['gambling', 'betting']),
        "93": ('Sports activities and amusement and recreation activities', ['sports', 'recreation', 'physical activity', 'exercise', 'amusement']),
    }),
    "T": ('Other service activities', {
        "94": ('Activities of membership organizations', ['nonprofit organization', 'religious organization', 'political organization', 'advocacy group', 'trade union', 'civil society', 'NGO']),
        "95": ('Repair and maintenance of computers, personal and household goods, and motor vehicles and motorcycles', []),
        "96": ('Personal service activities', ['personal services', 'beauty care', 'personal care']),
    }),
    "U": ('Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use', {
        "97": ('Activities of households as employers of domestic personnel', ['domestic work', 'household employment']),
        "98": ('Undifferentiated goods- and services-producing activities of private households for own use', ['household activities', 'family life', 'domestic labor', 'unpaid care work']),
    }),
    "V": ('Activities of extraterritorial organizations and bodies', {
        "99": ('Activities of extraterritorial organizations and bodies', ['international organization', 'united nations', 'diplomatic mission']),
    }),
}


def all_divisions():
    """Yield (section_code, section_name, division_code, division_name, keywords) tuples."""
    for sec_code, (sec_name, divs) in ISIC_REV5.items():
        for div_code, (div_name, keywords) in divs.items():
            yield sec_code, sec_name, div_code, div_name, keywords


def get_section_for_division(division_code: str) -> str:
    for sec_code, (_, divs) in ISIC_REV5.items():
        if division_code in divs:
            return sec_code
    return "UNKNOWN"


def get_division_name(division_code: str) -> str:
    for _, (_, divs) in ISIC_REV5.items():
        if division_code in divs:
            return divs[division_code][0]
    return "Unclassified"


def get_section_name(section_code: str) -> str:
    if section_code in ISIC_REV5:
        return ISIC_REV5[section_code][0]
    return "Unclassified"
