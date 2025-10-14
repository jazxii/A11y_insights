import re
from typing import List
from schemas import DetectedComponent
# A small rule-based parser to extract likely components from user story text.
COMPONENT_KEYWORDS = {
 'button': [r'button', r'click', r'tap'],
 'form': [r'form', r'submit', r'input field', r'input'],
 'modal': [r'modal', r'dialog', r'popup'],
 'toast': [r'toast', r'notification', r'alert'],
 'search': [r'search', r'find'],
 'navigation': [r'nav', r'navigate', r'menu', r'tab'],
 'image': [r'image', r'photo', r'thumbnail'],
 'link': [r'link', r'anchor'],
 'list': [r'list', r'items', r'results'],
}
def extract_components(text: str) -> List[DetectedComponent]:
 text_l = text.lower()
 found = {}
 for comp, patterns in COMPONENT_KEYWORDS.items():
     for p in patterns:
         if re.search(p, text_l):
             found[comp] = found.get(comp, 0) + 1
 components = []
 for c in found.keys():
     components.append(DetectedComponent(name=c, type=c, hint='Detected by keyword match'))
 # Fallback: if none found, suggest generic 'screen' component
 if not components:
     components.append(DetectedComponent(name='screen', type='screen', hint='No specific components detected - treat as full screen flow'))
 return components


