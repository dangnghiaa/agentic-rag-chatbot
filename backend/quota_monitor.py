"""
QUOTA MONITOR - Theo dõi usage của Groq API
Chạy file này để xem thống kê chi tiết
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

# =====================================================
# CONFIG
# =====================================================
CACHE_FILE = "answer_cache.json"
QUOTA_LOG_FILE = "quota_usage.json"

# Groq Free Tier Limits
GROQ_LIMITS = {
    "llama-3.3-70b-versatile": {
        "rpm": 30,  # requests per minute
        "rpd": 14400,  # requests per day (ước tính)
        "tpm": 20000  # tokens per minute
    },
    "llama-3.1-8b-instant": {
        "rpm": 30,
        "rpd": 30000,  # cao hơn
        "tpm": 40000
    }
}


# =====================================================
# LOAD DATA
# =====================================================
def load_quota_log():
    """Load usage log"""
    if os.path.exists(QUOTA_LOG_FILE):
        try:
            with open(QUOTA_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"daily_usage": {}, "hourly_usage": {}}


def load_cache():
    """Load answer cache"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_quota_log(log):
    """Save usage log"""
    try:
        with open(QUOTA_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
    except:
        pass


# =====================================================
# TRACKING FUNCTIONS
# =====================================================
def log_api_call(model, tokens=100):
    """Ghi lại mỗi lần gọi API"""
    log = load_quota_log()

    today = datetime.now().strftime("%Y-%m-%d")
    hour = datetime.now().strftime("%Y-%m-%d %H:00")

    # Daily tracking
    if today not in log["daily_usage"]:
        log["daily_usage"][today] = {
            "llama-3.3-70b": 0,
            "llama-3.1-8b": 0,
            "total_tokens": 0
        }

    # Hourly tracking
    if hour not in log["hourly_usage"]:
        log["hourly_usage"][hour] = {
            "llama-3.3-70b": 0,
            "llama-3.1-8b": 0,
            "total_tokens": 0
        }

    # Increment
    model_key = "llama-3.3-70b" if "70b" in model else "llama-3.1-8b"
    log["daily_usage"][today][model_key] += 1
    log["daily_usage"][today]["total_tokens"] += tokens
    log["hourly_usage"][hour][model_key] += 1
    log["hourly_usage"][hour]["total_tokens"] += tokens

    save_quota_log(log)


def get_current_usage():
    """Lấy usage hiện tại"""
    log = load_quota_log()
    today = datetime.now().strftime("%Y-%m-%d")

    if today in log["daily_usage"]:
        return log["daily_usage"][today]
    return {"llama-3.3-70b": 0, "llama-3.1-8b": 0, "total_tokens": 0}


def estimate_remaining_quota():
    """Ước tính quota còn lại"""
    usage = get_current_usage()

    # Ước tính cho 70b model (quan trọng nhất)
    used_70b = usage.get("llama-3.3-70b", 0)
    used_8b = usage.get("llama-3.1-8b", 0)

    remaining_70b = GROQ_LIMITS["llama-3.3-70b-versatile"]["rpd"] - used_70b
    remaining_8b = GROQ_LIMITS["llama-3.1-8b-instant"]["rpd"] - used_8b

    return {
        "70b": {
            "used": used_70b,
            "limit": GROQ_LIMITS["llama-3.3-70b-versatile"]["rpd"],
            "remaining": remaining_70b,
            "percentage": (used_70b / GROQ_LIMITS["llama-3.3-70b-versatile"]["rpd"]) * 100
        },
        "8b": {
            "used": used_8b,
            "limit": GROQ_LIMITS["llama-3.1-8b-instant"]["rpd"],
            "remaining": remaining_8b,
            "percentage": (used_8b / GROQ_LIMITS["llama-3.1-8b-instant"]["rpd"]) * 100
        }
    }


def estimate_questions_remaining():
    """Ước tính số câu hỏi còn có thể hỏi"""
    quota = estimate_remaining_quota()

    # Mỗi câu hỏi tốn trung bình:
    # - Router: 1 call (8b)
    # - Rewriter: 0.5 call (skip 50% - 8b)
    # - Generator: 1 call (70b)
    # - Critic: 1 call (8b)
    # Trung bình: 1 call 70b, 2.5 call 8b

    questions_by_70b = quota["70b"]["remaining"] // 1
    questions_by_8b = quota["8b"]["remaining"] // 2.5

    return min(questions_by_70b, questions_by_8b)


# =====================================================
# DISPLAY FUNCTIONS
# =====================================================
def print_dashboard():
    """In ra dashboard đẹp"""
    print("\n" + "=" * 70)
    print("📊 GROQ API QUOTA DASHBOARD")
    print("=" * 70)

    # Current usage
    usage = get_current_usage()
    print(f"\n📅 Hôm nay ({datetime.now().strftime('%d/%m/%Y')})")
    print(f"  • Llama 3.3 70b: {usage.get('llama-3.3-70b', 0):,} calls")
    print(f"  • Llama 3.1 8b: {usage.get('llama-3.1-8b', 0):,} calls")
    print(f"  • Total tokens: {usage.get('total_tokens', 0):,}")

    # Remaining quota
    quota = estimate_remaining_quota()
    print(f"\n💰 Quota còn lại:")

    # 70b
    bar_70b = "█" * int(quota["70b"]["percentage"] / 5) + "░" * (20 - int(quota["70b"]["percentage"] / 5))
    print(f"  • 70b: [{bar_70b}] {quota['70b']['percentage']:.1f}%")
    print(f"    Used: {quota['70b']['used']:,} / {quota['70b']['limit']:,}")
    print(f"    Remaining: {quota['70b']['remaining']:,}")

    # 8b
    bar_8b = "█" * int(quota["8b"]["percentage"] / 5) + "░" * (20 - int(quota["8b"]["percentage"] / 5))
    print(f"  • 8b:  [{bar_8b}] {quota['8b']['percentage']:.1f}%")
    print(f"    Used: {quota['8b']['used']:,} / {quota['8b']['limit']:,}")
    print(f"    Remaining: {quota['8b']['remaining']:,}")

    # Estimate
    questions_left = estimate_questions_remaining()
    print(f"\n🎯 Ước tính: Còn hỏi được ~{questions_left:,} câu hỏi")

    # Cache stats
    cache = load_cache()
    print(f"\n💾 Cache:")
    print(f"  • Số câu đã cache: {len(cache):,}")
    print(f"  • Tiết kiệm: ~{len(cache) * 4:,} API calls")

    # Warnings
    if quota["70b"]["percentage"] > 80:
        print(f"\n⚠️  CẢNH BÁO: Đã dùng {quota['70b']['percentage']:.1f}% quota 70b!")

    if quota["70b"]["percentage"] > 95:
        print(f"🚨 NGUY HIỂM: Sắp hết quota 70b! Còn {quota['70b']['remaining']} calls")

    print("=" * 70 + "\n")


def print_weekly_report():
    """In báo cáo tuần"""
    log = load_quota_log()

    print("\n" + "=" * 70)
    print("📈 BÁO CÁO 7 NGÀY GẦN NHẤT")
    print("=" * 70)

    # Get last 7 days
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    dates.reverse()

    print(f"\n{'Ngày':<12} {'70b calls':<12} {'8b calls':<12} {'Total':<12}")
    print("-" * 70)

    total_70b = 0
    total_8b = 0

    for date in dates:
        if date in log["daily_usage"]:
            usage = log["daily_usage"][date]
            calls_70b = usage.get("llama-3.3-70b", 0)
            calls_8b = usage.get("llama-3.1-8b", 0)
            total = calls_70b + calls_8b

            total_70b += calls_70b
            total_8b += calls_8b

            print(f"{date:<12} {calls_70b:<12,} {calls_8b:<12,} {total:<12,}")
        else:
            print(f"{date:<12} {0:<12} {0:<12} {0:<12}")

    print("-" * 70)
    print(f"{'TỔNG':<12} {total_70b:<12,} {total_8b:<12,} {total_70b + total_8b:<12,}")
    print(f"\n💡 Trung bình/ngày: {(total_70b + total_8b) / 7:.0f} calls")
    print("=" * 70 + "\n")


# =====================================================
# CLEANUP FUNCTION
# =====================================================
def cleanup_old_logs():
    """Xóa logs cũ hơn 30 ngày"""
    log = load_quota_log()
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Clean daily usage
    log["daily_usage"] = {
        k: v for k, v in log["daily_usage"].items()
        if k >= cutoff
    }

    # Clean hourly usage
    cutoff_hour = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    log["hourly_usage"] = {
        k: v for k, v in log["hourly_usage"].items()
        if k >= cutoff_hour
    }

    save_quota_log(log)
    print("✅ Đã dọn dẹp logs cũ")


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "week":
            print_weekly_report()
        elif cmd == "cleanup":
            cleanup_old_logs()
        else:
            print("Commands: week, cleanup")
    else:
        print_dashboard()