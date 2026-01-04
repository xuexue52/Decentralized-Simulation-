#!/usr/bin/env python3

import csv
import os
from collections import defaultdict
from datetime import datetime


def analyze_token_usage(log_file):
    if not os.path.exists(log_file):
        print(f"❌ Token usage log file not found: {log_file}")
        return
    
    print(f"\n{'='*80}")
    print(f"Token Usage Analysis")
    print(f"Log file: {log_file}")
    print(f"{'='*80}\n")
    
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    action_type_stats = defaultdict(lambda: {
        'count': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0
    })
    round_stats = defaultdict(lambda: {
        'count': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0
    })
    user_stats = defaultdict(lambda: {
        'count': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0
    })
    model_stats = defaultdict(lambda: {
        'count': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0
    })
    
    records = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('timestamp', '').startswith('---'):
                continue
            
            try:
                prompt_tokens = int(row.get('prompt_tokens', 0))
                completion_tokens = int(row.get('completion_tokens', 0))
                total = int(row.get('total_tokens', 0))
                
                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens
                total_tokens += total
                
                action_type = row.get('action_type', 'unknown')
                action_type_stats[action_type]['count'] += 1
                action_type_stats[action_type]['prompt_tokens'] += prompt_tokens
                action_type_stats[action_type]['completion_tokens'] += completion_tokens
                action_type_stats[action_type]['total_tokens'] += total
                
                round_num = row.get('round', 'unknown')
                round_stats[round_num]['count'] += 1
                round_stats[round_num]['prompt_tokens'] += prompt_tokens
                round_stats[round_num]['completion_tokens'] += completion_tokens
                round_stats[round_num]['total_tokens'] += total
                
                user_id = row.get('user_id', 'unknown')
                user_stats[user_id]['count'] += 1
                user_stats[user_id]['prompt_tokens'] += prompt_tokens
                user_stats[user_id]['completion_tokens'] += completion_tokens
                user_stats[user_id]['total_tokens'] += total
                
                model = row.get('model', 'unknown')
                model_stats[model]['count'] += 1
                model_stats[model]['prompt_tokens'] += prompt_tokens
                model_stats[model]['completion_tokens'] += completion_tokens
                model_stats[model]['total_tokens'] += total
                
                records.append(row)
                
            except (ValueError, KeyError) as e:
                continue
    
    print(f"📊 Overall Statistics")
    print(f"{'='*80}")
    print(f"Total API Calls: {len(records)}")
    print(f"Total Prompt Tokens: {total_prompt_tokens:,}")
    print(f"Total Completion Tokens: {total_completion_tokens:,}")
    print(f"Total Tokens: {total_tokens:,}")
    print()
    
    print(f"📝 By Action Type")
    print(f"{'='*80}")
    print(f"{'Action Type':<25} {'Calls':<10} {'Prompt':<15} {'Completion':<15} {'Total':<15}")
    print(f"{'-'*80}")
    for action_type in sorted(action_type_stats.keys()):
        stats = action_type_stats[action_type]
        print(f"{action_type:<25} {stats['count']:<10} {stats['prompt_tokens']:<15,} {stats['completion_tokens']:<15,} {stats['total_tokens']:<15,}")
    print()
    
    print(f"🔄 By Round")
    print(f"{'='*80}")
    print(f"{'Round':<10} {'Calls':<10} {'Prompt':<15} {'Completion':<15} {'Total':<15}")
    print(f"{'-'*80}")
    
    sorted_rounds = sorted(
        [(k, v) for k, v in round_stats.items() if k != 'unknown'],
        key=lambda x: int(x[0]) if x[0].isdigit() else float('inf')
    )
    
    for round_num, stats in sorted_rounds:
        print(f"{round_num:<10} {stats['count']:<10} {stats['prompt_tokens']:<15,} {stats['completion_tokens']:<15,} {stats['total_tokens']:<15,}")
    
    if 'unknown' in round_stats:
        stats = round_stats['unknown']
        print(f"{'unknown':<10} {stats['count']:<10} {stats['prompt_tokens']:<15,} {stats['completion_tokens']:<15,} {stats['total_tokens']:<15,}")
    print()
    
    print(f"🤖 By Model")
    print(f"{'='*80}")
    print(f"{'Model':<25} {'Calls':<10} {'Prompt':<15} {'Completion':<15} {'Total':<15}")
    print(f"{'-'*80}")
    for model in sorted(model_stats.keys()):
        stats = model_stats[model]
        print(f"{model:<25} {stats['count']:<10} {stats['prompt_tokens']:<15,} {stats['completion_tokens']:<15,} {stats['total_tokens']:<15,}")
    print()
    
    print(f"👥 Top 10 Users by Token Usage")
    print(f"{'='*80}")
    print(f"{'User ID':<25} {'Calls':<10} {'Prompt':<15} {'Completion':<15} {'Total':<15}")
    print(f"{'-'*80}")
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['total_tokens'], reverse=True)[:10]
    for user_id, stats in sorted_users:
        print(f"{user_id:<25} {stats['count']:<10} {stats['prompt_tokens']:<15,} {stats['completion_tokens']:<15,} {stats['total_tokens']:<15,}")
    print()
    
    input_cost = (total_prompt_tokens / 1_000_000) * 0.15
    output_cost = (total_completion_tokens / 1_000_000) * 0.60
    total_cost = input_cost + output_cost
    
    print(f"💰 Cost Estimation (gpt-4o-mini)")
    print(f"{'='*80}")
    print(f"Input Cost:  ${input_cost:.4f} ({total_prompt_tokens:,} tokens @ $0.15/1M)")
    print(f"Output Cost: ${output_cost:.4f} ({total_completion_tokens:,} tokens @ $0.60/1M)")
    print(f"Total Cost:  ${total_cost:.4f}")
    print()


def main():
    import sys
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = "../../output/example/logs_token_usage.csv"
        if not os.path.exists(log_file):
            log_file = "output/example/logs_token_usage.csv"
    
    analyze_token_usage(log_file)


if __name__ == "__main__":
    main()
