#!/usr/bin/env python3
"""
Tracker de révision ECNi — Flask + pywebview
"""

from flask import Flask, request, jsonify
import json, os, time
from datetime import datetime, timedelta
from threading import Thread

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, 'revision_data.json')
CONCOURS = '2026-10-12'
CONCOURS_DAYS = ['2026-10-12', '2026-10-13', '2026-10-14', '2026-10-15']

# ---------------------------------------------------------------------------
# Items — liste figée des 367 items ECNi
# ---------------------------------------------------------------------------
ITEMS = {
    '1': 'Relation médecin-malade — colloque singulier et communication',
    '2': 'Valeurs professionnelles du médecin et des soignants',
    '3': 'Raisonnement médical — EBM et décision médicale partagée',
    '4': 'Qualité et sécurité des soins — EIAS et démarche qualité',
    '5': 'Responsabilités médicales et aléa thérapeutique',
    '6': 'Organisation de l exercice clinique et sécurisation du parcours',
    '7': 'Les droits individuels et collectifs du patient',
    '8': 'Les discriminations',
    '9': 'Introduction à l éthique médicale',
    '10': 'Approches transversales du corps',
    '11': 'Violences et santé',
    '12': 'Violences sexuelles',
    '13': 'Certificats médicaux Décès et législation',
    '14': 'La mort',
    '15': 'Soins psychiatriques sans consentement',
    '16': 'Organisation du système de soins — régulation et parcours',
    '17': 'Télémédecine télésanté et téléservices en santé',
    '18': 'Santé et numérique',
    '19': 'Sécurité sociale — assurance maladie et protection sociale',
    '20': 'La méthodologie de la recherche en santé',
    '21': 'Mesure de l état de santé de la population',
    '22': 'Maladies rares',
    '23': 'Grossesse normale',
    '24': 'Principales complications de la grossesse',
    '25': 'Grossesse extra-utérine',
    '26': 'Douleur abdominale aiguë chez une femme enceinte',
    '27': 'Prévention des risques fœtaux',
    '28': 'Infection urinaire et grossesse',
    '29': 'Risques professionnels liés à la maternité',
    '30': 'Prématurité et retard de croissance intra-utérin',
    '31': 'Accouchement délivrance et suites de couches normales',
    '32': 'Évaluation et soins du nouveau-né à terme',
    '33': 'Allaitement maternel',
    '34': 'Suites de couches pathologiques',
    '35': 'Anomalies du cycle menstruel Métrorragies',
    '36': 'Contraception voir item 330',
    '37': 'Interruption volontaire de grossesse',
    '38': 'Infertilité du couple conduite de la première consultation',
    '39': 'Assistance médicale à la procréation',
    '40': 'Algies pelviennes chez la femme',
    '41': 'Endométriose',
    '42': 'Aménorrhée',
    '43': 'Hémorragie génitale chez la femme',
    '44': 'Tuméfaction pelvienne chez la femme',
    '45': 'Spécificités des maladies génétiques voir item 9',
    '46': 'Médecine génomique',
    '47': 'Suivi nourrisson enfant adolescent — dépistages',
    '48': 'Alimentation et nutrition du nourrisson et de l enfant',
    '49': 'Puberté normale et pathologique',
    '50': 'Pathologie génito-scrotale chez le garçon et chez l homme',
    '51': 'Troubles de la miction chez l enfant',
    '52': 'Strabisme et amblyopie de l enfant',
    '53': 'Retard de croissance staturo-pondérale',
    '54': 'Boiterie chez l enfant',
    '55': 'Développement psychomoteur du nourrisson et de l enfant',
    '56': 'L enfant handicapé — orientation et prise en charge',
    '57': 'Maltraitance et enfants en danger — PMI',
    '58': 'Sexualité normale et ses troubles',
    '59': 'Sujets en situation de précarité',
    '60': 'Facteurs de risque et dépistage des troubles psychiques',
    '61': 'Classifications des troubles mentaux',
    '62': 'Organisation des soins en psychiatrie',
    '63': 'Troubles schizophréniques de l adolescent et de l adulte',
    '64': 'Troubles bipolaires de l adolescent et de l adulte',
    '65': 'Trouble délirant persistant',
    '66': 'Troubles dépressif anxieux TOC PTSD — diagnostic',
    '67': 'Troubles du neurodéveloppement',
    '68': 'Troubles du comportement de l enfant et de l adolescent',
    '69': 'Troubles psychiques de la grossesse et du post-partum',
    '70': 'Troubles psychiques du sujet âgé',
    '71': 'Troubles des conduites alimentaires',
    '72': 'Troubles à symptomatologie somatique',
    '73': 'Différents types de techniques psychothérapeutiques',
    '74': 'Prescription et surveillance des psychotropes',
    '75': 'Addiction au tabac',
    '76': 'Addiction à l alcool',
    '77': 'Addiction aux benzodiazépines et médicaments psychotropes',
    '78': 'Addiction au cannabis cocaïne amphétamines opiacés',
    '79': 'Addictions comportementales',
    '80': 'Dopage et conduites dopantes',
    '81': 'Altération chronique de la vision',
    '82': 'Altération aiguë de la vision',
    '83': 'Infections et inflammations oculaires',
    '84': 'Glaucomes',
    '85': 'Troubles de la réfraction',
    '86': 'Pathologie des paupières',
    '87': 'Epistaxis',
    '88': 'Trouble aigu de la parole Dysphonie',
    '89': 'Altération de la fonction auditive',
    '90': 'Pathologie des glandes salivaires',
    '91': 'Déficit neurologique récent',
    '92': 'Déficit moteur et ou sensitif des membres',
    '93': 'Compression médullaire et syndrome de la queue de cheval',
    '94': 'Rachialgie',
    '95': 'Radiculalgie et syndrome canalaire',
    '96': 'Neuropathies périphériques',
    '97': 'Guillain-Barré — polyradiculonévrite aiguë',
    '98': 'Myasthénie',
    '99': 'Migraine névralgie du trijumeau et algies de la face',
    '100': 'Céphalée inhabituelle aiguë et chronique',
    '101': 'Paralysie faciale',
    '102': 'Diplopie',
    '103': 'Vertige',
    '104': 'Sclérose en plaques',
    '105': 'Épilepsie de l enfant et de l adulte',
    '106': 'Maladie de Parkinson',
    '107': 'Mouvements anormaux',
    '108': 'Confusion démences voir item 132',
    '109': 'Troubles de la marche et de l équilibre',
    '110': 'Troubles du sommeil de l enfant et de l adulte',
    '111': 'Dermatoses faciales acné rosacée dermatite séborrhéique',
    '112': 'Dermatose bulleuse touchant la peau et ou les muqueuses externes',
    '113': 'Hémangiomes et malformations vasculaires cutanées',
    '114': 'Exanthème et érythrodermie adulte et enfant',
    '115': 'Toxidermies',
    '116': 'Prurit',
    '117': 'Psoriasis',
    '118': 'La personne handicapée — évaluation fonctionnelle',
    '119': 'Soins et accompagnement dans la maladie chronique et le handicap',
    '120': 'Complications de l immobilité et du décubitus',
    '121': 'Le handicap psychique',
    '122': 'Techniques de rééducation et de réadaptation',
    '123': 'Vieillissement normal — aspects biologiques et sociologiques',
    '124': 'Ménopause insuffisance ovarienne prématurée et andropause',
    '125': 'Troubles de la miction et incontinence urinaire',
    '126': 'Trouble de l érection',
    '127': 'Hypertrophie bénigne de la prostate',
    '128': 'Ostéopathies fragilisantes',
    '129': 'Arthrose',
    '130': 'La personne âgée malade — particularités thérapeutiques',
    '131': 'Troubles de la marche et de l équilibre',
    '132': 'Troubles cognitifs du sujet âgé',
    '133': 'Autonomie et dépendance chez le sujet âgé',
    '134': 'Physiopathologie de la douleur aiguë et chronique',
    '135': 'Thérapeutiques antalgiques médicamenteuses et non médicamenteuses',
    '136': 'Anesthésie locale locorégionale et générale',
    '137': 'Douleur chez l enfant évaluation et traitements antalgique',
    '138': 'Douleur chez la personne vulnérable',
    '139': 'Soins palliatifs 1 — repères cliniques',
    '140': 'Soins palliatifs 2 — accompagnement du malade',
    '141': 'Soins palliatifs 3 — sédation pour détresse',
    '142': 'Soins palliatifs en pédiatrie',
    '143': 'Soins palliatifs en réanimation',
    '144': 'Deuil normal et pathologique',
    '145': 'Surveillance des maladies infectieuses transmissibles',
    '146': 'Vaccinations',
    '147': 'Fièvre aiguë chez l enfant et l adulte',
    '148': 'Infections naso-sinusiennes de l adulte et de l enfant',
    '149': 'Angines de l adulte et de l enfant',
    '150': 'Otites infectieuses de l adulte et de l enfant',
    '151': 'Méningites méningoencéphalites abcès cérébral',
    '152': 'Endocardite infectieuse',
    '153': 'Surveillance des porteurs de prothèses valvulaires',
    '154': 'Infections broncho-pulmonaires communautaires',
    '155': 'Infections cutanéo-muqueuses bactériennes et mycosiques',
    '156': 'Infections ostéo-articulaires IOA',
    '157': 'Bactériémie Fongémie de l adulte et de l enfant',
    '158': 'Sepsis et choc septique de l enfant et de l adulte',
    '159': 'Tuberculose de l adulte et de l enfant',
    '160': 'Tétanos',
    '161': 'Infections urinaires de l enfant et de l adulte',
    '162': 'Infections sexuellement transmissibles IST',
    '163': 'Coqueluche',
    '164': 'Exanthèmes fébriles de l enfant',
    '165': 'Oreillons',
    '166': 'Grippe',
    '167': 'Hépatites virales',
    '168': 'Infections à herpès virus du sujet immunocompétent',
    '169': 'Infections à VIH',
    '170': 'Paludisme',
    '171': 'Gale et pédiculose',
    '172': 'Parasitoses digestives',
    '173': 'Zoonoses',
    '174': 'Pathologie infectieuse chez les migrants',
    '175': 'Voyage en pays tropical — conseils et pathologies du retour',
    '176': 'Diarrhées infectieuses de l adulte et de l enfant',
    '177': 'Prescription et surveillance des anti-infectieux',
    '178': 'Risques émergents bioterrorisme maladies hautement transmissibles',
    '179': 'Risques sanitaires alimentaires et toxi-infections',
    '180': 'Risques sanitaires liés aux irradiations Radioprotection',
    '181': 'Sécurité sanitaire des produits — veille sanitaire',
    '182': 'Environnement professionnel et santé au travail',
    '183': 'Médecine du travail et prévention des risques',
    '184': 'Accidents du travail et maladies professionnelles',
    '185': 'Réaction inflammatoire — aspects biologiques et cliniques',
    '186': 'Hypersensibilités et allergies — physiopathologie et traitement',
    '187': 'Allergies cutanéomuqueuses — urticaire et dermatites',
    '188': 'Allergies respiratoires — asthme et rhinite',
    '189': 'Déficit immunitaire',
    '190': 'Fièvre prolongée',
    '191': 'Fièvre chez un patient immunodéprimé',
    '192': 'Pathologies auto-immunes',
    '193': 'Vascularites systémiques',
    '194': 'Lupus systémique LS Syndrome des anti-phospholipides SAPL',
    '195': 'Artérite à cellules géantes',
    '196': 'Polyarthrite rhumatoïde',
    '197': 'Spondyloarthrite',
    '198': 'Arthropathies microcristallines',
    '199': 'Syndrome douloureux régional complexe ex algodystrophie',
    '200': 'Douleur et épanchement articulaire Arthrite d évolution récente',
    '201': 'Transplantation d organes — immunologie et complications',
    '202': 'Biothérapies et thérapies ciblées',
    '203': 'Dyspnée aiguë et chronique',
    '204': 'Toux chez l enfant et chez l adulte',
    '205': 'Hémoptysie',
    '206': 'Épanchement pleural liquidien',
    '207': 'Opacités et masses intra-thoraciques',
    '208': 'Insuffisance respiratoire chronique',
    '209': 'Bronchopneumopathie chronique obstructive chez l adulte',
    '210': 'Pneumopathie interstitielle diffuse',
    '211': 'Sarcoïdose',
    '212': 'Hémogramme — indications et interprétation',
    '213': 'Anémie chez l adulte et l enfant',
    '214': 'Thrombopénie chez l adulte et l enfant',
    '215': 'Purpuras chez l adulte et l enfant',
    '216': 'Syndrome hémorragique d origine hématologique',
    '217': 'Syndrome mononucléosique',
    '218': 'Éosinophilie',
    '219': 'Pathologie du fer chez l adulte et l enfant',
    '220': 'Adénopathie superficielle',
    '221': 'Athérome — épidémiologie et malade poly-athéromateux',
    '222': 'Facteurs de risque cardio-vasculaire et prévention',
    '223': 'Dyslipidémies',
    '224': 'Hypertension artérielle de l adulte et de l enfant',
    '225': 'Artériopathie des membres inférieurs et anévrysmes',
    '226': 'Thrombose veineuse profonde et embolie pulmonaire',
    '227': 'Insuffisance veineuse chronique Varices',
    '228': 'Ulcère de jambe',
    '229': 'Surveillance et complications des abords veineux',
    '230': 'Douleur thoracique aiguë',
    '231': 'Électrocardiogramme indications et interprétations',
    '232': 'Fibrillation atriale',
    '233': 'Valvulopathies',
    '234': 'Insuffisance cardiaque de l adulte',
    '235': 'Péricardite aiguë',
    '236': 'Troubles de la conduction intracardiaque',
    '237': 'Palpitations',
    '238': 'Souffle cardiaque chez l enfant',
    '239': 'Acrosyndromes — phénomène de Raynaud',
    '240': 'Hypoglycémie chez l adulte et l enfant',
    '241': 'Goitre nodules et cancers thyroïdiens',
    '242': 'Hyperthyroïdie',
    '243': 'Hypothyroïdie',
    '244': 'Adénome hypophysaire',
    '245': 'Insuffisance surrénale chez l adulte et l enfant',
    '246': 'Gynécomastie',
    '247': 'Diabète type 1 et 2 — complications',
    '248': 'Prévention primaire par la nutrition',
    '249': 'Modifications du mode de vie — alimentation et activité physique',
    '250': 'Dénutrition chez l adulte et l enfant',
    '251': 'Amaigrissement à tous les âges',
    '252': 'Troubles nutritionnels chez le sujet âgé',
    '253': 'Obésité de l enfant et de l adulte',
    '254': 'Besoins nutritionnels de la femme enceinte',
    '255': 'Diabète gestationnel',
    '256': 'Aptitude au sport et nutrition du sportif',
    '257': 'Œdèmes des membres inférieurs localisés ou généralisés',
    '258': 'Élévation de la créatininémie',
    '259': 'Protéinurie et syndrome néphrotique',
    '260': 'Hématurie',
    '261': 'Néphropathie glomérulaire',
    '262': 'Néphropathies interstitielles',
    '263': 'Néphropathies vasculaires',
    '264': 'Insuffisance rénale chronique',
    '265': 'Lithiase urinaire',
    '266': 'Polykystose rénale',
    '267': 'Troubles acido-basiques et désordres hydroélectrolytiques',
    '268': 'Hypercalcémie',
    '269': 'Douleurs abdominales aiguës chez l enfant et chez l adulte',
    '270': 'Douleurs lombaires aiguës',
    '271': 'Reflux gastro-œsophagien et hernie hiatale',
    '272': 'Ulcère gastrique et duodénal Gastrite',
    '273': 'Dysphagie',
    '274': 'Vomissements du nourrisson enfant et adulte',
    '275': 'Splénomégalie',
    '276': 'Hépatomégalie et masse abdominale',
    '277': 'Lithiase biliaire et complications',
    '278': 'Ictère de l adulte et de l enfant',
    '279': 'Cirrhose et complications',
    '280': 'Ascite',
    '281': 'Pancréatite chronique',
    '282': 'Maladies inflammatoires chroniques intestinales MICI',
    '283': 'Constipation',
    '284': 'Colopathie fonctionnelle',
    '285': 'Diarrhée chronique',
    '286': 'Diarrhée aiguë et déshydratation',
    '287': 'Diverticulose et diverticulite aiguë du sigmoïde',
    '288': 'Pathologie hémorroïdaire',
    '289': 'Hernie pariétale',
    '290': 'Épidémiologie prévention et dépistage des cancers',
    '291': 'Cancer cancérogénèse oncogénétique',
    '292': 'Diagnostic des cancers — investigations et stadification',
    '293': 'Prélèvements en anatomopathologie',
    '294': 'Traitements des cancers — modalités et complications',
    '295': 'Accompagnement du malade atteint de cancer',
    '296': 'Agranulocytose médicamenteuse conduite à tenir',
    '297': 'Cancer de l enfant — particularités',
    '298': 'Tumeurs ORL et voies aérodigestives supérieures',
    '299': 'Tumeurs intracrâniennes',
    '300': 'Tumeurs du col utérin tumeur du corps utérin',
    '301': 'Tumeurs du colon et du rectum',
    '302': 'Tumeurs cutanées épithéliales et mélanomes',
    '303': 'Tumeurs de l estomac',
    '304': 'Tumeurs du foie primitives et secondaires',
    '305': 'Tumeurs de l œsophage',
    '306': 'Tumeurs de l ovaire',
    '307': 'Tumeurs des os primitives et secondaires',
    '308': 'Tumeurs du pancréas',
    '309': 'Tumeurs du poumon primitives et secondaires',
    '310': 'Tumeurs de la prostate',
    '311': 'Tumeurs du rein de l adulte',
    '312': 'Tumeurs du sein',
    '313': 'Tumeurs du testicule',
    '314': 'Tumeurs vésicales',
    '315': 'Leucémies aiguës',
    '316': 'Syndromes myélodysplasiques',
    '317': 'Syndromes myéloprolifératifs',
    '318': 'Leucémies lymphoïdes chroniques',
    '319': 'Lymphomes malins',
    '320': 'Myélome multiple des os',
    '321': 'Bon usage du médicament',
    '322': 'Décision thérapeutique personnalisée — situations à risque',
    '323': 'Analyse critique des études cliniques — niveaux de preuve',
    '324': 'Éducation thérapeutique observance et automédication',
    '325': 'Risques iatrogènes et erreurs médicamenteuses',
    '326': 'Cadre réglementaire de la prescription',
    '327': 'Médecine intégrative et thérapies complémentaires',
    '328': 'Thérapeutiques non médicamenteuses et dispositifs médicaux',
    '329': 'Produits sanguins labiles PSL',
    '330': 'Prescription et surveillance des médicaments les plus courants',
    '331': 'Arrêt cardio-circulatoire',
    '332': 'État de choc — étiologies et prise en charge',
    '333': 'Situations exceptionnelles',
    '334': 'Prise en charge du brûlé et du polytraumatisé',
    '335': 'Traumatisme crânio-facial et oculaire',
    '336': 'Coma non traumatique chez l adulte et chez l enfant',
    '337': 'Principales intoxications aiguës',
    '338': 'Œdème de Quincke et anaphylaxie',
    '339': 'Syndromes coronariens aigus',
    '340': 'Accidents vasculaires cérébraux',
    '341': 'Hémorragie méningée',
    '342': 'Malaise perte de connaissance crise comitiale',
    '343': 'État confusionnel et trouble de conscience',
    '344': 'Pré-éclampsie',
    '345': 'Malaise grave du nourrisson et mort inattendue',
    '346': 'Convulsions chez le nourrisson et chez l enfant',
    '347': 'Rétention aiguë d urine',
    '348': 'Insuffisance rénale aiguë - Anurie',
    '349': 'Infections des parties molles abcès panaris phlegmon',
    '350': 'Grosse jambe rouge aiguë',
    '351': 'Agitation et délire aigu',
    '352': 'Crise d angoisse aiguë et attaque de panique',
    '353': 'Risque et conduite suicidaires',
    '354': 'Syndrome occlusif de l enfant et de l adulte',
    '355': 'Hémorragie digestive',
    '356': 'Appendicite de l enfant et de l adulte',
    '357': 'Péritonite aiguë chez l enfant et chez l adulte',
    '358': 'Pancréatite aiguë',
    '359': 'Détresse et insuffisance respiratoire aiguë',
    '360': 'Pneumothorax',
    '361': 'Lésions péri-articulaires du genou cheville et épaule',
    '362': 'Prothèses et ostéosynthèses',
    '363': 'Fractures fréquentes de l adulte et du sujet âgé',
    '364': 'Fractures chez l enfant — particularités',
    '365': 'Surveillance d un malade sous plâtre résine',
    '366': 'Exposition accidentelle aux liquides biologiques AES',
    '367': 'Impact de l environnement sur la santé',
}

# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(d):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def today():
    return datetime.now().strftime('%Y-%m-%d')

def shift(date_str, days):
    return (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')

# ---------------------------------------------------------------------------
# Routes Flask
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/api/overview')
def api_overview():
    data = load_data()
    t = today()
    days_left = (datetime.strptime(CONCOURS, '%Y-%m-%d') - datetime.now()).days
    items_data = {k: v for k, v in data.items() if not k.startswith('_')}
    vus = sum(1 for d in items_data.values() if len(d.get('reviews', [])) >= 3)
    en_cours = sum(1 for d in items_data.values() if 0 < len(d.get('reviews', [])) < 3)
    due = sum(
        1 for d in items_data.values()
        for rev in [d.get('reviews', [])]
        if 0 < len(rev) < 3 and shift(rev[-1], 2) <= t
    )
    return jsonify({
        'today': t, 'days_left': days_left, 'total': len(ITEMS),
        'vus': vus, 'en_cours': en_cours,
        'non_vus': len(ITEMS) - vus - en_cours, 'due': due,
    })

@app.route('/api/items')
def api_items():
    data = load_data()
    t = today()
    out = []
    for num, titre in ITEMS.items():
        d = data.get(num, {})
        rev = d.get('reviews', [])
        n = len(rev)
        nxt = shift(rev[-1], 2) if 0 < n < 3 else None
        out.append({
            'num': num, 'titre': titre, 'tours': n,
            'status': 'vu' if n >= 3 else ('en_cours' if n > 0 else 'non_vu'),
            'last': rev[-1] if rev else None, 'next': nxt,
            'score': d.get('score'),
            'due': nxt is not None and nxt <= t,
            'overdue': nxt is not None and nxt < t,
        })
    return jsonify(out)

@app.route('/api/review', methods=['POST'])
def api_review():
    body = request.json
    nums = [str(n).strip() for n in body.get('items', [])]
    t = body.get('date', today())
    data = load_data()
    completed, errors, added = [], [], []
    for num in nums:
        if not num: continue
        if num not in ITEMS:
            errors.append('Item {} inconnu'.format(num)); continue
        if num not in data:
            data[num] = {'reviews': [], 'score': None}
        rev = data[num]['reviews']
        if len(rev) >= 3:
            errors.append('Item {} : 3 tours deja effectues'.format(num)); continue
        if rev and rev[-1] == t:
            errors.append('Item {} : deja note aujourd\'hui'.format(num)); continue
        rev.append(t)
        added.append(num)
        if len(rev) == 3:
            completed.append({'num': num, 'titre': ITEMS[num]})
    save_data(data)
    return jsonify({'added': added, 'completed': completed, 'errors': errors})

@app.route('/api/score', methods=['POST'])
def api_score():
    body = request.json
    num = str(body.get('item', ''))
    score = body.get('score')
    if num not in ITEMS or not isinstance(score, int) or not (1 <= score <= 10):
        return jsonify({'ok': False, 'error': 'Parametres invalides'}), 400
    data = load_data()
    if num not in data:
        data[num] = {'reviews': [], 'score': None}
    data[num]['score'] = score
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/undo', methods=['POST'])
def api_undo():
    num = str(request.json.get('item', ''))
    data = load_data()
    if num in data and data[num].get('reviews'):
        data[num]['reviews'].pop()
        if not data[num]['reviews']:
            del data[num]
        save_data(data)
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Rien a annuler'})

@app.route('/api/calendar')
def api_calendar():
    data = load_data()
    t = today()
    reviews_by_date, planned_by_date = {}, {}
    for num, d in data.items():
        if num.startswith('_'): continue
        rev = d.get('reviews', [])
        for rev_date in rev:
            reviews_by_date.setdefault(rev_date, []).append({'num': num, 'titre': ITEMS.get(num, '?')})
        if 0 < len(rev) < 3:
            nxt = shift(rev[-1], 2)
            if nxt > t:
                planned_by_date.setdefault(nxt, []).append({'num': num, 'titre': ITEMS.get(num, '?'), 'tour': len(rev) + 1})
    return jsonify({
        'today': t, 'concours': CONCOURS, 'concours_days': CONCOURS_DAYS,
        'reviews': reviews_by_date, 'planned': planned_by_date,
        'work_time': data.get('_work_time', {}), 'lca': data.get('_lca', []),
    })

@app.route('/api/lca/mark', methods=['POST'])
def api_lca_mark():
    body = request.json or {}
    date = body.get('date', today())
    data = load_data()
    if '_lca' not in data: data['_lca'] = []
    if date not in data['_lca']: data['_lca'].append(date)
    save_data(data)
    return jsonify({'ok': True, 'date': date})

@app.route('/api/timer/save', methods=['POST'])
def api_timer_save():
    body = request.json
    date = body.get('date', today())
    seconds = int(body.get('seconds', 0))
    data = load_data()
    if '_work_time' not in data: data['_work_time'] = {}
    data['_work_time'][date] = seconds
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/timer/get')
def api_timer_get():
    data = load_data()
    t = today()
    return jsonify({'today': t, 'seconds': data.get('_work_time', {}).get(t, 0)})

# ---------------------------------------------------------------------------
# Interface HTML
# ---------------------------------------------------------------------------
HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tracker ECNi</title>
<style>
:root {
  --accent: #4355C6; --accent-dark: #3447B0; --green: #1A8A5A;
  --amber: #B45309; --red: #C0392B; --bg: #F7F7F7; --white: #FFFFFF;
  --border: #CCCCCC; --border-light: #E8E8E8; --text: #1A1A1A;
  --text-light: #666666; --r: 3px;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:13px;}
.header{background:#1A1A1A;color:white;padding:9px 14px 7px;}
.header-inner{max-width:880px;margin:0 auto;}
.hdr-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:5px;}
.header h1{font-size:.92rem;font-weight:700;letter-spacing:.01em;white-space:nowrap;}
.hdr-sub{color:#666;font-size:.72rem;font-weight:400;margin-left:8px;}
.hdr-stats{display:flex;gap:14px;flex-wrap:wrap;align-items:baseline;margin-bottom:5px;}
.hdr-s{font-size:.74rem;color:#777;}
.hdr-s strong{font-weight:700;color:white;font-size:.88rem;margin-right:2px;}
.hdr-s-due strong{color:#FCD34D;}
.jbadge{border:1px solid #444;border-radius:var(--r);padding:2px 8px;font-size:.72rem;color:#aaa;white-space:nowrap;flex-shrink:0;}
.jbadge-weeks{border:1px solid #444;border-radius:var(--r);padding:1px 8px;font-size:.68rem;color:#888;white-space:nowrap;margin-top:3px;text-align:center;}
.pbar{height:2px;background:#2a2a2a;overflow:hidden;}
.pbar-fill{height:100%;background:#4ADE80;transition:width .5s;}
.page{max-width:880px;margin:0 auto;padding:11px 14px 40px;}
.tabs{display:flex;gap:0;margin-bottom:11px;border-bottom:1px solid var(--border);}
.tab-btn{padding:6px 16px;border:none;background:none;font-size:.84rem;font-weight:600;color:var(--text-light);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;}
.tab-btn.active{color:var(--accent);border-bottom-color:var(--accent);}
.tab-btn:hover:not(.active){color:var(--text);}
.card{background:var(--white);border:1px solid var(--border);border-radius:var(--r);padding:11px 13px;margin-bottom:8px;}
.card-hdr{font-size:.78rem;font-weight:700;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;color:var(--text-light);text-transform:uppercase;letter-spacing:.05em;}
.due-item{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--border-light);}
.due-item:last-child{border-bottom:none;}
.due-num{font-weight:700;color:var(--accent);width:34px;flex-shrink:0;font-size:.84rem;}
.due-titre{flex:1;font-size:.82rem;line-height:1.35;min-width:0;}
.pill-tour{font-size:.7rem;font-weight:600;padding:1px 7px;border-radius:var(--r);white-space:nowrap;flex-shrink:0;border:1px solid;}
.pill-t2{border-color:#D97706;color:#B45309;background:#FFFBEB;}
.pill-t3{border-color:#16A34A;color:#166534;background:#F0FDF4;}
.pill-retard{font-size:.69rem;font-weight:600;padding:1px 6px;border:1px solid var(--red);color:var(--red);border-radius:var(--r);flex-shrink:0;}
.btn-fait{padding:4px 11px;background:var(--white);color:var(--green);border:1px solid var(--green);border-radius:var(--r);font-size:.77rem;font-weight:600;cursor:pointer;white-space:nowrap;flex-shrink:0;}
.btn-fait:hover{background:var(--green);color:white;}
.btn-fait:disabled{opacity:.4;cursor:default;}
.score-card{background:var(--white);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:var(--r);padding:10px 12px;margin-bottom:8px;}
.score-card h4{font-size:.81rem;font-weight:700;margin-bottom:2px;}
.score-card p{font-size:.75rem;color:var(--text-light);margin-bottom:8px;}
.score-btns{display:flex;gap:4px;flex-wrap:wrap;}
.score-btn{width:30px;height:30px;border-radius:var(--r);border:1px solid var(--border);background:white;font-size:.78rem;font-weight:600;cursor:pointer;}
.score-btn:hover{border-color:var(--accent);color:var(--accent);}
.score-btn.selected{background:var(--accent);color:white;border-color:var(--accent);}
.input-nums{flex:1;padding:6px 10px;border:1px solid var(--border);border-radius:var(--r);font-size:.86rem;font-family:inherit;resize:none;}
.input-nums:focus{outline:none;border-color:var(--accent);}
.btn-primary{padding:6px 15px;background:var(--accent);color:white;border:1px solid var(--accent);border-radius:var(--r);font-size:.82rem;font-weight:600;cursor:pointer;white-space:nowrap;}
.btn-primary:hover{background:var(--accent-dark);}
.input-hint{font-size:.72rem;color:var(--text-light);margin-top:5px;}
.feedback{padding:6px 10px;border-radius:var(--r);font-size:.79rem;margin-top:6px;display:none;border:1px solid;}
.feedback.ok{background:#F0FDF4;color:#166534;border-color:#86EFAC;}
.feedback.err{background:#FEF2F2;color:#991B1B;border-color:#FCA5A5;}
.filter-row{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:9px;}
.chip{padding:3px 10px;border-radius:var(--r);border:1px solid var(--border);background:white;font-size:.75rem;font-weight:600;cursor:pointer;color:var(--text-light);}
.chip.active{border-color:var(--accent);background:var(--accent);color:white;}
.chip:hover:not(.active){border-color:var(--accent);color:var(--accent);}
.chip-due{border-color:#D97706;color:#B45309;}
.chip-due.active{background:#D97706;border-color:#D97706;color:white;}
.search{width:100%;padding:5px 10px;border:1px solid var(--border);border-radius:var(--r);font-size:.86rem;font-family:inherit;margin-bottom:9px;}
.search:focus{outline:none;border-color:var(--accent);}
.tbl-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:.79rem;}
th{padding:5px 10px;text-align:left;font-size:.69rem;font-weight:700;color:var(--text-light);background:var(--bg);border-bottom:1px solid var(--border);text-transform:uppercase;letter-spacing:.05em;white-space:nowrap;}
td{padding:5px 10px;border-bottom:1px solid var(--border-light);vertical-align:middle;}
tr:hover td{background:#F5F5F5;}
tr.row-due td{background:#FFFBEB;}
tr.row-due:hover td{background:#FEF3C7;}
.num-col{font-weight:700;color:var(--accent);width:40px;}
.titre-col{max-width:340px;}
.badge{display:inline-block;padding:1px 6px;border-radius:var(--r);font-size:.7rem;font-weight:600;white-space:nowrap;border:1px solid;}
.b-nv{border-color:#D1D5DB;color:#6B7280;background:#F9FAFB;}
.b-ec{border-color:#D97706;color:#B45309;background:#FFFBEB;}
.b-vu{border-color:#16A34A;color:#166534;background:#F0FDF4;}
.score-low{font-weight:700;color:var(--red);}
.score-mid{font-weight:700;color:var(--amber);}
.score-hi{font-weight:700;color:var(--green);}
.btn-link{font-size:.72rem;color:var(--accent);text-decoration:underline;background:none;border:none;cursor:pointer;padding:0;}
.btn-undo{padding:1px 7px;font-size:.7rem;border-radius:var(--r);border:1px solid var(--border);background:white;cursor:pointer;color:var(--text-light);}
.btn-undo:hover{color:var(--red);border-color:var(--red);}
.empty{padding:30px;text-align:center;color:var(--text-light);font-size:.82rem;}
.btn-sm-all{padding:3px 9px;font-size:.73rem;border-radius:var(--r);border:1px solid var(--border);background:white;cursor:pointer;color:var(--text-light);font-weight:600;}
.btn-sm-all:hover{border-color:var(--green);color:var(--green);}
.hidden{display:none!important;}
.search-wrap{position:relative;margin-bottom:6px;}
.search-dd{position:absolute;top:100%;left:0;right:0;background:white;border:1px solid var(--border);border-top:none;border-radius:0 0 var(--r) var(--r);max-height:180px;overflow-y:auto;z-index:200;box-shadow:0 3px 8px rgba(0,0,0,.12);}
.search-dd-item{padding:6px 10px;cursor:pointer;font-size:.8rem;border-bottom:1px solid var(--border-light);display:flex;align-items:center;gap:6px;}
.search-dd-item:last-child{border-bottom:none;}
.search-dd-item:hover,.search-dd-item.dd-active{background:#F0F4FF;}
.dd-num{font-weight:700;color:var(--accent);flex-shrink:0;}
.dd-titre{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.dd-status{font-size:.68rem;color:var(--text-light);flex-shrink:0;}
.sel-items{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px;}
.sel-pill{background:#EEF1FF;border:1px solid #C7CEFF;color:var(--accent);border-radius:var(--r);padding:2px 6px 2px 8px;font-size:.74rem;font-weight:600;display:flex;align-items:center;gap:3px;}
.sel-pill-x{background:none;border:none;cursor:pointer;color:#999;padding:0 0 0 2px;font-size:1.1rem;line-height:1;}
.sel-pill-x:hover{color:var(--red);}
.cal-outer{overflow-x:auto;padding-bottom:4px;}
.cal-grid{display:grid;grid-template-columns:40px repeat(7,1fr);gap:2px;min-width:520px;}
.cal-hdr-cell{font-size:.65rem;font-weight:700;color:var(--text-light);text-align:center;padding:2px 0 4px;text-transform:uppercase;}
.cal-wlbl{font-size:.63rem;color:var(--text-light);line-height:1.3;padding-top:4px;}
.cal-cell{min-height:48px;background:var(--white);border:1px solid var(--border-light);border-radius:var(--r);padding:3px 4px;overflow:hidden;}
.cal-cell.is-today{border-color:var(--accent);border-width:2px;}
.cal-cell.is-future{background:#FAFAFA;}
.cal-cell.is-concours{background:#F0EEFF;border-color:#7C3AED;border-width:2px;}
.cal-dnum{font-size:.66rem;font-weight:700;color:#ccc;margin-bottom:2px;}
.cal-dnum.is-today{color:var(--accent);}
.cal-dnum.is-concours{color:#7C3AED;font-size:.75rem;}
.cal-concours-lbl{font-size:.58rem;font-weight:700;color:#7C3AED;margin-top:1px;display:block;}
.cal-pill{font-size:.59rem;font-weight:600;padding:1px 3px;border-radius:2px;margin-bottom:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;display:block;}
.cal-p-done{background:#EEF1FF;color:var(--accent);}
.cal-p-t2{background:#FFFBEB;color:#B45309;}
.cal-p-t3{background:#F0FDF4;color:#166534;}
.cal-p-lca{background:#D1FAE5;color:#065F46;font-weight:700;}
.cal-worktime{font-size:.58rem;font-weight:600;color:#888;margin-top:2px;display:block;}
.cal-section-lbl{grid-column:1/-1;font-size:.7rem;font-weight:700;color:var(--text-light);padding:6px 0 2px;text-transform:uppercase;letter-spacing:.05em;}
.sel-pill-lca{background:#D1FAE5;border-color:#6EE7B7;color:#065F46;}
.dd-lca-badge{font-size:.68rem;font-weight:700;background:#D1FAE5;color:#065F46;border-radius:3px;padding:1px 5px;flex-shrink:0;}
.chrono-wrap{display:flex;align-items:center;gap:10px;}
.chrono-display{font-size:1.25rem;font-weight:700;color:white;letter-spacing:.06em;font-variant-numeric:tabular-nums;min-width:80px;}
.chrono-display.running{color:#4ADE80;}
.chrono-play-btn{width:28px;height:28px;border:none;background:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;padding:0;opacity:.7;}
.chrono-play-btn:hover{opacity:1;}
.chrono-play-btn.running{opacity:1;}
.chrono-play-btn svg{width:16px;height:16px;}
</style>
</head>
<body>
<div class="header">
  <div class="header-inner">
    <div class="hdr-top">
      <h1>Tracker ECNi<span class="hdr-sub" id="hdr-sub"></span></h1>
      <div class="chrono-wrap">
        <span class="chrono-display" id="chrono-display">00:00:00</span>
        <button type="button" class="chrono-play-btn" id="chrono-btn" onclick="toggleChrono()"><svg viewBox="0 0 24 24" fill="white" stroke="none" width="16" height="16"><path d="M8 5v14l11-7z"/></svg></button>
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0;">
        <div class="jbadge" id="jbadge">EDN J-...</div>
        <div class="jbadge jbadge-weeks" id="jbadge-weeks">S-...</div>
      </div>
    </div>
    <div class="hdr-stats">
      <span class="hdr-s"><strong id="sv-vus">—</strong> vus</span>
      <span class="hdr-s"><strong id="sv-ec">—</strong> en cours</span>
      <span class="hdr-s"><strong id="sv-nv">—</strong> non vus</span>
      <span class="hdr-s hdr-s-due"><strong id="sv-due">—</strong> aujourd\'hui</span>
    </div>
    <div class="pbar"><div class="pbar-fill" id="pbar-fill" style="width:0%"></div></div>
  </div>
</div>
<div class="page">
  <nav class="tabs">
    <div class="tab-btn active" data-tab="today">Aujourd\'hui</div>
    <div class="tab-btn" data-tab="all">Tous les items (367)</div>
    <div class="tab-btn" data-tab="cal">Calendrier</div>
  </nav>
  <div id="tab-today">
    <div class="card" id="due-card">
      <div class="card-hdr">
        <span id="due-title">Lectures dues aujourd\'hui</span>
        <button class="btn-sm-all hidden" id="btn-all" onclick="markAllDue()">Tout cocher</button>
      </div>
      <div id="due-list"><div class="empty">Chargement...</div></div>
    </div>
    <div id="score-prompts"></div>
    <div class="card">
      <div class="card-hdr">Nouveaux items vus aujourd\'hui — 1ere lecture</div>
      <div class="search-wrap">
        <input type="text" class="input-nums" id="inp-search" autocomplete="off"
          placeholder="Rechercher un item par numero ou titre..."
          oninput="onSearchInput()" onkeydown="onSearchKey(event)">
        <div id="search-dd" class="search-dd hidden"></div>
      </div>
      <div class="sel-items" id="sel-items"></div>
      <div style="display:flex;align-items:center;gap:8px;">
        <button class="btn-primary" id="btn-validate" onclick="submitNew()" disabled>Valider</button>
        <span style="font-size:.72rem;color:var(--text-light);" id="sel-count"></span>
      </div>
      <div class="input-hint" style="margin-top:5px;">Selectionnez les items, puis validez.</div>
      <div class="feedback" id="fb-new"></div>
    </div>
  </div>
  <div id="tab-cal" style="display:none">
    <div class="card">
      <div class="card-hdr">Calendrier des revisions</div>
      <div class="cal-outer" id="cal-container"><div class="empty">Cliquez sur l\'onglet pour charger...</div></div>
    </div>
  </div>
  <div id="tab-all" style="display:none">
    <div class="card">
      <div class="filter-row">
        <button class="chip active" data-f="all" onclick="setFilter(\'all\')">Tous <span id="c-all"></span></button>
        <button class="chip" data-f="non_vu" onclick="setFilter(\'non_vu\')">Non vus <span id="c-nv"></span></button>
        <button class="chip" data-f="en_cours" onclick="setFilter(\'en_cours\')">En cours <span id="c-ec"></span></button>
        <button class="chip" data-f="vu" onclick="setFilter(\'vu\')">Vus <span id="c-vu"></span></button>
        <button class="chip chip-due" data-f="due" onclick="setFilter(\'due\')">A reviser <span id="c-due"></span></button>
      </div>
      <input class="search" id="srch" placeholder="Rechercher par numero ou titre..." oninput="renderTable()">
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>N°</th><th>Titre</th><th>Statut</th><th style="text-align:center">Tours</th><th>Prochaine revision</th><th>Note</th><th></th></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>
<script>
var S = { items: [], filter: "all", selNums: [] };

async function api(path, method, body) {
  var opts = { method: method || "GET", headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  var r = await fetch(path, opts);
  return r.json();
}

var C = { running: false, seconds: 0, interval: null, saveInterval: null, today: "" };

async function initChrono() {
  var r = await api("/api/timer/get");
  C.today = r.today; C.seconds = r.seconds || 0; updateChronoDisplay();
}
function fmtTime(s) {
  var h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
  return (h<10?"0":"")+h+":"+(m<10?"0":"")+m+":"+(sec<10?"0":"")+sec;
}
function updateChronoDisplay() { document.getElementById("chrono-display").textContent = fmtTime(C.seconds); }
function toggleChrono() { if (C.running) pauseChrono(); else startChrono(); }

var SVG_PLAY  = \'<svg viewBox="0 0 24 24" fill="white" stroke="none" width="16" height="16"><path d="M8 5v14l11-7z"/></svg>\';
var SVG_PAUSE = \'<svg viewBox="0 0 24 24" fill="#4ADE80" stroke="none" width="16" height="16"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>\';

function startChrono() {
  C.running = true;
  var display = document.getElementById("chrono-display"), btn = document.getElementById("chrono-btn");
  display.classList.add("running"); btn.classList.add("running"); btn.innerHTML = SVG_PAUSE;
  C.interval = setInterval(function(){ C.seconds++; updateChronoDisplay(); }, 1000);
  C.saveInterval = setInterval(function(){ saveChrono(); }, 30000);
}
function pauseChrono() {
  C.running = false; clearInterval(C.interval); clearInterval(C.saveInterval);
  var display = document.getElementById("chrono-display"), btn = document.getElementById("chrono-btn");
  display.classList.remove("running"); btn.classList.remove("running"); btn.innerHTML = SVG_PLAY;
  saveChrono();
}
async function saveChrono() {
  if (C.seconds > 0) await api("/api/timer/save", "POST", { date: C.today, seconds: C.seconds });
}
window.addEventListener("beforeunload", function(){ if (C.running) pauseChrono(); });

async function init() {
  setupTabs();
  try {
    var ov = await api("/api/overview");
    var items = await api("/api/items");
    await initChrono();
    S.items = items; renderHeader(ov); renderToday(); renderTable();
  } catch(e) {
    document.getElementById("due-list").innerHTML =
      \'<div style="color:red;padding:12px;font-size:.82rem;"><strong>Erreur :</strong> \' + e.message + \'</div>\';
  }
}

function renderHeader(ov) {
  document.getElementById("jbadge").textContent = "EDN — J-" + ov.days_left;
  document.getElementById("jbadge-weeks").textContent = "S-" + Math.ceil(ov.days_left / 7);
  var d = ov.today.split("-");
  document.getElementById("hdr-sub").textContent = " · " + d[2] + "/" + d[1] + "/" + d[0];
  document.getElementById("sv-vus").textContent = ov.vus;
  document.getElementById("sv-ec").textContent = ov.en_cours;
  document.getElementById("sv-nv").textContent = ov.non_vus;
  document.getElementById("sv-due").textContent = ov.due;
  document.getElementById("pbar-fill").style.width = Math.round(ov.vus / ov.total * 100) + "%";
  document.getElementById("c-all").textContent = "(" + S.items.length + ")";
  document.getElementById("c-nv").textContent = "(" + ov.non_vus + ")";
  document.getElementById("c-ec").textContent = "(" + ov.en_cours + ")";
  document.getElementById("c-vu").textContent = "(" + ov.vus + ")";
  document.getElementById("c-due").textContent = "(" + ov.due + ")";
}

function renderToday() {
  var due = S.items.filter(function(i){ return i.due; });
  var listEl = document.getElementById("due-list"), btnAll = document.getElementById("btn-all");
  document.getElementById("due-title").textContent =
    due.length > 0 ? due.length + " lecture" + (due.length>1?"s":"") + " a faire aujourd\'hui" : "Lectures a faire aujourd\'hui";
  if (due.length === 0) {
    listEl.innerHTML = \'<div class="empty">Aucune revision due aujourd\\\'hui.</div>\';
    btnAll.classList.add("hidden"); return;
  }
  btnAll.classList.remove("hidden");
  listEl.innerHTML = due.map(function(item) {
    var tourNum = item.tours + 1;
    var pillClass = tourNum === 2 ? "pill-tour pill-t2" : "pill-tour pill-t3";
    var retard = item.overdue ? \'<span class="pill-retard">En retard</span>\' : "";
    return \'<div class="due-item" id="di-\'+item.num+\'">\' +
      \'<div class="due-num">#\'+item.num+\'</div>\' +
      \'<div class="due-titre">\'+item.titre+\'</div>\' +
      retard + \'<span class="\'+pillClass+\'">\'+tourNum+\'eme lecture</span>\' +
      \'<button class="btn-fait" id="bf-\'+item.num+\'" onclick="markDue(\\\'\'+ item.num +\'\\\')"">Fait</button>\' +
      \'</div>\';
  }).join("");
}

async function markDue(num) {
  var btn = document.getElementById("bf-"+num); btn.disabled=true; btn.textContent="...";
  var r = await api("/api/review","POST",{items:[num]});
  if (r.completed && r.completed.length>0) showScorePrompts(r.completed);
  await refresh();
}
async function markAllDue() {
  var due = S.items.filter(function(i){return i.due;}).map(function(i){return i.num;});
  var r = await api("/api/review","POST",{items:due});
  if (r.completed && r.completed.length>0) showScorePrompts(r.completed);
  await refresh();
}
function showScorePrompts(items) {
  var container = document.getElementById("score-prompts"), existing = container.innerHTML;
  var html = items.map(function(item) {
    var titre = item.titre.length>65 ? item.titre.substring(0,62)+"..." : item.titre;
    var btns = [1,2,3,4,5,6,7,8,9,10].map(function(n){
      return \'<button class="score-btn" onclick="submitScore(\\\'\'+ item.num +\'\\\',\'+n+\',this)">\'+n+\'</button>\';
    }).join("");
    return \'<div class="score-card" id="sp-\'+item.num+\'">\' +
      \'<h4>Item #\'+item.num+\' complete (3 tours)</h4>\' +
      \'<p>Titre : \'+titre+\'<br>Ta note de maitrise sur 10 :</p>\' +
      \'<div class="score-btns">\'+btns+\'</div></div>\';
  }).join("");
  container.innerHTML = existing + html;
}
async function submitScore(num, score, btn) {
  btn.closest(".score-btns").querySelectorAll(".score-btn").forEach(function(b){b.classList.remove("selected");});
  btn.classList.add("selected");
  await api("/api/score","POST",{item:num,score:score});
  setTimeout(function(){ var sp=document.getElementById("sp-"+num); if(sp) sp.remove(); }, 900);
  var item = S.items.find(function(i){return i.num===num;});
  if (item) item.score = score;
  renderTable();
}

function onSearchInput() {
  var q = document.getElementById("inp-search").value.trim().toLowerCase();
  var dd = document.getElementById("search-dd");
  if (q.length===0) { dd.classList.add("hidden"); return; }
  var rows = [];
  var lcaMatch = "lca".indexOf(q)>=0 || "lecture critique".indexOf(q)>=0 || q==="l";
  if (lcaMatch && S.selNums.indexOf("lca")<0) {
    rows.push(\'<div class="search-dd-item" data-num="lca">\' +
      \'<span class="dd-lca-badge">LCA</span>\' +
      \'<span class="dd-titre">Lecture Critique d\\\'Article — sans repetition</span></div>\');
  }
  var matches = S.items.filter(function(i){
    return S.selNums.indexOf(i.num)<0 && (i.num.indexOf(q)>=0 || i.titre.toLowerCase().indexOf(q)>=0);
  }).slice(0,11);
  matches.forEach(function(i) {
    var statusTxt = i.status==="vu"?"Vu":i.status==="en_cours"?"En cours":"";
    rows.push(\'<div class="search-dd-item" data-num="\'+i.num+\'">\' +
      \'<span class="dd-num">#\'+i.num+\'</span>\' +
      \'<span class="dd-titre">\'+i.titre+\'</span>\' +
      (statusTxt?\'<span class="dd-status">\'+statusTxt+\'</span>\':\'\')+\'</div>\');
  });
  if (rows.length===0) { dd.classList.add("hidden"); return; }
  dd.innerHTML = rows.join(\'\'); dd.classList.remove("hidden");
}
function onSearchKey(e) {
  if (e.key==="Escape") { document.getElementById("search-dd").classList.add("hidden"); document.getElementById("inp-search").blur(); }
}
function selectItem(num) {
  if (S.selNums.indexOf(num)>=0) return;
  S.selNums.push(num);
  document.getElementById("inp-search").value = "";
  document.getElementById("search-dd").classList.add("hidden");
  renderSelItems();
}
function removeSelected(num) { S.selNums=S.selNums.filter(function(n){return n!==num;}); renderSelItems(); }
function renderSelItems() {
  var container=document.getElementById("sel-items"), btn=document.getElementById("btn-validate"), cnt=document.getElementById("sel-count");
  if (S.selNums.length===0) { container.innerHTML=""; btn.disabled=true; cnt.textContent=""; return; }
  container.innerHTML = S.selNums.map(function(num) {
    if (num==="lca") return \'<span class="sel-pill sel-pill-lca"><span>LCA</span><button class="sel-pill-x" data-num="lca">x</button></span>\';
    var item = S.items.find(function(i){return i.num===num;});
    var t = item ? (item.titre.length>35?item.titre.substring(0,33)+"...":item.titre) : num;
    return \'<span class="sel-pill"><span>#\'+num+\' \'+t+\'</span><button class="sel-pill-x" data-num="\'+num+\'">x</button></span>\';
  }).join(\'\');
  btn.disabled=false;
  cnt.textContent = S.selNums.length+" item"+(S.selNums.length>1?"s":"")+" selectionne"+(S.selNums.length>1?"s":"");
}
document.addEventListener("click", function(e) {
  var ddItem = e.target.closest(".search-dd-item");
  if (ddItem) { selectItem(ddItem.dataset.num); return; }
  var removeBtn = e.target.closest(".sel-pill-x");
  if (removeBtn) { removeSelected(removeBtn.dataset.num); return; }
  if (!e.target.closest(".search-wrap")) document.getElementById("search-dd").classList.add("hidden");
});
async function submitNew() {
  if (S.selNums.length===0) return;
  var hasLca=S.selNums.indexOf("lca")>=0, regularNums=S.selNums.filter(function(n){return n!=="lca";});
  var msgs=[], hasSuccess=false;
  if (hasLca) {
    var todayStr=C.today||localDateStr(new Date());
    await api("/api/lca/mark","POST",{date:todayStr});
    msgs.push("LCA enregistree pour aujourd\'hui."); hasSuccess=true;
  }
  if (regularNums.length>0) {
    var r=await api("/api/review","POST",{items:regularNums});
    if (r.completed&&r.completed.length>0) showScorePrompts(r.completed);
    if (r.added.length>0) { msgs.push(r.added.length+" item(s) ajoute(s) : "+r.added.map(function(n){return "#"+n;}).join(", ")+"."); hasSuccess=true; }
    if (r.errors.length>0) msgs.push(r.errors.join(" | "));
  }
  showFeedback("fb-new", msgs.join(" ")||"OK", hasSuccess?"ok":"err");
  if (hasSuccess) { S.selNums=[]; renderSelItems(); await refresh(); }
}

async function loadCalendar() {
  var cal = document.getElementById("tab-cal");
  try {
    var data = await api("/api/calendar");
    renderCalendar(data);
  } catch(e) {
    if (cal) cal.innerHTML=\'<div style="color:red;padding:20px;font-size:.82rem;"><strong>Erreur calendrier :</strong> \'+e.message+\'</div>\';
  }
}
function localDateStr(d) {
  var y=d.getFullYear(), m=d.getMonth()+1, day=d.getDate();
  return y+\'-\'+(m<10?\'0\':\'\')+m+\'-\'+(day<10?\'0\':\'\')+day;
}
function renderCalendar(data) {
  var t=data.today, tDate=new Date(t+"T12:00:00");
  var dayOfWeek=(tDate.getDay()+6)%7, monThisWeek=new Date(tDate);
  monThisWeek.setDate(tDate.getDate()-dayOfWeek);
  var startDate=new Date(monThisWeek); startDate.setDate(monThisWeek.getDate()-28);
  var days=["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"];
  var months=["Jan","Fev","Mar","Avr","Mai","Jun","Jul","Aou","Sep","Oct","Nov","Dec"];
  var concoursDays=data.concours_days||[data.concours||"2026-10-12"];
  var lastConcoursDay=concoursDays[concoursDays.length-1];
  var concoursDate=new Date(lastConcoursDay+"T12:00:00");
  var weeksToEnd=Math.ceil((concoursDate-startDate)/(7*24*3600*1000))+1;
  var totalWeeks=Math.max(weeksToEnd,10);
  var html=\'<div class="cal-grid">\';
  html+=\'<div class="cal-hdr-cell"></div>\';
  days.forEach(function(d){html+=\'<div class="cal-hdr-cell">\'+d+\'</div>\';});
  var pastDone=false;
  for (var w=0;w<totalWeeks;w++) {
    var wStart=new Date(startDate); wStart.setDate(startDate.getDate()+w*7);
    var wLbl=wStart.getDate()+" "+months[wStart.getMonth()];
    if (!pastDone && w>=4) { html+=\'<div class="cal-section-lbl">A venir (planifie)</div>\'; pastDone=true; }
    html+=\'<div class="cal-wlbl">\'+wLbl+\'</div>\';
    for (var d2=0;d2<7;d2++) {
      var day=new Date(wStart); day.setDate(wStart.getDate()+d2);
      var ds=localDateStr(day), isToday=ds===t, isFuture=ds>t;
      var concoursIdx=concoursDays.indexOf(ds), isConcours=concoursIdx>=0;
      var cls=\'cal-cell\'+(isConcours?\' is-concours\':isToday?\' is-today\':isFuture?\' is-future\':\'\');
      var dnumCls=\'cal-dnum\'+(isConcours?\' is-concours\':isToday?\' is-today\':\'\');
      html+=\'<div class="\'+cls+\'"><div class="\'+dnumCls+\'">\'+day.getDate()+\'</div>\';
      if (isConcours) html+=\'<span class="cal-concours-lbl">EDN J\'+(concoursIdx+1)+\'</span>\';
      if (data.reviews[ds]) data.reviews[ds].forEach(function(item){html+=\'<span class="cal-pill cal-p-done">#\'+item.num+\'</span>\';});
      if (isFuture&&data.planned[ds]) data.planned[ds].forEach(function(item){
        html+=\'<span class="cal-pill \'+( item.tour===2?\'cal-p-t2\':\'cal-p-t3\')+\'">#\'+item.num+\'</span>\';
      });
      if (data.lca&&data.lca.indexOf(ds)>=0) html+=\'<span class="cal-pill cal-p-lca">LCA</span>\';
      if (!isFuture&&data.work_time&&data.work_time[ds]) {
        var wt=data.work_time[ds], wh=Math.floor(wt/3600), wm=Math.floor((wt%3600)/60);
        html+=\'<span class="cal-worktime">\'+(wh>0?wh+\'h\'+(wm>0?wm+\'m\':\'\'): wm+\'min\')+\'</span>\';
      }
      html+=\'</div>\';
    }
  }
  html+=\'</div>\';
  document.getElementById("cal-container").innerHTML=html;
}

function showFeedback(id,msg,type) {
  var el=document.getElementById(id); el.textContent=msg; el.className="feedback "+type; el.style.display="block";
  setTimeout(function(){el.style.display="none";},5000);
}
function setFilter(f) {
  S.filter=f;
  document.querySelectorAll(".chip").forEach(function(c){ if(c.getAttribute("data-f")===f) c.classList.add("active"); else c.classList.remove("active"); });
  renderTable();
}
function renderTable() {
  var f=S.filter, srch=document.getElementById("srch").value.toLowerCase().trim(), items=S.items;
  if (f==="due") items=items.filter(function(i){return i.due;});
  else if (f!=="all") items=items.filter(function(i){return i.status===f;});
  if (srch) items=items.filter(function(i){return i.num.indexOf(srch)>=0||i.titre.toLowerCase().indexOf(srch)>=0;});
  var tbody=document.getElementById("tbody");
  if (items.length===0) { tbody.innerHTML=\'<tr><td colspan="7"><div class="empty">Aucun item.</div></td></tr>\'; return; }
  function fmtDate(d) { if(!d)return"—"; var p=d.split("-"); return p[2]+"/"+p[1]+"/"+p[0]; }
  tbody.innerHTML=items.map(function(item) {
    var bclass=item.status==="vu"?"badge b-vu":item.status==="en_cours"?"badge b-ec":"badge b-nv";
    var blabel=item.status==="vu"?"Vu":item.status==="en_cours"?"En cours":"Non vu";
    var nextTxt=item.next?fmtDate(item.next):"—";
    var nextCell=item.due?\'<strong style="color:\'+(item.overdue?"#E24B4A":"#D97706")+'">'+nextTxt+(item.overdue?" (!)":"")+\'</strong>\':nextTxt;
    var scoreCell="—";
    if (item.status==="vu") {
      if (item.score) { var cls=item.score>=8?"score-hi":item.score>=5?"score-mid":"score-low"; scoreCell=\'<span class="\'+cls+\'">\'+item.score+\'/10</span>\'; }
      else scoreCell=\'<button class="btn-link" onclick="promptScore(\\\'\'+ item.num +\'\\\')">\'+\'A noter</button>\';
    }
    var undoBtn=item.tours>0?\'<button class="btn-undo" onclick="undoItem(\\\'\'+ item.num +\'\\\')">\'+\'Annuler</button>\':"";
    return \'<tr class="\'+( item.due?"row-due":"")+\'">\' +
      \'<td class="num-col">\'+item.num+\'</td>\' +
      \'<td class="titre-col" style="font-size:.81rem">\'+item.titre+\'</td>\' +
      \'<td><span class="\'+bclass+\'">\'+blabel+\'</span></td>\' +
      \'<td style="text-align:center;color:#6B7280">\'+item.tours+\'/3</td>\' +
      \'<td>\'+nextCell+\'</td><td>\'+scoreCell+\'</td><td>\'+undoBtn+\'</td></tr>\';
  }).join("");
}
function promptScore(num) {
  var item=S.items.find(function(i){return i.num===num;});
  showTab("today"); showScorePrompts([item]); window.scrollTo({top:0,behavior:"smooth"});
}
async function undoItem(num) {
  if (!confirm("Annuler la derniere revision de l\'item #"+num+" ?")) return;
  var r=await api("/api/undo","POST",{item:num});
  if (r.ok) await refresh(); else alert(r.error||"Erreur");
}
async function refresh() {
  var res=await Promise.all([api("/api/overview"),api("/api/items")]);
  S.items=res[1]; renderHeader(res[0]); renderToday(); renderTable();
}
function showTab(t) {
  ["today","all","cal"].forEach(function(id){ var el=document.getElementById("tab-"+id); if(el) el.style.display=(id===t)?"block":"none"; });
  document.querySelectorAll(".tab-btn").forEach(function(btn){
    var isActive=btn.getAttribute("data-tab")===t;
    btn.style.color=isActive?"var(--accent)":"var(--text-light)";
    btn.style.borderBottomColor=isActive?"var(--accent)":"transparent";
  });
}
function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach(function(btn){
    btn.addEventListener("click",function(){ var t=btn.getAttribute("data-tab"); showTab(t); if(t==="cal") loadCalendar(); });
  });
}
init();
</script>
</body>
</html>'''

# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import webview

    # Icône Dock via pyobjc (natif macOS, pas de dépendance externe)
    icon_path = os.path.join(BASE, 'icon.png')
    try:
        from AppKit import NSApplication, NSImage
        if os.path.exists(icon_path):
            img = NSImage.alloc().initWithContentsOfFile_(icon_path)
            NSApplication.sharedApplication().setApplicationIconImage_(img)
    except Exception:
        pass

    print('\n  Tracker Revision ECNi — demarrage...\n')
    flask_thread = Thread(target=lambda: app.run(port=5001, debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1.2)

    webview.create_window('Tracker Revision ECNi', 'http://localhost:5001',
                          width=900, height=620, min_size=(700, 480))
    webview.start()
