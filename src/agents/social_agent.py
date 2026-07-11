import json
import time
import random
import requests
import re
from datetime import datetime
from utils.config import (
    API_KEY, API_BASE_URL, 
    MAX_MEMORY_ITEMS, MAX_REFLECTION_MEMORIES,
    MAX_RELEVANT_MEMORIES, MAX_POST_CONTENT_LENGTH,
    MAX_STANCE_HISTORY, MAX_TOKEN_COUNT, MAX_DISPLAY_TOKEN_COUNT,
    MAX_FOLLOWING_POSTS, MAX_SERVER_POSTS,
    RETRY_BASE_DELAY, RETRY_BACKOFF_FACTOR, RETRY_MAX_DELAY,
    RETRY_JITTER_LOW, RETRY_JITTER_HIGH,
    RETRYABLE_STATUS_CODES, RETRYABLE_ERROR_SUBSTRINGS
)
from utils.logger import log_action, log_stance_change, log_migration, log_satisfaction, log_dramatic_stance_change, log_memory_compression
from utils.prompts import (
    build_create_post_prompt,
    build_environment_evaluation_prompt,
    build_decision_prompt,
    build_adjust_stance_after_interaction_prompt,
    build_reflection_prompt
)

class SocialAgent:
    AVAILABLE_SERVERS = ['A', 'B', 'C']
    def __init__(self, profile, user_id, network, initial_server):
        self.profile = profile
        self.user_id = f"user_{user_id}"
        self.network = network
        self.network.add_user(self.user_id)
        self.network.user_servers[self.user_id] = initial_server
        
        self.behavior_memory = []
        self.reflections = []
        self.total_importance_since_last_reflection = 0
        self.current_round = 0
    
    def get_current_server(self):
        return self.network.user_servers[self.user_id]
    
    def add_behavior_memory(self, action_type, content, server, stance, outcome=""):
        full_observation = f"{action_type} on {server}: {content}"
        if outcome:
            full_observation += f" (Outcome: {outcome})"
        
        importance = self._calculate_importance(full_observation, action_type)
        
        memory = {
            'action_type': action_type,
            'content': content,
            'server': server,
            'stance': stance,
            'outcome': outcome,
            'importance': importance,
            'timestamp': time.time()
        }
        self.behavior_memory.append(memory)
        
        self.total_importance_since_last_reflection += importance
        
        if len(self.behavior_memory) > MAX_MEMORY_ITEMS:
            self.behavior_memory = self.behavior_memory[-MAX_MEMORY_ITEMS:]
        
        if self.total_importance_since_last_reflection >= 50:
            self._generate_reflection()
            self.total_importance_since_last_reflection = 0
        
        self._update_profile_with_reflection()
    
    def _calculate_importance(self, observation, action_type):
        importance_map = {
            'migrate': 9,
            'follow': 6,
            'unfollow': 6,
            'create_post': 7,
            'comment': 6,
            'retweet': 5,
            'like': 4,
            'silent': 2,
        }
        
        base_importance = importance_map.get(action_type, 5)
        
        if any(keyword in observation.lower() for keyword in ['hate', 'love', 'strongly', 'never', 'always']):
            base_importance = min(10, base_importance + 2)
        
        return base_importance
    
    def _generate_reflection(self):
        if len(self.behavior_memory) < 5:
            return
        
        recent_memories = self.behavior_memory[-MAX_REFLECTION_MEMORIES:]
        
        prompt = build_reflection_prompt(recent_memories)
        
        log_memory_compression({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": self.user_id,
            "round": getattr(self, 'current_round', ''),
            "event_type": "reflection_triggered",
            "total_memories": len(self.behavior_memory),
            "memories_used": len(recent_memories),
            "current_reflections": len(self.reflections),
            "importance_score": self.total_importance_since_last_reflection,
            "prompt": prompt.replace('\n', ' | '),
            "generated_reflections": "",
            "new_reflection_count": "",
            "final_reflection_count": "",
        })
        
        try:
            response = self._query_openai(prompt, expect_json_array=True, action_type="reflection")
            if response and isinstance(response, list):
                new_reflections_count = 0
                for insight in response[:2]:
                    reflection = {
                        'content': insight,
                        'timestamp': time.time(),
                        'importance': 8,
                        'type': 'reflection'
                    }
                    self.reflections.append(reflection)
                    new_reflections_count += 1
                
                old_reflection_count = len(self.reflections)
                if len(self.reflections) > 3:
                    self.reflections = self.reflections[-3:]
                
                log_memory_compression({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user": self.user_id,
                    "round": getattr(self, 'current_round', ''),
                    "event_type": "reflection_generated",
                    "total_memories": len(self.behavior_memory),
                    "memories_used": len(recent_memories),
                    "current_reflections": old_reflection_count,
                    "importance_score": self.total_importance_since_last_reflection,
                    "prompt": "",
                    "generated_reflections": " | ".join(response[:2]),
                    "new_reflection_count": new_reflections_count,
                    "final_reflection_count": len(self.reflections),
                })
                
                print(f"💭 {self.user_id} generated reflections: {response}")
        except Exception as e:
            log_memory_compression({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": self.user_id,
                "round": getattr(self, 'current_round', ''),
                "event_type": "reflection_failed",
                "total_memories": len(self.behavior_memory),
                "memories_used": len(recent_memories),
                "current_reflections": len(self.reflections),
                "importance_score": self.total_importance_since_last_reflection,
                "prompt": "",
                "generated_reflections": f"ERROR: {str(e)}",
                "new_reflection_count": 0,
                "final_reflection_count": len(self.reflections),
            })
            print(f"⚠️ Reflection generation failed: {e}")
    
    def _update_profile_with_reflection(self):
        if not self.reflections:
            self.profile['history'] = []
            return
        
        self.profile['history'] = [reflection['content'] for reflection in self.reflections]
    
    def get_relevant_memories(self, context_type="interaction", max_memories=MAX_RELEVANT_MEMORIES):
        if not self.behavior_memory:
            return []
        
        recent_memories = []
        for memory in reversed(self.behavior_memory):
            recent_memories.append(memory)
            
            if len(recent_memories) >= 10:
                break
        
        relevant_memories = []
        for memory in recent_memories:
            if context_type == "interaction":
                if memory['action_type'] in ['comment', 'like', 'retweet', 'create_post', 'follow', 'unfollow']:
                    relevant_memories.append(memory)
            elif context_type == "migration":
                if memory['action_type'] in ['create_post', 'migrate']:
                    relevant_memories.append(memory)
            else:
                relevant_memories.append(memory)
            
            if len(relevant_memories) >= max_memories:
                break
        
        return relevant_memories
    
    def create_post(self):
        current_server = self.get_current_server()
        print(f"\n{self.user_id} preparing to post on server {current_server}")
        
        prompt = build_create_post_prompt(self.profile)

        response = self._query_openai(prompt, action_type="post_creation")
        
        if response and "content" in response:
            post_content = response["content"]
            self.network.add_post({
                "author": self.user_id,
                "content": post_content,
                "likes": 0,
                "comments": [],
                "stance": self.profile.get('stance', 0),
                "timestamp": datetime.now().isoformat()
            }, current_server)
            print(f"📝 {self.user_id} posted on server {current_server}: {post_content[:30]}...")
            
            log_action({
                "timestamp": datetime.now().isoformat(),
                "user": self.user_id,
                "action": "create_post",
                "details": {
                    "content": post_content,
                    "server": current_server
                },
                "round": getattr(self, 'current_round', ''),
                "prompt": prompt,
            })
            
            self.add_behavior_memory(
                action_type="create_post",
                content=post_content,
                server=current_server,
                stance=self.profile.get('stance', 0),
                outcome="posted"
            )

    def evaluate_environment(self):
        current_server = self.get_current_server()
        visible_posts = self.network.get_mixed_posts_for_user(self.user_id, current_server, 
                                                               max_following_posts=MAX_FOLLOWING_POSTS, 
                                                               max_server_posts=MAX_SERVER_POSTS)
        
        MAX_RELEVANT_MEMORIES = 5
        relevant_memories = self.get_relevant_memories("interaction", MAX_RELEVANT_MEMORIES)

        prompt = build_environment_evaluation_prompt(self.user_id, self.profile, current_server, visible_posts, relevant_memories)

        result = self._query_openai(prompt, action_type="environment_evaluation")
        if not isinstance(result, dict):
            result = {}

        score = result.get("score", 0)
        reason = result.get("reason", "")

        return {"score": score, "reason": reason, "prompt": prompt}

    def migrate_if_unsatisfied(self):
        evaluation = self.evaluate_environment()
        if evaluation.get("score", 0) < 6:
            self._migrate_with_logging(evaluation)
            return True
        return False

    def _migrate_with_logging(self, evaluation):
        old_server = self.get_current_server()
        candidates = [s for s in self.AVAILABLE_SERVERS if s != old_server]
        if not candidates:
            return
        new_server = random.choice(candidates)
        self.network.change_user_server(self.user_id, new_server)
        migration_record = f"User {self.user_id} migrated from server {old_server} to server {new_server} (score={evaluation.get('score', '')})"
        self.network.migration_reasons.append(migration_record)
        print(f"⚠️ {migration_record}")
        
        self.add_behavior_memory(
            action_type="migrate",
            content=f"Migrated from server {old_server} to server {new_server}",
            server=new_server,
            stance=self.profile.get('stance', 0),
            outcome=f"migrated due to dissatisfaction: {evaluation.get('reason', '')}"
        )
        try:
            log_migration({
                'timestamp': datetime.now().isoformat(),
                'user': self.user_id,
                'from_server': old_server,
                'to_server': new_server,
                'reason': evaluation.get('reason', ''),
                'round': getattr(self, 'current_round', ''),
                'prompt': evaluation.get('prompt', ''),
            })
        except Exception as e:
            print(f"Failed to record migration CSV: {e}")

    def generate_decision_prompt(self, visible_posts, round_num=1, has_posted_this_round=False):
        recent_posts = visible_posts
        
        user_liked_posts = self.network.user_likes.get(self.user_id, set())
        
        posts_info = []
        for post in recent_posts:
            info = {
                'post_id': post.get('post_id'),
                'author': post.get('author'),
                'content': post.get('content', '')[:MAX_POST_CONTENT_LENGTH],
                'stance': post.get('stance', 'unknown'),
                'likes': post.get('likes', 0),
                'comments': len(post.get('comments', [])),
                'already_liked': str(post.get('post_id')) in user_liked_posts
            }
            posts_info.append(info)

        relevant_memories = self.get_relevant_memories("interaction", MAX_RELEVANT_MEMORIES)
        
        following_users = self.network.get_following(self.user_id)
        following_info = f"\n\nCurrently following users: {list(following_users) if following_users else 'none'}"
        
        prompt = build_decision_prompt(self.profile, posts_info, round_num, has_posted_this_round)
        prompt += following_info
        
        if relevant_memories:
            memory_text = "\n\nPast experience (recent interactions):\n"
            for i, memory in enumerate(relevant_memories, 1):
                memory_text += f"{i}. {memory['action_type']}@{memory['server']}(stance {memory['stance']}) "
                memory_text += f"'{memory['content']}'\n"
                if memory.get('outcome'):
                    memory_text += f"   Outcome: {memory['outcome']}\n"
            
            memory_text += "\nPlease refer to these experiences to make decisions."
            prompt += memory_text
        
        return prompt

    def estimate_token_count(self, text):
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        return chinese_chars + int(english_words * 0.75)

    def adjust_stance_after_interaction(self, post, action_type, action_content):
        old_stance = self.profile.get('stance', 0)
        
        prompt = build_adjust_stance_after_interaction_prompt(self.profile, post, action_type, action_content)
        
        print(f"  📝 Stance Adjustment Prompt: {prompt[:500]}...")
        
        response = self._query_openai(prompt, action_type="stance_adjustment")
        if response and "new_stance" in response:
            try:
                new_stance = int(response["new_stance"])
                if new_stance in [-2, -1, 0, 1, 2]:
                    if not self._validate_stance_change(old_stance, new_stance, response.get('reason', '')):
                        print(f"  ⚠️ Unreasonable stance change, keeping original stance: {old_stance}")
                        return
                    
                    if old_stance != new_stance:
                        self.record_stance_change(old_stance, new_stance, f"Interaction impact ({action_type})", response.get('reason', ''), prompt)
                        self.profile['stance'] = new_stance
                        print(f"  📊 stance: {old_stance} → {new_stance}")
                    else:
                        self.profile['stance'] = new_stance
                else:
                    print(f"{self.user_id} LLM returned invalid stance: {response['new_stance']}")
            except Exception as e:
                print(f"{self.user_id} LLM stance parsing failed: {response.get('new_stance')}, error: {e}")

    def _validate_stance_change(self, old_stance, new_stance, reason):
        change_magnitude = abs(new_stance - old_stance)
        
        if change_magnitude >= 2:
            if not reason or len(reason.strip()) < 10:
                print(f"  ⚠️ Large stance change ({old_stance}→{new_stance}) lacks reasonable justification")
                return False
        
        if (old_stance in [-2, 2] and new_stance in [-2, 2] and old_stance != new_stance):
            if not reason or len(reason.strip()) < 20:
                print(f"  ⚠️ Extreme stance change ({old_stance}→{new_stance}) requires stronger justification")
                return False
        
        return True


    def record_stance_change(self, old_stance, new_stance, change_type, reason, prompt=""):
        if old_stance == new_stance:
            return
        
        if 'stance_history' not in self.profile:
            self.profile['stance_history'] = []
        
        stance_change = {
            'old_stance': old_stance,
            'new_stance': new_stance,
            'change_type': change_type
        }
        
        self.profile['stance_history'].append(stance_change)
        
        stance_difference = abs(new_stance - old_stance)
        is_dramatic_change = stance_difference >= 2
        
        try:
            log_stance_change({
                'timestamp': datetime.now().isoformat(),
                'user': self.user_id,
                'old_stance': old_stance,
                'new_stance': new_stance,
                'change_type': change_type,
                'reason': reason,
                'round': getattr(self, 'current_round', ''),
                'prompt': prompt,
            })
        except Exception as e:
            print(f"Failed to record stance change CSV: {e}")
        
        if is_dramatic_change:
            try:
                log_dramatic_stance_change({
                    'timestamp': datetime.now().isoformat(),
                    'user': self.user_id,
                    'old_stance': old_stance,
                    'new_stance': new_stance,
                    'change_magnitude': stance_difference,
                    'change_type': change_type,
                    'reason': reason,
                    'round': getattr(self, 'current_round', ''),
                    'prompt': prompt,
                    'user_profile': self.profile.get('personality', ''),
                    'current_server': self.get_current_server()
                })
                print(f"🚨 Dramatic stance change: {self.user_id} {old_stance}→{new_stance} (magnitude:{stance_difference})")
            except Exception as e:
                print(f"Failed to record dramatic stance change: {e}")
        
        if len(self.profile['stance_history']) > MAX_STANCE_HISTORY:
            self.profile['stance_history'] = self.profile['stance_history'][-MAX_STANCE_HISTORY:]

    def interact_with_posts(self, round_num=1, has_posted_this_round=False):
        current_server = self.get_current_server()
        visible_posts = self.network.get_mixed_posts_for_user(
            self.user_id, 
            current_server, 
            max_following_posts=MAX_FOLLOWING_POSTS,
            max_server_posts=MAX_SERVER_POSTS
        )
        
        following_set = self.network.user_following.get(self.user_id, set())
        following_count = sum(1 for p in visible_posts if p.get('author') in following_set)
        server_count = len(visible_posts) - following_count
        
        print(f"\n{self.user_id} (server {current_server}) starting interaction... (total {len(visible_posts)} posts: {following_count} following posts, {server_count} server posts)")
        
        decision_prompt = self.generate_decision_prompt(visible_posts, round_num, has_posted_this_round)
        
        estimated_tokens = self.estimate_token_count(decision_prompt)
        if estimated_tokens > MAX_DISPLAY_TOKEN_COUNT:
            print(f"\n{'='*60}")
            print(f"🤖 {self.user_id} Decision Prompt (truncated, {estimated_tokens} tokens):")
            print(f"{'='*60}")
            print(decision_prompt[:1000] + "...\n[Content too long, truncated]")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print(f"🤖 {self.user_id} Decision Prompt:")
            print(f"{'='*60}")
            print(decision_prompt)
            print(f"{'='*60}\n")
        
        response = self._query_openai(decision_prompt, action_type="interaction_decision")

        user_liked_posts = self.network.user_likes.get(self.user_id, set())

        if response and "actions" in response:
            for action in response["actions"]:
                action_type = action["type"]
                target_post_id = action.get("target_post_id")
                content = action.get("content")
                print(f"  → {action_type}: {content[:20] if content else 'No content'}...")
                if action_type == "comment" and target_post_id is not None:
                    if not content or content.strip() == "":
                        print(f"  ⚠ Comment content is empty, skipping comment action")
                        continue
                    
                    self.network.add_interaction(self.user_id, target_post_id, "create_comment", content)
                    post = next((p for p in visible_posts if p.get('post_id') == target_post_id), None)
                    if post is not None:
                        self.add_behavior_memory(
                            action_type="comment",
                            content=content,
                            server=current_server,
                            stance=self.profile.get('stance', 0),
                            outcome=f"commented on post by {post['author']}"
                        )
                        self.adjust_stance_after_interaction(post, "comment", content)
                elif action_type == "retweet" and target_post_id is not None:
                    post = next((p for p in visible_posts if p.get('post_id') == target_post_id), None)
                    if post is not None:
                        retweet_content = f"[Retweet] {post['content']}"
                        self.network.add_post({
                            "author": self.user_id,
                            "content": retweet_content,
                            "likes": 0,
                            "comments": [],
                            "stance": post.get('stance', self.profile.get('stance', 0)),
                            "timestamp": datetime.now().isoformat()
                        }, current_server)
                        self.network.add_interaction(self.user_id, target_post_id, "retweet")
                        self.add_behavior_memory(
                            action_type="retweet",
                            content=retweet_content,
                            server=current_server,
                            stance=self.profile.get('stance', 0),
                            outcome=f"retweeted post by {post['author']}"
                        )
                        self.adjust_stance_after_interaction(post, "retweet", retweet_content)
                elif action_type == "like" and target_post_id is not None:
                    if str(target_post_id) not in user_liked_posts:
                        self.network.add_interaction(self.user_id, target_post_id, "like_post")
                        print(f"  ✓ Liked post {target_post_id}")
                        post = next((p for p in visible_posts if p.get('post_id') == target_post_id), None)
                        if post is not None:
                            self.add_behavior_memory(
                                action_type="like",
                                content=f"Liked {post['author']}'s post",
                                server=current_server,
                                stance=self.profile.get('stance', 0),
                                outcome=f"liked post by {post['author']}"
                            )
                            self.adjust_stance_after_interaction(post, "like", "Liked post")
                    else:
                        print(f"  ⚠ Already liked post {target_post_id}")
                elif action_type == "follow":
                    target_user_id = action.get("target_user_id")
                    if target_user_id and target_user_id != self.user_id:
                        if self.network.follow_user(self.user_id, target_user_id):
                            print(f"  👥 Followed {target_user_id}")
                            self.add_behavior_memory(
                                action_type="follow",
                                content=f"Followed {target_user_id}",
                                server=current_server,
                                stance=self.profile.get('stance', 0),
                                outcome=f"followed {target_user_id}"
                            )
                        else:
                            print(f"  ⚠ Already following {target_user_id}")
                    else:
                        print(f"  ⚠ Invalid follow target: {target_user_id}")
                elif action_type == "unfollow":
                    target_user_id = action.get("target_user_id")
                    if target_user_id and target_user_id != self.user_id:
                        if self.network.unfollow_user(self.user_id, target_user_id):
                            print(f"  👥 Unfollowed {target_user_id}")
                            self.add_behavior_memory(
                                action_type="unfollow",
                                content=f"Unfollowed {target_user_id}",
                                server=current_server,
                                stance=self.profile.get('stance', 0),
                                outcome=f"unfollowed {target_user_id}"
                            )
                        else:
                            print(f"  ⚠ Not following {target_user_id}")
                    else:
                        print(f"  ⚠ Invalid unfollow target: {target_user_id}")
                elif action_type == "silent":
                    print(f"  😶 Chose to remain silent")
                    self.add_behavior_memory(
                        action_type="silent",
                        content="Chose to remain silent",
                        server=current_server,
                        stance=self.profile.get('stance', 0),
                        outcome="remained silent"
                    )
                log_action({
                    "timestamp": datetime.now().isoformat(),
                    "user": self.user_id,
                    "action": action_type,
                    "details": action,
                    "round": getattr(self, 'current_round', ''),
                    "prompt": decision_prompt,
                })
        else:
            print("  ⚠ LLM did not return valid actions, defaulting to silent")

        evaluation = self.evaluate_environment()
        
        evaluation_with_round = evaluation.copy()
        evaluation_with_round['round'] = getattr(self, 'current_round', '')
        evaluation_with_round['prompt'] = evaluation.get('prompt', '')
        self.network.record_satisfaction(self.user_id, current_server, evaluation_with_round)

        if evaluation.get("score", 0) < 6:
            self._migrate_with_logging(evaluation)
        else:
            print(f"  ✅ Environment satisfied (score={evaluation.get('score', '')})")


    def _query_openai(self, prompt, max_retries=5, timeout=60, expect_json_array=False, action_type="unknown"):
        print(f"\n{'='*80}")
        print(f"🤖 API call started - {self.user_id}")
        print(f"{'='*80}")
        
        estimated_tokens = self.estimate_token_count(prompt)
        if estimated_tokens > MAX_TOKEN_COUNT:
            print(f"⚠️ Prompt too long ({estimated_tokens} tokens), truncating...")
            target_tokens = 50000
            max_chars = int(len(prompt) * target_tokens / estimated_tokens)
            prompt = prompt[:max_chars] + "\n\n[Content truncated to save tokens]"
            
            final_tokens = self.estimate_token_count(prompt)
            while final_tokens > 60000:
                max_chars = int(max_chars * 0.8)
                prompt = prompt[:max_chars] + "\n\n[Content truncated to save tokens]"
                final_tokens = self.estimate_token_count(prompt)
            
            print(f"✅ Truncated to {final_tokens} tokens")
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/chat/completions", 
                    headers=headers, 
                    json=data,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    content = response_data["choices"][0]["message"]["content"].strip()
                    
                    if "usage" in response_data:
                        from utils.logger import log_token_usage
                        from datetime import datetime
                        
                        usage = response_data["usage"]
                        log_token_usage({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "round": getattr(self, 'current_round', 0),
                            "user_id": self.user_id,
                            "action_type": action_type,
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                            "model": data.get("model", "unknown"),
                        })
                    
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0].strip()
                    else:
                        json_str = content.strip()
                    
                    try:
                        result = json.loads(json_str)
                        print(f"✅ API call successful - {self.user_id}")
                        print(f"{'='*80}\n")
                        return result
                    except json.JSONDecodeError:
                        print(f"❌ JSON parsing failed, original content: {json_str[:200]}...")
                        if attempt < max_retries - 1:
                            print(f"⏳ Waiting before retry...")
                            delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** attempt))
                            delay *= random.uniform(RETRY_JITTER_LOW, RETRY_JITTER_HIGH)
                            time.sleep(delay)
                            continue
                        else:
                            print(f"⚠️ All retries failed, returning original content as reason")
                            return {"reason": json_str[:100], "error": "JSON parse failed"}
                else:
                    print(f"❌ API error: {response.text}")
                    is_retryable = (response.status_code in RETRYABLE_STATUS_CODES) or any(
                        err_substr.lower() in response.text.lower() for err_substr in RETRYABLE_ERROR_SUBSTRINGS
                    )
                    if attempt < max_retries - 1 and is_retryable:
                        print(f"⏳ Retryable error, waiting before retry...")
                        delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** attempt))
                        delay *= random.uniform(RETRY_JITTER_LOW, RETRY_JITTER_HIGH)
                        time.sleep(delay)
                        continue
                    else:
                        return {"reason": response.text[:200], "status": response.status_code, "error": "HTTP error"}
                    
            except requests.exceptions.Timeout:
                print(f"⏰ API call timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print("⏳ Waiting before retry...")
                    delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** attempt))
                    delay *= random.uniform(RETRY_JITTER_LOW, RETRY_JITTER_HIGH)
                    time.sleep(delay)
                    continue
                
            except requests.exceptions.ConnectionError:
                print(f"🔌 Connection error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print("⏳ Waiting before retry...")
                    delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** attempt))
                    delay *= random.uniform(RETRY_JITTER_LOW, RETRY_JITTER_HIGH)
                    time.sleep(delay)
                    continue
                
            except Exception as e:
                print(f"💥 API call error: {e}")
                if attempt < max_retries - 1:
                    print("⏳ Waiting before retry...")
                    delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** attempt))
                    delay *= random.uniform(RETRY_JITTER_LOW, RETRY_JITTER_HIGH)
                    time.sleep(delay)
                    continue
        
        print(f"❌ API call completely failed - {self.user_id}")
        print(f"{'='*80}\n")
        return {"reason": "API call failed after all retries", "error": "API failure"} 

    