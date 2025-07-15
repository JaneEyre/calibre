# Calibre Scheduled Downloader

A Python script that leverages Calibre's existing recipe and scheduling infrastructure to set up regular download jobs for news, blogs, and other content.

## Features

- **Custom Recipe Creation**: Create recipes for downloading content from RSS feeds, news sites, etc.
- **Flexible Scheduling**: Support for interval-based, daily, weekly, or monthly schedules
- **Multiple Integration Options**: Works with cron, Python schedule library, or built-in daemon mode
- **Format Support**: Download to EPUB, MOBI, PDF, and other e-book formats
- **Automated Management**: Tracks download history and prevents duplicate downloads

## Requirements

- Calibre installed and available in Python path
- Python 3.6+ 
- Network access for downloading content

## Installation

1. Ensure Calibre is installed:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install calibre
   
   # macOS (using Homebrew)
   brew install calibre
   
   # Or download from https://calibre-ebook.com/download
   ```

2. Download the script:
   ```bash
   wget https://raw.githubusercontent.com/your-repo/calibre_scheduled_downloader.py
   chmod +x calibre_scheduled_downloader.py
   ```

## Quick Start

### 1. Set Up Example Recipe

```bash
# Create and schedule an example recipe
python calibre_scheduled_downloader.py --example
```

This creates an example recipe that downloads from Hacker News and Python feeds daily.

### 2. Run Downloads Once

```bash
# Check for and run any scheduled downloads
python calibre_scheduled_downloader.py --run-once
```

### 3. Start Daemon Mode

```bash
# Run continuously, checking every 5 minutes
python calibre_scheduled_downloader.py --daemon --check-interval 300
```

## Usage Examples

### Basic Operations

```bash
# List all scheduled recipes
python calibre_scheduled_downloader.py --list-scheduled

# Schedule an existing recipe file
python calibre_scheduled_downloader.py --schedule-recipe my_recipe.recipe --interval 2.0

# Unschedule a recipe
python calibre_scheduled_downloader.py --unschedule example_news_site

# Specify custom output directory
python calibre_scheduled_downloader.py --output-dir /path/to/downloads --run-once
```

### Creating Custom Recipes

Create a Python file with your custom recipe:

```python
# custom_recipe.py
from calibre.web.feeds.news import BasicNewsRecipe

class MyCustomRecipe(BasicNewsRecipe):
    title = 'My News Source'
    __author__ = 'Your Name'
    description = 'Downloads from my favorite news site'
    
    # Download settings
    language = 'en'
    oldest_article = 7  # days
    max_articles_per_feed = 20
    delay = 1  # seconds between downloads
    
    # Content settings
    no_stylesheets = True
    remove_javascript = True
    
    # RSS feeds to download
    feeds = [
        ('Tech News', 'https://example.com/tech-feed.rss'),
        ('World News', 'https://example.com/world-feed.rss'),
    ]
    
    # Custom processing (optional)
    def preprocess_html(self, soup):
        # Remove ads and unwanted content
        for tag in soup.find_all('div', class_='advertisement'):
            tag.decompose()
        return soup
```

Then schedule it:

```python
from calibre_scheduled_downloader import CalibreScheduledDownloader
from custom_recipe import MyCustomRecipe

downloader = CalibreScheduledDownloader()
downloader.schedule_recipe(MyCustomRecipe, 'interval', 1.0)  # Daily
```

### Advanced Scheduling

```python
from calibre_scheduled_downloader import CalibreScheduledDownloader

downloader = CalibreScheduledDownloader()

# Schedule for specific days of week (Monday=0, Sunday=6)
# Download every Monday at 8:00 AM
downloader.schedule_recipe(
    recipe_class, 
    'days_of_week', 
    [[0], 8, 0]  # [days], hour, minute
)

# Download every weekday at 6:00 AM
downloader.schedule_recipe(
    recipe_class,
    'days_of_week', 
    [[0,1,2,3,4], 6, 0]  # Monday-Friday
)

# Download daily at 9:30 PM
downloader.schedule_recipe(
    recipe_class,
    'day/time',
    [-1, 21, 30]  # -1 means every day
)
```

## Integration with External Schedulers

### Using Cron

Add to your crontab (`crontab -e`):

```bash
# Run every hour
0 * * * * /usr/bin/python3 /path/to/calibre_scheduled_downloader.py --run-once

# Run every day at 6 AM
0 6 * * * /usr/bin/python3 /path/to/calibre_scheduled_downloader.py --run-once

# Run every Monday at 8 AM
0 8 * * 1 /usr/bin/python3 /path/to/calibre_scheduled_downloader.py --run-once
```

### Using Python Schedule Library

```python
import schedule
import time
from calibre_scheduled_downloader import CalibreScheduledDownloader

downloader = CalibreScheduledDownloader()

# More flexible scheduling
schedule.every().day.at("06:00").do(downloader.run_scheduled_downloads)
schedule.every().hour.do(downloader.run_scheduled_downloads)  
schedule.every().monday.at("08:00").do(downloader.run_scheduled_downloads)
schedule.every(2).hours.do(downloader.run_scheduled_downloads)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Using systemd (Linux)

Create a service file `/etc/systemd/system/calibre-downloader.service`:

```ini
[Unit]
Description=Calibre Scheduled Downloader
After=network.target

[Service]
Type=simple
User=your-username
ExecStart=/usr/bin/python3 /path/to/calibre_scheduled_downloader.py --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable calibre-downloader.service
sudo systemctl start calibre-downloader.service
```

