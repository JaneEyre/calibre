#!/usr/bin/env python3
"""
Calibre Scheduled Downloader
============================

This script demonstrates how to set up regular download jobs using Calibre's 
existing recipe and scheduling infrastructure. It shows how to:

1. Create custom recipes for downloading content
2. Schedule recipes for automatic downloads  
3. Execute scheduled downloads programmatically
4. Integrate with external schedulers (cron, Python schedule, etc.)

Requirements:
- Calibre installed and available in Python path
- Network access for downloading content

Usage Examples:
    # Run scheduled downloads once
    python calibre_scheduled_downloader.py --run-once
    
    # Start daemon mode (runs continuously)
    python calibre_scheduled_downloader.py --daemon
    
    # Schedule a new recipe
    python calibre_scheduled_downloader.py --schedule-recipe my_recipe --interval 1.0
"""

import argparse
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Import Calibre components
try:
    from calibre.web.feeds.news import BasicNewsRecipe
    from calibre.web.feeds.recipes.collection import SchedulerConfig
    from calibre.web.feeds.recipes.model import RecipeModel
    from calibre.ebooks.conversion.config import load_defaults
    from calibre.ebooks.conversion.plugins.recipe_input import RecipeInput
    from calibre.utils.config import config_dir
    from calibre.utils.date import utcnow
    from calibre.ptempfile import PersistentTemporaryDirectory
    from calibre import prints
except ImportError as e:
    print(f"Error importing Calibre: {e}")
    print("Please ensure Calibre is installed and available in your Python path")
    sys.exit(1)


# Example Custom Recipe
class ExampleNewsRecipe(BasicNewsRecipe):
    """
    Example recipe for downloading content regularly.
    Customize this for your specific needs.
    """
    title = 'Example News Site'
    __author__ = 'Your Name'
    description = 'Download example news content'
    publisher = 'Example Publisher'
    
    # Download settings
    language = 'en'
    encoding = 'utf-8'
    
    # Timing settings
    oldest_article = 7  # days
    max_articles_per_feed = 25
    delay = 1  # seconds between downloads
    
    # Content settings
    no_stylesheets = True
    remove_javascript = True
    
    # Feed URLs to download from
    feeds = [
        ('Tech News', 'https://feeds.ycombinator.com/news.rss'),
        ('Python News', 'https://realpython.com/atom.xml'),
    ]
    
    def preprocess_html(self, soup):
        """Custom preprocessing of downloaded HTML"""
        # Remove unwanted elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        return soup


class CalibreScheduledDownloader:
    """
    Main class for managing scheduled Calibre downloads
    """
    
    def __init__(self, output_dir=None):
        """
        Initialize the scheduled downloader.
        
        Args:
            output_dir (str): Directory to save downloaded files. 
                            Defaults to ~/Downloads/calibre-scheduled/
        """
        self.output_dir = Path(output_dir or Path.home() / "Downloads" / "calibre-scheduled")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Calibre components
        self.scheduler_config = SchedulerConfig()
        self.recipe_input = RecipeInput(None)
        
        # Keep track of running state
        self.running = False
        self.daemon_thread = None
        
        print(f"Calibre Scheduled Downloader initialized")
        print(f"Output directory: {self.output_dir}")
    
    def create_recipe_file(self, recipe_class, filename=None):
        """
        Create a recipe file from a recipe class.
        
        Args:
            recipe_class: The recipe class to create file for
            filename: Optional filename, defaults to recipe title
            
        Returns:
            Path to created recipe file
        """
        if filename is None:
            filename = f"{recipe_class.title.replace(' ', '_').lower()}.recipe"
        
        recipe_file = self.output_dir / filename
        
        # Generate recipe file content
        recipe_content = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

from calibre.web.feeds.news import BasicNewsRecipe

class {recipe_class.__name__}(BasicNewsRecipe):
    title = '{recipe_class.title}'
    __author__ = '{recipe_class.__author__}'
    description = '{recipe_class.description}'
    publisher = '{recipe_class.publisher}'
    language = '{recipe_class.language}'
    encoding = '{recipe_class.encoding}'
    
    oldest_article = {recipe_class.oldest_article}
    max_articles_per_feed = {recipe_class.max_articles_per_feed}
    delay = {recipe_class.delay}
    
    no_stylesheets = {recipe_class.no_stylesheets}
    remove_javascript = {recipe_class.remove_javascript}
    
    feeds = {recipe_class.feeds!r}
