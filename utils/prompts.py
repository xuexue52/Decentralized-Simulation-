import json
from .config import MAX_FOLLOWING_POSTS, MAX_SERVER_POSTS


def build_create_post_prompt(profile: dict) -> str:
    return f"""# Posting Task
You are a social media user and need to publish an original post about the topic: Artificial Intelligence (AI).

# Your Profile
{json.dumps(profile, ensure_ascii=False, indent=2)}

Note: stance scale from -2 to 2 (-2=Strongly Oppose AI, -1=Oppose AI, 0=Neutral, 1=Support AI, 2=Strongly Support AI)

# Posting Guidelines
1. Your post must be related to the topic of Artificial Intelligence (AI), especially about whether AI brings more benefits or more risks (e.g., opinions, questions, personal experiences, or concerns about AI).
2. The content should faithfully reflect the characteristics of your profile.
3. **IMPORTANT: Keep your post content concise - maximum 40 words.**

Please return your post in the following format:
{{
    "content": "Post content (max 40 words)"
}}
"""


def build_environment_evaluation_prompt(user_id: str, profile: dict, server: str, visible_posts: list, memories: list = None) -> str:
    prompt = f"""You are a social media user (user {user_id}).please evaluate the discussion the current server: {server}.

Your personality traits:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Note: stance scale from -2 to 2 (-2=Strongly Oppose AI, -1=Oppose AI, 0=Neutral, 1=Support AI, 2=Strongly Support AI)

How do you evaluate the quality of social media content based on the posts you have seen (satisfaction level)?

Recent posts visible to you ({MAX_FOLLOWING_POSTS} from people you follow + {MAX_SERVER_POSTS} from current server, in chronological order):
{json.dumps(visible_posts, ensure_ascii=False, indent=2)}
"""
    
    if memories:
        memory_text = "\n\nPast experience (recent interactions):\n"
        for i, memory in enumerate(memories, 1):
            memory_text += f"{i}. {memory['action_type']}@{memory['server']}(stance {memory['stance']}) "
            memory_text += f"'{memory['content']}'\n"
            if memory.get('outcome'):
                memory_text += f"   Outcome: {memory['outcome']}\n"
        memory_text += "\nPlease consider these experiences when evaluating."
        prompt += memory_text
    
    prompt += """

# IMPORTANT: First provide your reasoning for the satisfaction level, then assign the score between 1 and 10 (1 = very poor, 10 = excellent). The reasoning should be concise and align with your score.

Respond in the following JSON format:
{{
    "reason": "A brief explanation of your evaluation (maximum 50 words)",
    "score": integer from 1 to 10
}}
"""
    return prompt


def build_decision_prompt(profile: dict, visible_posts_info: list, round_num: int, has_posted_this_round: bool = False) -> str:
    stance = profile.get('stance', 'unknown')
    history = profile.get('history', [])  
    
    age = profile.get('age', 0)
    gender = profile.get('gender', '')
    education = profile.get('education', '')
    occupation = profile.get('occupation', '')
    interests = profile.get('interests', [])
    
    openness = profile.get('openness', 'unknown')
    conscientiousness = profile.get('conscientiousness', 'unknown')
    extraversion = profile.get('extraversion', 'unknown')
    agreeableness = profile.get('agreeableness', 'unknown')
    neuroticism = profile.get('neuroticism', 'unknown')

    return f"""
# Discussion Topic
AI brings more benefits or more risks

You are a social network user with the following attributes:
- Age: {age}
- Gender: {gender}
- Education: {education}
- Occupation: {occupation}
- Interests: {', '.join(interests) if interests else 'None specified'}
- Stance: {stance}
- Recent behavior summary: {history}

Note: stance scale from -2 to 2 (-2=Strongly Oppose AI, -1=Oppose AI, 0=Neutral, 1=Support AI, 2=Strongly Support AI)

# Big Five Personality Traits:
- Openness: {openness} (openness to new experiences and ideas)
- Conscientiousness: {conscientiousness} (self-discipline and organization)
- Extraversion: {extraversion} (social energy and assertiveness)
- Agreeableness: {agreeableness} (trust and cooperation)
- Neuroticism: {neuroticism} (emotional stability, higher = less stable)

Recent posts on this server (in chronological order):
{json.dumps(visible_posts_info, ensure_ascii=False, indent=2)}


You can choose one or more of the following actions:
- comment: comment on a post,you should provide specific comment content
- retweet: retweet a post
- like: like a post (note: posts with "already_liked": true have been liked by you, do not like them again)
- follow: follow a user (specify target_user_id)
- unfollow: unfollow a user (specify target_user_id)
- silent: remain silent and do nothing this round

Based on your profile and the posts, decide which actions you will take this round.All your actions and comments must be related to the topic of AI.

# IMPORTANT: 
# - Keep comment content concise (max 30 words)
# - For comment actions, you must provide specific comment content, not generic text
# - If you cannot think of a specific comment, do not choose the comment action

Return your answer in the following JSON format:
{{
  "actions": [
    {{"type": "comment/retweet/like/follow/unfollow/silent", "target_post_id": optional, "target_user_id": optional, "content": optional}}
  ]
}}
"""