## Recipe Examples

### Tech News Recipe

```python
class TechNewsRecipe(BasicNewsRecipe):
    title = 'Daily Tech News'
    description = 'Aggregated technology news'
    
    feeds = [
        ('Hacker News', 'https://hnrss.org/frontpage'),
        ('TechCrunch', 'https://feeds.feedburner.com/TechCrunch/'),
        ('Ars Technica', 'http://feeds.arstechnica.com/arstechnica/index'),
        ('The Verge', 'https://www.theverge.com/rss/index.xml'),
    ]
    
    oldest_article = 2
    max_articles_per_feed = 15
```

### Academic Papers Recipe

```python
class ArXivRecipe(BasicNewsRecipe):
    title = 'arXiv CS Papers'
    description = 'Recent computer science papers from arXiv'
    
    feeds = [
        ('Machine Learning', 'http://export.arxiv.org/rss/cs.LG'),
        ('Computer Vision', 'http://export.arxiv.org/rss/cs.CV'),
        ('Artificial Intelligence', 'http://export.arxiv.org/rss/cs.AI'),
    ]
    
    oldest_article = 7
    max_articles_per_feed = 10
```

### Blog Aggregator Recipe

```python
class DevBlogsRecipe(BasicNewsRecipe):
    title = 'Developer Blogs'
    description = 'Programming and development blogs'
    
    feeds = [
        ('Joel on Software', 'https://www.joelonsoftware.com/feed/'),
        ('Martin Fowler', 'https://martinfowler.com/feed.atom'),
        ('Paul Graham', 'http://www.aaronsw.com/2002/feeds/pgessays.rss'),
    ]
    
    def preprocess_html(self, soup):
        # Remove navigation and sidebar elements
        for tag in soup.find_all(['nav', 'aside', 'footer']):
            tag.decompose()
        
        # Remove social sharing buttons
        for tag in soup.find_all('div', class_='social-share'):
            tag.decompose()
            
        return soup
```

## Command Line Reference

```
usage: calibre_scheduled_downloader.py [-h] [--output-dir OUTPUT_DIR] 
                                       [--run-once] [--daemon] 
                                       [--check-interval CHECK_INTERVAL]
                                       [--schedule-recipe SCHEDULE_RECIPE] 
                                       [--interval INTERVAL] [--list-scheduled] 
                                       [--unschedule UNSCHEDULE] [--example]

Options:
  -h, --help            show help message and exit
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Output directory for downloads
  --run-once            Run scheduled downloads once and exit
  --daemon              Start in daemon mode (continuous)
  --check-interval CHECK_INTERVAL
                        Daemon check interval in seconds (default: 300)
  --schedule-recipe SCHEDULE_RECIPE
                        Schedule a recipe (provide recipe file path)
  --interval INTERVAL   Download interval in days (default: 1.0)
  --list-scheduled      List all scheduled recipes
  --unschedule UNSCHEDULE
                        Unschedule a recipe (provide recipe ID)
  --example             Set up example recipe and schedule
```

## File Structure

When you run the script, it creates the following structure:

```
~/Downloads/calibre-scheduled/
├── example_news_site.recipe       # Recipe files
├── my_custom_recipe.recipe
├── example_news_site_20231201_090000.epub    # Downloaded content
├── example_news_site_20231202_090000.epub
└── my_custom_recipe_20231201_180000.epub
```

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure Calibre is properly installed and in your Python path
   ```bash
   python -c "import calibre; print('Calibre found')"
   ```

2. **Permission Errors**: Ensure the output directory is writable
   ```bash
   mkdir -p ~/Downloads/calibre-scheduled
   chmod 755 ~/Downloads/calibre-scheduled
   ```

3. **Network Issues**: Check internet connectivity and feed URLs
   ```bash
   curl -I https://feeds.ycombinator.com/news.rss
   ```

4. **Recipe Errors**: Test recipes manually first
   ```bash
   ebook-convert my_recipe.recipe output.epub
   ```

### Debug Mode

Enable verbose logging by modifying the script or use Calibre's debug options:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use Calibre's debugging
from calibre import prints
prints.override_default_level(prints.DEBUG)
```

## Advanced Configuration

### Custom Output Formats

Modify the `download_recipe` method to support different formats:

```python
# Download as PDF instead of EPUB
downloader.download_recipe('my_recipe', output_format='pdf')

# Multiple formats
for fmt in ['epub', 'mobi', 'pdf']:
    downloader.download_recipe('my_recipe', output_format=fmt)
```

### Custom Processing Pipeline

```python
class AdvancedRecipe(BasicNewsRecipe):
    title = 'Advanced Processing Example'
    
    def postprocess_book(self, oeb, opts, log):
        # Custom post-processing after conversion
        # Add metadata, modify structure, etc.
        pass
    
    def preprocess_raw_html(self, raw_html, url):
        # Process HTML before parsing
        # Fix encoding issues, clean malformed HTML, etc.
        return raw_html
```

## Contributing

Feel free to submit issues, feature requests, or pull requests. When contributing:

1. Test with multiple recipe types
2. Ensure backward compatibility
3. Add appropriate error handling
4. Update documentation

## License

This script builds upon Calibre's GPL v3 licensed codebase and is therefore also GPL v3.

## See Also

- [Calibre User Manual](https://manual.calibre-ebook.com/)
- [Creating Custom Recipes](https://manual.calibre-ebook.com/news.html)
- [Calibre Command Line Tools](https://manual.calibre-ebook.com/generated/en/cli-index.html)