'''
        
        with open(recipe_file, 'w', encoding='utf-8') as f:
            f.write(recipe_content)
        
        print(f"Created recipe file: {recipe_file}")
        return recipe_file
    
    def schedule_recipe(self, recipe_or_file, schedule_type='interval', schedule=1.0):
        """
        Schedule a recipe for regular downloads.
        
        Args:
            recipe_or_file: Recipe class, recipe file path, or recipe ID
            schedule_type: 'interval' (days), 'day/time', 'days_of_week'
            schedule: Schedule parameters based on type:
                     - interval: float (days between downloads)  
                     - day/time: [day_of_week, hour, minute] (-1 for daily)
                     - days_of_week: [[days], hour, minute]
        """
        
        # Handle different input types
        if isinstance(recipe_or_file, type) and issubclass(recipe_or_file, BasicNewsRecipe):
            # Recipe class - create file first
            recipe_file = self.create_recipe_file(recipe_or_file)
            recipe_id = recipe_or_file.title.replace(' ', '_').lower()
            recipe_title = recipe_or_file.title
        elif isinstance(recipe_or_file, (str, Path)):
            # File path
            recipe_file = Path(recipe_or_file)
            if not recipe_file.exists():
                raise FileNotFoundError(f"Recipe file not found: {recipe_file}")
            recipe_id = recipe_file.stem
            recipe_title = recipe_id.replace('_', ' ').title()
        else:
            raise ValueError("recipe_or_file must be a recipe class or file path")
        
        # Create recipe info dict
        recipe_info = {
            'id': recipe_id,
            'title': recipe_title,
            'file_path': str(recipe_file)
        }
        
        # Schedule the recipe
        self.scheduler_config.schedule_recipe(
            recipe_info, 
            schedule_type, 
            schedule
        )
        
        print(f"Scheduled recipe '{recipe_title}' with {schedule_type}: {schedule}")
        return recipe_id
    
    def get_scheduled_recipes(self):
        """Get list of all scheduled recipes"""
        recipes = []
        for recipe_xml in self.scheduler_config.iter_recipes():
            recipe_info = {
                'id': recipe_xml.get('id'),
                'title': recipe_xml.get('title'),
                'last_downloaded': recipe_xml.get('last_downloaded'),
            }
            recipes.append(recipe_info)
        return recipes
    
    def get_due_recipes(self):
        """Get recipes that are due for download"""
        due_recipes = []
        for recipe_xml in self.scheduler_config.iter_recipes():
            if self.scheduler_config.recipe_needs_to_be_downloaded(recipe_xml):
                due_recipes.append({
                    'id': recipe_xml.get('id'),
                    'title': recipe_xml.get('title'),
                    'xml': recipe_xml
                })
        return due_recipes
    
    def download_recipe(self, recipe_id, output_format='epub'):
        """
        Download a specific recipe.
        
        Args:
            recipe_id: ID of the recipe to download
            output_format: Output format (epub, mobi, pdf, etc.)
        """
        try:
            # Find recipe file
            recipe_file = self.output_dir / f"{recipe_id}.recipe"
            if not recipe_file.exists():
                print(f"Recipe file not found: {recipe_file}")
                return False
            
            # Create output filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"{recipe_id}_{timestamp}.{output_format}"
            
            print(f"Downloading recipe '{recipe_id}' to {output_file}")
            
            # Load recipe and run conversion
            with open(recipe_file, 'r', encoding='utf-8') as f:
                recipe_source = f.read()
            
            # Create a temporary directory for the conversion
            with PersistentTemporaryDirectory() as temp_dir:
                temp_recipe = Path(temp_dir) / f"{recipe_id}.recipe"
                with open(temp_recipe, 'w', encoding='utf-8') as f:
                    f.write(recipe_source)
                
                # Run the recipe conversion
                # This is a simplified version - in practice you'd want to use
                # Calibre's full conversion pipeline
                from calibre.ebooks.conversion.plumber import Plumber
                from calibre.customize.conversion import OptionRecommendation
                
                # Set up conversion options
                opts = load_defaults('recipe_input')
                opts.input_profile = 'default'
                opts.output_profile = 'default'
                
                # Create plumber and run conversion
                plumber = Plumber(str(temp_recipe), str(output_file), opts)
                plumber.run()
            
            # Update last downloaded time
            self.scheduler_config.update_last_downloaded(recipe_id)
            
            print(f"Successfully downloaded: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error downloading recipe '{recipe_id}': {e}")
            return False
    
    def run_scheduled_downloads(self):
        """Run all scheduled downloads that are due"""
        due_recipes = self.get_due_recipes()
        
        if not due_recipes:
            print("No recipes due for download")
            return
        
        print(f"Found {len(due_recipes)} recipes due for download")
        
        success_count = 0
        for recipe in due_recipes:
            print(f"\nProcessing: {recipe['title']}")
            if self.download_recipe(recipe['id']):
                success_count += 1
        
        print(f"\nCompleted downloads: {success_count}/{len(due_recipes)} successful")
    
    def start_daemon(self, check_interval=300):
        """
        Start daemon mode - continuously check and run scheduled downloads.
        
        Args:
            check_interval: Seconds between checks (default: 5 minutes)
        """
        def daemon_loop():
            print(f"Starting daemon mode, checking every {check_interval} seconds")
            while self.running:
                try:
                    print(f"\n[{datetime.now()}] Checking for scheduled downloads...")
                    self.run_scheduled_downloads()
                except Exception as e:
                    print(f"Error in daemon loop: {e}")
                
                # Wait for next check
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
            
            print("Daemon stopped")
        
        self.running = True
        self.daemon_thread = threading.Thread(target=daemon_loop, daemon=True)
        self.daemon_thread.start()
    
    def stop_daemon(self):
        """Stop daemon mode"""
        self.running = False
        if self.daemon_thread:
            self.daemon_thread.join(timeout=5)
    
    def unschedule_recipe(self, recipe_id):
        """Remove a recipe from the schedule"""
        self.scheduler_config.un_schedule_recipe(recipe_id)
        print(f"Unscheduled recipe: {recipe_id}")
    
    def list_scheduled_recipes(self):
        """Print list of all scheduled recipes"""
        recipes = self.get_scheduled_recipes()
        
        if not recipes:
            print("No recipes are currently scheduled")
            return
        
        print(f"\nScheduled Recipes ({len(recipes)}):")
        print("-" * 60)
        for recipe in recipes:
            print(f"ID: {recipe['id']}")
            print(f"Title: {recipe['title']}")
            print(f"Last Downloaded: {recipe['last_downloaded']}")
            print("-" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Calibre Scheduled Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--output-dir', '-o', 
                       help='Output directory for downloads')
    parser.add_argument('--run-once', action='store_true',
                       help='Run scheduled downloads once and exit')
    parser.add_argument('--daemon', action='store_true',
                       help='Start in daemon mode (continuous)')
    parser.add_argument('--check-interval', type=int, default=300,
                       help='Daemon check interval in seconds (default: 300)')
    parser.add_argument('--schedule-recipe', 
                       help='Schedule a recipe (provide recipe file path)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Download interval in days (default: 1.0)')
    parser.add_argument('--list-scheduled', action='store_true',
                       help='List all scheduled recipes')
    parser.add_argument('--unschedule', 
                       help='Unschedule a recipe (provide recipe ID)')
    parser.add_argument('--example', action='store_true',
                       help='Set up example recipe and schedule')
    
    args = parser.parse_args()
    
    # Create downloader instance
    downloader = CalibreScheduledDownloader(args.output_dir)
    
    try:
        if args.example:
            # Set up example recipe
            print("Setting up example recipe...")
            recipe_id = downloader.schedule_recipe(ExampleNewsRecipe, 'interval', 1.0)
            print(f"Example recipe '{recipe_id}' scheduled to run daily")
            
        elif args.schedule_recipe:
            # Schedule a recipe
            downloader.schedule_recipe(args.schedule_recipe, 'interval', args.interval)
            
        elif args.unschedule:
            # Unschedule a recipe
            downloader.unschedule_recipe(args.unschedule)
            
        elif args.list_scheduled:
            # List scheduled recipes
            downloader.list_scheduled_recipes()
            
        elif args.run_once:
            # Run downloads once
            downloader.run_scheduled_downloads()
            
        elif args.daemon:
            # Start daemon mode
            downloader.start_daemon(args.check_interval)
            try:
                print("Daemon running. Press Ctrl+C to stop...")
                while downloader.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping daemon...")
                downloader.stop_daemon()
                
        else:
            # Default: show help
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# Example usage with external schedulers
def example_cron_integration():
    """
    Example of how to integrate with cron for scheduling.
    
    Add this to your crontab:
    # Run every hour
    0 * * * * /usr/bin/python3 /path/to/calibre_scheduled_downloader.py --run-once
    
    # Run every day at 6 AM
    0 6 * * * /usr/bin/python3 /path/to/calibre_scheduled_downloader.py --run-once
    """
    pass


def example_python_schedule():
    """
    Example using Python's schedule library for more flexible scheduling.
    
    pip install schedule
    """
    try:
        import schedule
        
        downloader = CalibreScheduledDownloader()
        
        # Schedule different recipes at different times
        schedule.every().day.at("06:00").do(downloader.run_scheduled_downloads)
        schedule.every().hour.do(downloader.run_scheduled_downloads)
        schedule.every().monday.at("08:00").do(downloader.run_scheduled_downloads)
        
        print("Python schedule running...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except ImportError:
        print("Install 'schedule' package: pip install schedule")


if __name__ == '__main__':
    main()