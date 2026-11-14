"""Conservative market label classifier; no provider schema assumed."""
import re

def classify_market(label):
    s=re.sub(r'[_-]+',' ',str(label)).lower().strip()
    first=bool(re.search(r'first half|1st half|1h\b|premi[eè]re mi.temps',s))
    second=bool(re.search(r'second half|2nd half|2h\b|deuxi[eè]me mi.temps',s))
    period='unknown' if first and second else 'first_half' if first else 'second_half' if second else 'full_match'
    assist=bool(re.search(r'assists?|passe[s]? d[eé]cisive[s]?',s))
    goal=bool(re.search(r'goals?|scorer|buteur|but[s]? marqu',s))
    if assist==goal: return {'category':'unknown','threshold':None,'period':period,'needs_review':True}
    # Do not classify team totals, 'no goal' or opponent-specific negative propositions.
    if re.search(r'\b(team|total|under|no goal|not to score|without)\b',s):
        return {'category':'unknown','threshold':None,'period':period,'needs_review':True}
    thresholds=set()
    for n in (1,2,3):
        if re.search(r'(?<!\d)'+str(n)+r'\s*\+(?!\d)',s) or re.search(r'\b(?:at least|minimum)\s*'+str(n)+r'\b',s) or re.search(r'\b'+str(n)+r'\s+or more\b',s): thresholds.add(n)
        if re.search(r'\bover\s*'+str(n-1)+r'[.,]5\b',s): thresholds.add(n)
    if re.search(r'\b(anytime|to score)\b',s) and goal: thresholds.add(1)
    if re.search(r'\b(brace|doubl[eé])\b',s) and goal: thresholds.add(2)
    if re.search(r'\b(hat\s*trick|tripl[eé])\b',s) and goal: thresholds.add(3)
    threshold=next(iter(thresholds)) if len(thresholds)==1 else None
    return {'category':'assists' if assist else 'goals','threshold':threshold,'period':period,'needs_review':threshold is None or period=='unknown'}
