import random
import json
from typing import Dict, List
import numpy as np
from utils.config import PROFILES_FILE


class Big5ProfileGenerator:
    
    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_big5_traits(self) -> Dict[str, str]:
        categories = {
            'openness': ['closed', 'moderate', 'open'],
            'conscientiousness': ['disorganized', 'moderate', 'organized'],
            'extraversion': ['introverted', 'moderate', 'extraverted'],
            'agreeableness': ['disagreeable', 'moderate', 'agreeable'],
            'neuroticism': ['stable', 'moderate', 'neurotic']
        }
        
        traits = {}
        for trait, options in categories.items():
            traits[trait] = random.choice(options)
        
        return traits
    
    def calculate_stance(self, traits: Dict[str, str], user_id: int, total_users: int) -> int:
        if user_id < int(total_users * 0.4):
            return 0
        else:
            remaining_users = total_users - int(total_users * 0.4)
            remaining_id = user_id - int(total_users * 0.4)
            if remaining_id < remaining_users // 4:
                return -2
            elif remaining_id < remaining_users // 2:
                return -1
            elif remaining_id < remaining_users * 3 // 4:
                return 1
            else:
                return 2
    
    
    def generate_demographics(self) -> Dict[str, any]:
        age = int(np.random.beta(2, 3) * 47 + 18)
        
        gender = random.choice(['male', 'female', 'other'])
        
        return {
            'age': age,
            'gender': gender
        }
    
    def _get_trait_score(self, trait_value: str) -> float:
        score_map = {
            'closed': 0.2, 'moderate': 0.5, 'open': 0.8,
            'disorganized': 0.2, 'organized': 0.8,
            'introverted': 0.2, 'extraverted': 0.8,
            'disagreeable': 0.2, 'agreeable': 0.8,
            'stable': 0.2, 'neurotic': 0.8
        }
        return score_map.get(trait_value, 0.5)
    
    def generate_education_level(self, big5_traits: Dict[str, str]) -> str:
        conscientiousness_score = self._get_trait_score(big5_traits['conscientiousness'])
        openness_score = self._get_trait_score(big5_traits['openness'])
        
        education_score = (conscientiousness_score + openness_score) / 2
        
        if education_score >= 0.7:
            return str(np.random.choice(['master', 'phd'], p=[0.6, 0.4]))
        elif education_score >= 0.4:
            return str(np.random.choice(['bachelor', 'master'], p=[0.7, 0.3]))
        elif education_score >= 0.2:
            return str(np.random.choice(['high_school', 'bachelor'], p=[0.3, 0.7]))
        else:
            return str(np.random.choice(['high_school', 'bachelor'], p=[0.8, 0.2]))
    
    def generate_occupation(self, big5_traits: Dict[str, str], education: str) -> str:
        openness_score = self._get_trait_score(big5_traits['openness'])
        extraversion_score = self._get_trait_score(big5_traits['extraversion'])
        
        if education in ['master', 'phd']:
            if openness_score >= 0.6:
                return str(np.random.choice(['tech', 'education', 'creative'], p=[0.4, 0.3, 0.3]))
            else:
                return str(np.random.choice(['education', 'business', 'tech'], p=[0.4, 0.4, 0.2]))
        elif education == 'bachelor':
            if extraversion_score >= 0.6:
                return str(np.random.choice(['business', 'service', 'tech'], p=[0.4, 0.3, 0.3]))
            else:
                return str(np.random.choice(['tech', 'creative', 'business'], p=[0.4, 0.3, 0.3]))
        else:
            return str(np.random.choice(['service', 'business', 'other'], p=[0.5, 0.3, 0.2]))
    
    def generate_interests(self, big5_traits: Dict[str, str], occupation: str) -> List[str]:
        openness_score = self._get_trait_score(big5_traits['openness'])
        extraversion_score = self._get_trait_score(big5_traits['extraversion'])
        conscientiousness_score = self._get_trait_score(big5_traits['conscientiousness'])
        
        interest_categories = {
            'tech': ['programming', 'AI/ML', 'gadgets', 'cybersecurity', 'data_science'],
            'creative': ['art', 'music', 'writing', 'photography', 'design'],
            'outdoor': ['hiking', 'sports', 'travel', 'gardening', 'camping'],
            'social': ['social_media', 'networking', 'volunteering', 'community_events'],
            'intellectual': ['reading', 'research', 'philosophy', 'history', 'science'],
            'practical': ['cooking', 'DIY', 'finance', 'organization', 'productivity']
        }
        
        selected_interests = []
        
        if openness_score >= 0.6:
            selected_interests.extend(random.sample(interest_categories['creative'], 
                                                   min(2, len(interest_categories['creative']))))
            selected_interests.extend(random.sample(interest_categories['intellectual'], 
                                                   min(2, len(interest_categories['intellectual']))))
        
        if extraversion_score >= 0.6:
            selected_interests.extend(random.sample(interest_categories['social'], 
                                                   min(2, len(interest_categories['social']))))
            selected_interests.extend(random.sample(interest_categories['outdoor'], 
                                                   min(1, len(interest_categories['outdoor']))))
        
        if conscientiousness_score >= 0.6:
            selected_interests.extend(random.sample(interest_categories['practical'], 
                                                   min(2, len(interest_categories['practical']))))
        
        if occupation == 'tech':
            selected_interests.extend(random.sample(interest_categories['tech'], 
                                                   min(2, len(interest_categories['tech']))))
        elif occupation == 'creative':
            selected_interests.extend(random.sample(interest_categories['creative'], 
                                                   min(2, len(interest_categories['creative']))))
        
        if len(selected_interests) < 2:
            remaining_interests = []
            for category in interest_categories.values():
                remaining_interests.extend(category)
            remaining_interests = [i for i in remaining_interests if i not in selected_interests]
            needed = 2 - len(selected_interests)
            selected_interests.extend(random.sample(remaining_interests, 
                                                   min(needed, len(remaining_interests))))
        
        return selected_interests[:3]
    
    def generate_user_profile(self, user_id: int, total_users: int = 50) -> Dict[str, any]:
        big5_traits = self.generate_big5_traits()
        
        demographics = self.generate_demographics()
        
        stance = self.calculate_stance(big5_traits, user_id, total_users)
        
        education = self.generate_education_level(big5_traits)
        
        occupation = self.generate_occupation(big5_traits, education)
        
        interests = self.generate_interests(big5_traits, occupation)
        
        profile = {
            'name': f'user_{user_id}',
            'age': demographics['age'],
            'gender': demographics['gender'],
            'stance': stance,
            'education': education,
            'occupation': occupation,
            'interests': interests,
            'history': [],
            'openness': big5_traits['openness'],
            'conscientiousness': big5_traits['conscientiousness'],
            'extraversion': big5_traits['extraversion'],
            'agreeableness': big5_traits['agreeableness'],
            'neuroticism': big5_traits['neuroticism']
        }
        
        return profile
    
    def generate_multiple_profiles(self, num_users: int, seed: int = None) -> List[Dict[str, any]]:
        if seed is not None:
            self.__init__(seed)
        
        profiles = []
        for i in range(num_users):
            profile = self.generate_user_profile(i, num_users)
            profiles.append(profile)
        
        return profiles
    
    def save_profiles(self, profiles: List[Dict[str, any]], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    
    def analyze_profiles(self, profiles: List[Dict[str, any]]) -> Dict[str, any]:
        if not profiles:
            return {}
        
        stances = [p['stance'] for p in profiles]
        educations = [p['education'] for p in profiles]
        occupations = [p['occupation'] for p in profiles]
        
        big5_stats = {}
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            values = [p[trait] for p in profiles]
            from collections import Counter
            distribution = Counter(values)
            big5_stats[trait] = {
                'distribution': dict(distribution),
                'total': len(values)
            }
        
        education_distribution = Counter(educations)
        
        occupation_distribution = Counter(occupations)
        
        all_interests = []
        for profile in profiles:
            all_interests.extend(profile['interests'])
        interest_distribution = Counter(all_interests)
        
        return {
            'total_users': len(profiles),
            'stance_distribution': {
                'mean': round(np.mean(stances), 2),
                'distribution': {i: stances.count(i) for i in range(-2, 3)}
            },
            'education_distribution': dict(education_distribution),
            'occupation_distribution': dict(occupation_distribution),
            'top_interests': dict(interest_distribution.most_common(10)),
            'big5_traits': big5_stats
        }


def main():
    print("🤖 Big Five Personality Based User Profile Generator")
    print("=" * 50)
    
    generator = Big5ProfileGenerator(seed=42)
    
    print("📝 Generating 10 user profiles...")
    profiles = generator.generate_multiple_profiles(10, seed=42)
    
    output_file = PROFILES_FILE
    generator.save_profiles(profiles, output_file)
    print(f"💾 Saved to: {output_file}")
    
    print("\n📊 User Profile Statistics:")
    stats = generator.analyze_profiles(profiles)
    
    print(f"Total Users: {stats['total_users']}")
    print(f"Stance Distribution: {stats['stance_distribution']['distribution']}")
    
    print(f"\n🎓 Education Distribution: {stats['education_distribution']}")
    print(f"💼 Occupation Distribution: {stats['occupation_distribution']}")
    print(f"🎯 Top Interests: {stats['top_interests']}")
    
    print("\n🧠 Big Five Personality Distribution:")
    for trait, data in stats['big5_traits'].items():
        print(f"  {trait}: {data['distribution']}")
    
    print("\n👤 Sample Users:")
    for i, profile in enumerate(profiles[:3]):
        print(f"\nUser {i}:")
        print(f"  Age: {profile['age']}, Gender: {profile['gender']}")
        print(f"  AI Stance: {profile['stance']}")
        print(f"  Education: {profile['education']}")
        print(f"  Occupation: {profile['occupation']}")
        print(f"  Interests: {', '.join(profile['interests'])}")
        print(f"  Openness: {profile['openness']}")
        print(f"  Conscientiousness: {profile['conscientiousness']}")
        print(f"  Extraversion: {profile['extraversion']}")
        print(f"  Agreeableness: {profile['agreeableness']}")
        print(f"  Neuroticism: {profile['neuroticism']}")


if __name__ == "__main__":
    main()
