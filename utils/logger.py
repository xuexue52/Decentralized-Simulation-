import csv
import json
import os
from .config import (
    ACTIONS_LOG_CSV,
    STANCE_CHANGES_CSV,
    SATISFACTION_CSV,
    MIGRATIONS_CSV,
    DRAMATIC_STANCE_CHANGES_CSV,
    MEMORY_COMPRESSION_CSV,
    TOKEN_USAGE_CSV,
)

OUTPUT_DIR = "."

def set_output_directory(output_dir: str):
    global OUTPUT_DIR
    OUTPUT_DIR = output_dir
    os.makedirs(output_dir, exist_ok=True)


def _ensure_csv_with_header(path: str, header: list[str]):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)


def log_action(action_data: dict):
    header = [
        "timestamp",
        "user",
        "action",
        "target_post_id",
        "content",
        "server",
        "reason",
        "round",
        "prompt",
    ]
    log_path = os.path.join(OUTPUT_DIR, ACTIONS_LOG_CSV)
    _ensure_csv_with_header(log_path, header)

    row = [
        action_data.get("timestamp", ""),
        action_data.get("user", ""),
        action_data.get("action", ""),
        (action_data.get("details", {}) or {}).get("target_post_id", action_data.get("target_post_id", "")),
        (action_data.get("details", {}) or {}).get("content", action_data.get("content", "")),
        (action_data.get("details", {}) or {}).get("server", action_data.get("server", "")),
        action_data.get("reason", (action_data.get("details", {}) or {}).get("reason", "")),
        action_data.get("round", ""),
        action_data.get("prompt", ""),
    ]

    with open(log_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def _add_round_separator_to_csv(log_path: str, round_num: int, separator_type: str, num_columns: int):
    if separator_type == "start":
        separator_text = f"========== ROUND {round_num} START =========="
    else:
        separator_text = f"========== ROUND {round_num} END =========="
    
    separator_row = [separator_text] + [""] * (num_columns - 1)
    
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(separator_row)


def _add_action_separator_to_csv(log_path: str, num_columns: int):
    separator_text = "-------------------- ACTION RECORD ---------------------"
    
    separator_row = [separator_text] + [""] * (num_columns - 1)
    
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(separator_row)


def log_round_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, ACTIONS_LOG_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 9)


def log_stance_change_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, STANCE_CHANGES_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 8)


def log_satisfaction_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, SATISFACTION_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 7)


def log_migration_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, MIGRATIONS_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 7)


def log_dramatic_stance_change_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, DRAMATIC_STANCE_CHANGES_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 11)


def log_stance_change(record: dict):
    header = [
        "timestamp",
        "user",
        "old_stance",
        "new_stance",
        "change_type",
        "reason",
        "round",
        "prompt",
    ]
    log_path = os.path.join(OUTPUT_DIR, STANCE_CHANGES_CSV)
    _ensure_csv_with_header(log_path, header)
    
    row = [
        record.get("timestamp", ""),
        record.get("user", ""),
        record.get("old_stance", ""),
        record.get("new_stance", ""),
        record.get("change_type", ""),
        record.get("reason", ""),
        record.get("round", ""),
        record.get("prompt", ""),
    ]
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)


def log_satisfaction(record: dict):
    header = [
        "timestamp",
        "user",
        "server",
        "score",
        "reason",
        "round",
        "prompt",
    ]
    log_path = os.path.join(OUTPUT_DIR, SATISFACTION_CSV)
    _ensure_csv_with_header(log_path, header)
    
    row = [
        record.get("timestamp", ""),
        record.get("user", ""),
        record.get("server", ""),
        record.get("score", ""),
        record.get("reason", ""),
        record.get("round", ""),
        record.get("prompt", ""),
    ]
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)


def log_migration(record: dict):
    header = [
        "timestamp",
        "user",
        "from_server",
        "to_server",
        "reason",
        "round",
        "prompt",
    ]
    log_path = os.path.join(OUTPUT_DIR, MIGRATIONS_CSV)
    _ensure_csv_with_header(log_path, header)
    
    row = [
        record.get("timestamp", ""),
        record.get("user", ""),
        record.get("from_server", ""),
        record.get("to_server", ""),
        record.get("reason", ""),
        record.get("round", ""),
        record.get("prompt", ""),
    ]
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)


def log_dramatic_stance_change(record: dict):
    log_path = os.path.join(OUTPUT_DIR, DRAMATIC_STANCE_CHANGES_CSV)
    
    header = [
        "timestamp",
        "user",
        "old_stance",
        "new_stance", 
        "change_magnitude",
        "change_type",
        "reason",
        "round",
        "prompt",
        "user_profile",
        "current_server"
    ]
    _ensure_csv_with_header(log_path, header)
    
    row = [
        record.get("timestamp", ""),
        record.get("user", ""),
        record.get("old_stance", ""),
        record.get("new_stance", ""),
        record.get("change_magnitude", ""),
        record.get("change_type", ""),
        record.get("reason", ""),
        record.get("round", ""),
        record.get("prompt", ""),
        record.get("user_profile", ""),
        record.get("current_server", ""),
    ]
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)


def load_profiles(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def log_memory_compression(record: dict):
    header = [
        "timestamp",
        "user",
        "round",
        "event_type",
        "total_memories",
        "memories_used",
        "current_reflections",
        "importance_score",
        "prompt",
        "generated_reflections",
        "new_reflection_count",
        "final_reflection_count",
    ]
    log_path = os.path.join(OUTPUT_DIR, MEMORY_COMPRESSION_CSV)
    _ensure_csv_with_header(log_path, header)
    
    row = [
        record.get("timestamp", ""),
        record.get("user", ""),
        record.get("round", ""),
        record.get("event_type", ""),
        record.get("total_memories", ""),
        record.get("memories_used", ""),
        record.get("current_reflections", ""),
        record.get("importance_score", ""),
        record.get("prompt", ""),
        record.get("generated_reflections", ""),
        record.get("new_reflection_count", ""),
        record.get("final_reflection_count", ""),
    ]
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)


def log_memory_compression_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, MEMORY_COMPRESSION_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 12)


def log_token_usage(record: dict):
    log_path = os.path.join(OUTPUT_DIR, TOKEN_USAGE_CSV)
    
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "round",
                "user_id",
                "action_type",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "model",
            ])
    
    row = [
        record.get("timestamp", ""),
        record.get("round", ""),
        record.get("user_id", ""),
        record.get("action_type", ""),
        record.get("prompt_tokens", 0),
        record.get("completion_tokens", 0),
        record.get("total_tokens", 0),
        record.get("model", ""),
    ]
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)


def log_token_usage_separator(round_num: int, separator_type: str = "start"):
    log_path = os.path.join(OUTPUT_DIR, TOKEN_USAGE_CSV)
    _add_round_separator_to_csv(log_path, round_num, separator_type, 8)
