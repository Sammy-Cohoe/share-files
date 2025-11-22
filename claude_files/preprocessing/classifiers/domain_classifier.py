"""Technical domain classification for patent documents."""

from typing import List, Dict


class DomainClassifier:
    """Classifies technical domain of invention disclosures."""
    
    TECH_DOMAINS = {
        'software': [
            'algorithm', 'software', 'computer', 'processor', 'application',
            'program', 'code', 'data', 'server', 'database', 'interface',
            'api', 'network', 'cloud', 'machine learning', 'artificial intelligence'
        ],
        'mechanical': [
            'mechanism', 'device', 'apparatus', 'structure', 'assembly',
            'component', 'gear', 'motor', 'bearing', 'valve', 'actuator',
            'mechanical', 'engine', 'machine', 'tool'
        ],
        'electrical': [
            'circuit', 'electrical', 'electronic', 'signal', 'voltage',
            'current', 'power', 'transistor', 'semiconductor', 'microprocessor',
            'integrated circuit', 'pcb', 'conductor', 'capacitor', 'resistor'
        ],
        'chemical': [
            'compound', 'composition', 'reaction', 'molecule', 'chemical',
            'synthesis', 'catalyst', 'polymer', 'solvent', 'reagent',
            'formulation', 'mixture', 'solution', 'substance'
        ],
        'biotechnology': [
            'protein', 'gene', 'cell', 'biological', 'organism', 'dna',
            'rna', 'enzyme', 'antibody', 'bacteria', 'virus', 'genetic',
            'biotechnology', 'genome', 'peptide'
        ],
        'medical': [
            'treatment', 'diagnosis', 'therapeutic', 'patient', 'medical',
            'clinical', 'disease', 'therapy', 'pharmaceutical', 'drug',
            'medicine', 'surgical', 'healthcare', 'diagnostic'
        ],
        'telecommunications': [
            'wireless', 'communication', 'antenna', 'frequency', 'transmission',
            'receiver', 'transmitter', 'signal processing', 'modulation',
            'bandwidth', 'cellular', '5g', 'radio'
        ],
        'optics': [
            'optical', 'laser', 'light', 'lens', 'photon', 'beam',
            'wavelength', 'spectrum', 'imaging', 'camera', 'display'
        ]
    }
    
    def classify(self, text: str, min_keywords: int = 2) -> List[str]:
        """
        Classify technical domain(s) of text.
        
        Args:
            text: Text to classify
            min_keywords: Minimum keyword matches to include a domain
            
        Returns:
            List of identified domains
        """
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in self.TECH_DOMAINS.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches >= min_keywords:
                domain_scores[domain] = matches
        
        # Sort by score and return domains
        sorted_domains = sorted(
            domain_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top domains (those with scores)
        domains = [domain for domain, score in sorted_domains]
        return domains if domains else ['general']
    
    def extract_technical_terms(self, text: str, max_terms: int = 20) -> List[str]:
        """
        Extract likely technical terms from text.
        
        Args:
            text: Text to analyze
            max_terms: Maximum number of terms to extract
            
        Returns:
            List of technical terms
        """
        # Simple heuristic: capitalized words (potential acronyms/proper nouns)
        # and multi-word technical phrases
        words = text.split()
        technical_terms = []
        
        for i, word in enumerate(words):
            # Remove punctuation for analysis
            clean_word = word.strip('.,;:!?()')
            
            # Capitalized words (not at sentence start)
            if len(clean_word) > 2 and clean_word[0].isupper() and i > 0:
                if words[i-1].endswith('.'):
                    continue  # Likely sentence start
                technical_terms.append(clean_word)
        
        # Return unique terms, limited to max_terms
        unique_terms = list(dict.fromkeys(technical_terms))  # Preserve order
        return unique_terms[:max_terms]
    
    def get_cpc_hints(self, domains: List[str]) -> List[str]:
        """
        Suggest CPC classes based on detected domains.
        
        Args:
            domains: List of detected technical domains
            
        Returns:
            List of suggested CPC class prefixes
        """
        # Simplified CPC mapping for query expansion
        cpc_mapping = {
            'software': ['G06F'],  # Computing
            'mechanical': ['F16'],  # Engineering elements
            'electrical': ['H01', 'H02'],  # Basic electric elements, power
            'chemical': ['C07', 'C08'],  # Organic chemistry, polymers
            'biotechnology': ['C12'],  # Biochemistry, microbiology
            'medical': ['A61'],  # Medical or veterinary science
            'telecommunications': ['H04'],  # Electric communication
            'optics': ['G02'],  # Optics
        }
        
        cpc_hints = []
        for domain in domains:
            if domain in cpc_mapping:
                cpc_hints.extend(cpc_mapping[domain])
        
        return list(set(cpc_hints))  # Remove duplicates
