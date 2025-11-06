import datetime
import subprocess
import shlex

# --- Configuration for your recipes ---
# Define a list of recipe configurations.
# 'type' helps determine how to calculate the --recipe-specific-option.
# 'days' is for recipes that download articles from the last N days (like WashPost, FT).
# 'weekday' is for recipes that are only relevant on a specific day (e.g., a weekly magazine).

# a history to record what is the last time download 

RECIPE_CONFIGS = [
    # 2025-01-25 : YYYY-MM-DD
    {
        "name": "The Economist",
        "recipe": "economist.recipe",
        "output": "economists.pdf",
        "type": "date",
        "value": 5,  # Friday (0=Mon, 6=Sun). Assuming new edition comes out Friday.
        "format": "{year}-{month}-{date}"
        # Logic: If today is Saturday or Sunday, download Friday's edition.
    },
    # Oct 27, 2025 : MMM DD, YYYY 
    {
        "name": "Barron's",
        "recipe": "barrons.recipe",
        "output": "barron.pdf",
        "type": "date",
        "value": 6,  # Sunday (Assuming Sunday is the main publication date for a weekly)
        "format": "{month} {date}, {year}"
    },
    {
        "name": "Washington Post (Daily)",
        "recipe": "wash_post.recipe",
        "output": "washpost.pdf",
        "type": "days",
        "value": "0.5",  # Download articles from the last 12 hours
        "format": ""
    },
    {
        "name": "Financial Times (Daily)",
        "recipe": "financial_times.recipe",
        "output": "ftimes.pdf",
        "type": "days",
        "value": "0.5",
        "format": ""
    },
    # Note: Bloomberg Business Week and HBR use 'issue' which would require more complex
    # custom logic based on the current date, so they are omitted from the basic script for clarity.
]


def calculate_recipe_option(config):
    """Calculates the --recipe-specific-option value based on the config type."""
    today = datetime.date.today()
    
    if config["type"] == "days":
        # Simple case: always run, and the option is a fixed 'days' value.
        return f"days:'{config['value']}'", True

    elif config["type"] == "date":
        target_weekday = config["weekday"]
        current_weekday = today.weekday()  # 0=Monday, 6=Sunday

        # Calculate the date of the most recent target weekday
        # We want the date for the most recently *passed* target weekday (e.g., the last Friday).
        days_diff = (current_weekday - target_weekday) % 7
        if days_diff == 0 and current_weekday != target_weekday:
            # If today is the target day, we usually want to download today's edition,
            # but for a weekly, it's safer to check if the file already exists or just download today.
            # For simplicity, let's assume if today is the day, download today's date.
            pass
        elif days_diff == 0:
             # If today IS the target day, we likely want the date from 7 days ago,
             # as the latest edition is usually from the *previous* day's run.
             # This logic is *highly* specific to the publication's release time, so
             # for weekly publications, let's target the *last* one.
             if today.weekday() == target_weekday:
                 days_diff = 7

        # The date of the edition to download
        download_date = today - datetime.timedelta(days=days_diff)
        
        # Decide IF we should run. A common rule: only run for weekly publications once a week
        # or on specific "catch-up" days (e.g., Saturday/Sunday for a Friday pub).
        # A simple approach: Run only if the target date is in the last 7 days.
        run_download = days_diff < 7 # This needs more sophisticated logic for real-world use

        # The date format used by calibre recipes is often YYYY-MM-DD
        return f"date:'{download_date.strftime('%Y-%m-%d')}'", True # Always download in this concept

    return None, False


def run_conversion_commands():
    """Iterates through the config and executes ebook-convert commands."""
    print(f"--- Calibre Recipe Downloader Script: {datetime.date.today().strftime('%Y-%m-%d')} ---")

    for config in RECIPE_CONFIGS:
        option_value, should_run = calculate_recipe_option(config)
        
        if not should_run:
            print(f"[{config['name']}] Skipping download. Not the scheduled day.")
            continue
            
        # Construct the full command
        command = f"ebook-convert {config['recipe']} {datetime.date.today().strftime('%Y%m%d')}-{config['output']} --recipe-specific-option={option_value}"

        print(f"\n[{config['name']}] Running command:")
        print(f"  > {command}")
        
        try:
            # Use shlex.split to correctly handle spaces/quotes in the command
            # The 'shell=True' is often used for simple execution but 'shlex.split' is safer
            # result = subprocess.run(shlex.split(command), check=True, capture_output=True, text=True)
            
            # For simplicity and seeing output, we'll use a safer but less comprehensive method:
            print("  (Execution FAKE-OUT: Would run subprocess here)")
            # subprocess.run(command, shell=True, check=True) # Uncomment for real use
            
            # print(f"  Success: {result.stdout.strip()}")
            
        except subprocess.CalledProcessError as e:
            print(f"  *** ERROR during conversion for {config['name']} ***")
            # print(f"  {e.stderr.strip()}")
        except FileNotFoundError:
            print("  *** ERROR: ebook-convert command not found. Is Calibre installed and in your PATH? ***")

if __name__ == "__main__":
    # You would typically schedule this script to run daily using a system scheduler
    # like Cron (Linux/macOS) or Task Scheduler (Windows).
    run_conversion_commands()