def build_adjust_stance_after_interaction_prompt(profile: dict, post: dict, action_type: str, action_content: str) -> str:
    simplified_profile = {
        "name": profile.get("name", ""),
        "age": profile.get("age", 0),
        "gender": profile.get("gender", ""),
        "education": profile.get("education", ""),
        "occupation": profile.get("occupation", ""),
        "interests": profile.get("interests", []),
        "stance": profile.get("stance", 0),
        "openness": profile.get("openness", "moderate"),
        "conscientiousness": profile.get("conscientiousness", "moderate"),
        "extraversion": profile.get("extraversion", "moderate"),
        "agreeableness": profile.get("agreeableness", "moderate"),
        "neuroticism": profile.get("neuroticism", "moderate"),
        "history": profile.get("history", [])[-5:]  
    }
    
    simplified_post = {
        "author": post.get("author", ""),
        "content": post.get("content", ""),
        "stance": post.get("stance", 0),
        "likes": post.get("likes", 0),
        "comments_count": len(post.get("comments", []))
    }
    
    return f"""
You are a social media user. You just performed an action on a post and are considering whether this interaction should change your stance.

# Your profile
{json.dumps(simplified_profile, ensure_ascii=False, indent=2)}

Note: stance scale from -2 to 2 (-2=Strongly Oppose AI, -1=Oppose AI, 0=Neutral, 1=Support AI, 2=Strongly Support AI)

# The post you interacted with
{json.dumps(simplified_post, ensure_ascii=False, indent=2)}

# Your action
Action type: {action_type}
Action content: {action_content}

# Question
Based on the content you have interacted with on social media, do you want to adjust your stance? Consider:
1. Does the content of the post impact or align with your current stance?
2. Did this interaction challenge or reinforce your views, or change your perspective?
3. Do you think your stance should become more extreme, more moderate, or stay the same?

# IMPORTANT: 
# - Provide a brief reason for your new stance (max 30 words)
# - If your stance does not change, explain why it remains the same.
# - Your new stance must be one of the following five values: -2, -1, 0, 1, 2
# - Large stance changes (difference >= 2) should have specific reasons

Return your answer in the following JSON format:
{{
  "reason": "your explanation",
  "new_stance": -2 or -1 or 0 or 1 or 2
}}
"""



def build_reflection_prompt(recent_memories: list) -> str:
    memories_text = "\n".join([
        f"- {m['action_type']} on {m['server']} (stance {m['stance']}): {m['content']}"
        for m in recent_memories
    ])
    
    return f"""You are reflecting on your recent social media behavior. Here are your last actions:

{memories_text}

Based on these observations, what are 1-2 high-level insights about your behavior patterns?

Keep each insight brief (max 40 words). Return them as a JSON array of strings.

Example format:
["insight 1", "insight 2"]
"""
